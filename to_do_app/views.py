from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing tasks.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['completed', 'due_date']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'due_date']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        This view should return a list of all tasks
        for the currently authenticated user.
        """
        return Task.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def completed_tasks(self):
        """
        Return all completed tasks for the current user.
        """
        tasks = self.get_queryset().filter(completed=True)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_tasks(self):
        """
        Return all pending tasks for the current user.
        """
        tasks = self.get_queryset().filter(completed=False)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
