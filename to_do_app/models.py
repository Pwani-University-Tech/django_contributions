from django.db import models
from django.contrib.auth import get_user_model

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#FF0000")  # Hex color code
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='tags')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['name', 'user']  # Each user can have unique tag names
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def task_count(self):
        """Return the number of tasks using this tag"""
        return self.tasks.count()

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
    tags = models.ManyToManyField(Tag, related_name='tasks', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def tag_list(self):
        """Return a list of tag names for this task"""
        return list(self.tags.values_list('name', flat=True))

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

class NotificationPreference(models.Model):
    NOTIFICATION_TIMING_CHOICES = [
        ('1H', '1 hour before'),
        ('3H', '3 hours before'),
        ('6H', '6 hours before'),
        ('12H', '12 hours before'),
        ('24H', '24 hours before'),
        ('48H', '48 hours before'),
        ('1W', '1 week before'),
    ]

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='notification_preference')
    email_notifications = models.BooleanField(default=True)
    notification_timing = models.CharField(max_length=3, choices=NOTIFICATION_TIMING_CHOICES, default='24H')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s notification preferences"

class TaskNotification(models.Model):
    NOTIFICATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notifications')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='task_notifications')
    scheduled_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=NOTIFICATION_STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-scheduled_time']
        unique_together = ['task', 'user', 'scheduled_time']

    def __str__(self):
        return f"Notification for {self.task.title} to {self.user.username}"