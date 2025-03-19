from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Task, Category, TaskShare
from .serializers import (
    TaskSerializer, 
    UserSerializer, 
    UserRegistrationSerializer, 
    ChangePasswordSerializer,
    CategorySerializer,
    TaskShareSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return self.serializer_class

    @action(detail=False, methods=['get'])
    def me(self):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def change_password(self):
        user = self.request.user
        serializer = ChangePasswordSerializer(data=self.request.data)
        
        if serializer.is_valid():
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {'old_password': 'Wrong password.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.data.get('new_password'))
            user.save()
            return Response({'status': 'password changed'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['completed', 'due_date', 'category', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            models.Q(user=user) | 
            models.Q(shares__shared_with=user)
        ).distinct()

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        task = self.get_object()
        if task.user != self.request.user and not task.shares.filter(
            shared_with=self.request.user,
            permission__in=['EDIT', 'DELETE']
        ).exists():
            raise permissions.PermissionDenied("You don't have permission to edit this task")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user and not instance.shares.filter(
            shared_with=self.request.user,
            permission='DELETE'
        ).exists():
            raise permissions.PermissionDenied("You don't have permission to delete this task")
        instance.delete()

    @action(detail=False, methods=['get'])
    def completed_tasks(self):
        tasks = self.get_queryset().filter(completed=True)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_tasks(self):
        tasks = self.get_queryset().filter(completed=False)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tasks_by_category(self, request):
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {"error": "category_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def tasks_by_priority(self, request):
        priority = request.query_params.get('priority')
        if not priority:
            return Response(
                {"error": "priority parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if priority not in dict(Task.PRIORITY_CHOICES):
            return Response(
                {"error": "Invalid priority value"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = self.get_queryset().filter(priority=priority)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        task = self.get_object()
        if task.user != request.user:
            raise permissions.PermissionDenied("You can only share tasks that you own")

        serializer = TaskShareSerializer(data={
            'task': task.id,
            'shared_with': request.data.get('user_id'),
            'permission': request.data.get('permission', 'VIEW')
        }, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def unshare(self, request, pk=None):
        task = self.get_object()
        if task.user != request.user:
            raise permissions.PermissionDenied("You can only unshare tasks that you own")

        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {"error": "user_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            share = TaskShare.objects.get(task=task, shared_with_id=user_id)
            share.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except TaskShare.DoesNotExist:
            return Response(
                {"error": "Task is not shared with this user"}, 
                status=status.HTTP_404_NOT_FOUND
            )
