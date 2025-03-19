from django.db import models
from django.contrib.auth import get_user_model

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='categories')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "categories"
        unique_together = ['name', 'user']  # Each user can have only one category with a specific name

    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    shared_with = models.ManyToManyField(get_user_model(), through='TaskShare', related_name='shared_tasks')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class TaskShare(models.Model):
    PERMISSION_CHOICES = [
        ('VIEW', 'View Only'),
        ('EDIT', 'Can Edit'),
        ('DELETE', 'Can Delete'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='shares')
    shared_with = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='task_shares')
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='VIEW')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['task', 'shared_with']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.task.title} shared with {self.shared_with.username}"