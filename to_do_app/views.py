from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Q
from django.db import models
from .models import Task, Category, TaskShare, NotificationPreference, TaskNotification, Tag
from .serializers import (
    TaskSerializer, 
    UserSerializer, 
    UserRegistrationSerializer, 
    ChangePasswordSerializer,
    CategorySerializer,
    TaskShareSerializer,
    NotificationPreferenceSerializer,
    TaskNotificationSerializer,
    TagSerializer
)
from rest_framework import serializers

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

class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def get_object(self):
        # Get or create preferences for the current user
        pref, created = NotificationPreference.objects.get_or_create(user=self.request.user)
        return pref

class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def get_queryset(self):
        return Tag.objects.filter(user=self.request.user).annotate(
            task_count=Count('tasks')
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most used tags"""
        tags = self.get_queryset().order_by('-task_count')[:10]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a specific tag"""
        tag = self.get_object()
        tasks = tag.tasks.filter(user=request.user)
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['completed', 'due_date', 'category', 'priority', 'tags']
    search_fields = ['title', 'description', 'tags__name']
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
            raise PermissionDenied("You don't have permission to edit this task")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user and not instance.shares.filter(
            shared_with=self.request.user,
            permission='DELETE'
        ).exists():
            raise PermissionDenied("You don't have permission to delete this task")
        instance.delete()

    def filter_queryset(self, queryset):
        """Override to handle invalid filter values"""
        # Handle priority filter
        priority = self.request.query_params.get('priority')
        if priority and priority not in dict(Task.PRIORITY_CHOICES):
            raise serializers.ValidationError({
                'priority': f"Invalid priority value. Must be one of: {', '.join(dict(Task.PRIORITY_CHOICES).keys())}"
            })

        # Handle completion status filter
        completed = self.request.query_params.get('completed')
        if completed and completed.lower() not in ['true', 'false']:
            raise serializers.ValidationError({
                'completed': "Invalid completed value. Must be 'true' or 'false'"
            })

        # Handle date range filters
        due_date_before = self.request.query_params.get('due_date_before')
        due_date_after = self.request.query_params.get('due_date_after')
        
        try:
            if due_date_before:
                timezone.datetime.strptime(due_date_before, '%Y-%m-%d')
            if due_date_after:
                timezone.datetime.strptime(due_date_after, '%Y-%m-%d')
        except ValueError:
            raise serializers.ValidationError({
                'due_date': "Invalid date format. Use YYYY-MM-DD"
            })

        # Apply all filters
        try:
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(self.request, queryset, self)
            return queryset
        except Exception as e:
            raise serializers.ValidationError({
                'filter': f"Filter error: {str(e)}"
            })

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

    @action(detail=False, methods=['get'])
    def by_tag(self, request):
        """Get tasks filtered by multiple tags"""
        tag_ids = request.query_params.getlist('tag_ids[]')
        tag_names = request.query_params.getlist('tag_names[]')
        
        queryset = self.get_queryset()
        
        if tag_ids:
            queryset = queryset.filter(tags__id__in=tag_ids)
        
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names)
        
        # If both tag_ids and tag_names are provided, return tasks that have ANY of the specified tags
        # To require ALL tags, add .distinct() and check that the count matches the number of tags
        if request.query_params.get('require_all', '').lower() == 'true':
            if tag_ids and tag_names:
                total_tags = len(tag_ids) + len(tag_names)
                queryset = queryset.annotate(
                    matching_tags=Count('tags', distinct=True)
                ).filter(matching_tags=total_tags)
            elif tag_ids:
                queryset = queryset.annotate(
                    matching_tags=Count('tags', distinct=True)
                ).filter(matching_tags=len(tag_ids))
            elif tag_names:
                queryset = queryset.annotate(
                    matching_tags=Count('tags', distinct=True)
                ).filter(matching_tags=len(tag_names))
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_tags(self, request, pk=None):
        """Add tags to a task without removing existing ones"""
        task = self.get_object()
        
        if task.user != request.user:
            return Response(
                {"error": "You can only add tags to your own tasks"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        tag_ids = request.data.get('tag_ids', [])
        tag_names = request.data.get('tag_names', [])
        
        # Validate tag_ids
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, user=request.user)
            if len(tags) != len(tag_ids):
                return Response(
                    {"error": "One or more tags do not exist or do not belong to you"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            task.tags.add(*tags)
        
        # Handle tag_names
        if tag_names:
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=name,
                    user=request.user,
                    defaults={'color': '#FF0000'}
                )
                task.tags.add(tag)
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def remove_tags(self, request, pk=None):
        """Remove specific tags from a task"""
        task = self.get_object()
        
        if task.user != request.user:
            return Response(
                {"error": "You can only remove tags from your own tasks"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        tag_ids = request.data.get('tag_ids', [])
        tag_names = request.data.get('tag_names', [])
        
        if tag_ids:
            task.tags.remove(*tag_ids)
        
        if tag_names:
            task.tags.remove(*Tag.objects.filter(name__in=tag_names, user=request.user))
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share a task with another user"""
        task = self.get_object()
        
        # Validate ownership
        if task.user != request.user:
            raise PermissionDenied("You can only share tasks that you own")

        # Validate username
        username = request.data.get('username')
        if not username:
            return Response(
                {"error": "Username is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate permission
        permission = request.data.get('permission', 'VIEW')
        if permission not in dict(TaskShare.PERMISSION_CHOICES):
            return Response(
                {"error": f"Invalid permission. Choices are: {', '.join(dict(TaskShare.PERMISSION_CHOICES).keys())}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user to share with
        try:
            shared_with = get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            return Response(
                {"error": f"User '{username}' not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent self-sharing
        if shared_with == request.user:
            return Response(
                {"error": "You cannot share a task with yourself"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for existing share
        existing_share = TaskShare.objects.filter(
            task=task, 
            shared_with=shared_with
        ).first()

        if existing_share:
            if existing_share.permission == permission:
                return Response(
                    {"error": f"Task is already shared with user '{username}' with {permission} permission"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            # Update existing share with new permission
            existing_share.permission = permission
            existing_share.save()
            serializer = TaskShareSerializer(existing_share)
            return Response(serializer.data)

        # Create new share
        share = TaskShare.objects.create(
            task=task,
            shared_with=shared_with,
            permission=permission
        )

        serializer = TaskShareSerializer(share)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def upcoming_notifications(self, request):
        """Get all pending notifications for the current user"""
        notifications = TaskNotification.objects.filter(
            user=request.user,
            status='PENDING',
            scheduled_time__gte=timezone.now()
        ).select_related('task')
        
        serializer = TaskNotificationSerializer(notifications, many=True)
        return Response(serializer.data)

def send_task_notifications():
    """Send notifications for tasks that are due soon"""
    now = timezone.now()
    
    # Get all pending notifications that are due to be sent
    pending_notifications = TaskNotification.objects.filter(
        status='PENDING',
        scheduled_time__lte=now
    ).select_related('task', 'user').order_by('scheduled_time')
    
    # Group notifications by task to handle deduplication
    task_notifications = {}
    for notification in pending_notifications:
        if notification.task_id not in task_notifications:
            task_notifications[notification.task_id] = []
        task_notifications[notification.task_id].append(notification)
    
    # Process notifications for each task
    for task_id, notifications in task_notifications.items():
        # Keep only the earliest notification for each task
        primary_notification = notifications[0]
        duplicate_notifications = notifications[1:]
        
        try:
            # Attempt to send the notification
            if not primary_notification.user.email:
                raise ValueError("User has no email address")
            
            task = primary_notification.task
            subject = f'Task Due Soon: {task.title}'
            message = (
                f'Your task "{task.title}" is due {task.due_date.strftime("%Y-%m-%d %H:%M")}.\n\n'
                f'Description: {task.description or "No description"}\n'
                f'Priority: {task.priority}\n'
                f'Status: {"Completed" if task.completed else "Pending"}'
            )
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [primary_notification.user.email],
                fail_silently=False,
            )
            
            # Mark the notification as sent
            primary_notification.status = 'SENT'
            primary_notification.sent_at = timezone.now()
            primary_notification.save()
            
            # Mark other notifications as duplicates
            if duplicate_notifications:
                # First, mark all notifications as duplicates
                TaskNotification.objects.filter(
                    id__in=[n.id for n in duplicate_notifications]
                ).update(
                    status='DUPLICATE',
                    error_message='Duplicate notification - another notification was sent for this task'
                )
                
                # Then, mark any notifications with the same scheduled time as the primary as duplicates
                TaskNotification.objects.filter(
                    task=task,
                    user=primary_notification.user,
                    scheduled_time=primary_notification.scheduled_time,
                    status='PENDING'
                ).exclude(
                    id=primary_notification.id
                ).update(
                    status='DUPLICATE',
                    error_message='Duplicate notification - another notification was sent for this task'
                )
                
        except Exception as e:
            # Handle any errors that occur during sending
            error_message = str(e)
            primary_notification.status = 'FAILED'
            primary_notification.error_message = error_message
            primary_notification.save()
            
            # Mark duplicates as failed as well
            if duplicate_notifications:
                TaskNotification.objects.filter(
                    id__in=[n.id for n in duplicate_notifications]
                ).update(
                    status='FAILED',
                    error_message=error_message
                )
