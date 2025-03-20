from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Task, TaskNotification, Category, Tag
from ..views import (
    TaskViewSet,
    CategoryViewSet,
    TagViewSet,
    NotificationPreferenceViewSet,
    send_task_notifications
)

class URLPatternTestCase(TestCase):
    def test_task_urls(self):
        """Test task URL patterns"""
        # Test task list URL
        url = reverse('task-list')
        self.assertEqual(url, '/api/tasks/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, TaskViewSet.__name__)
        
        # Test task detail URL
        url = reverse('task-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/tasks/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, TaskViewSet.__name__)
        
        # Test task share URL
        url = reverse('task-share', kwargs={'pk': 1})
        self.assertEqual(url, '/api/tasks/1/share/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, TaskViewSet.__name__)

    def test_category_urls(self):
        """Test category URL patterns"""
        # Test category list URL
        url = reverse('category-list')
        self.assertEqual(url, '/api/categories/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, CategoryViewSet.__name__)
        
        # Test category detail URL
        url = reverse('category-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/categories/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, CategoryViewSet.__name__)

    def test_tag_urls(self):
        """Test tag URL patterns"""
        # Test tag list URL
        url = reverse('tag-list')
        self.assertEqual(url, '/api/tags/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, TagViewSet.__name__)
        
        # Test tag detail URL
        url = reverse('tag-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/tags/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, TagViewSet.__name__)

    def test_notification_preference_urls(self):
        """Test notification preference URL patterns"""
        # Test notification preference list URL
        url = reverse('notification-preference-list')
        self.assertEqual(url, '/api/notification-preferences/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, NotificationPreferenceViewSet.__name__)
        
        # Test notification preference detail URL
        url = reverse('notification-preference-detail', kwargs={'pk': 1})
        self.assertEqual(url, '/api/notification-preferences/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.__name__, NotificationPreferenceViewSet.__name__)


class BackgroundTaskTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create tasks with different due dates
        self.due_soon_task = Task.objects.create(
            title='Due Soon Task',
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(hours=1)
        )
        
        self.due_later_task = Task.objects.create(
            title='Due Later Task',
            user=self.user,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        self.overdue_task = Task.objects.create(
            title='Overdue Task',
            user=self.user,
            due_date=timezone.now() - timezone.timedelta(hours=1)
        )

    def test_send_task_notifications(self):
        """Test notification sending functionality"""
        # Create notifications for tasks
        soon_notification = TaskNotification.objects.create(
            task=self.due_soon_task,
            user=self.user,
            scheduled_time=timezone.now(),
            status='PENDING'
        )
        
        later_notification = TaskNotification.objects.create(
            task=self.due_later_task,
            user=self.user,
            scheduled_time=timezone.now() + timezone.timedelta(days=6),
            status='PENDING'
        )
        
        overdue_notification = TaskNotification.objects.create(
            task=self.overdue_task,
            user=self.user,
            scheduled_time=timezone.now() - timezone.timedelta(hours=2),
            status='PENDING'
        )
        
        # Run the notification sender
        send_task_notifications()
        
        # Verify notifications were processed correctly
        soon_notification.refresh_from_db()
        self.assertEqual(soon_notification.status, 'SENT')
        
        later_notification.refresh_from_db()
        self.assertEqual(later_notification.status, 'PENDING')
        
        overdue_notification.refresh_from_db()
        self.assertEqual(overdue_notification.status, 'SENT')

    def test_notification_error_handling(self):
        """Test notification error handling"""
        # Create a notification with invalid email
        self.user.email = ''  # Empty email should cause sending to fail
        self.user.save()
        
        notification = TaskNotification.objects.create(
            task=self.due_soon_task,
            user=self.user,
            scheduled_time=timezone.now(),
            status='PENDING'
        )
        
        # Run the notification sender
        send_task_notifications()
        
        # Verify notification was marked as failed
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'FAILED')
        self.assertIsNotNone(notification.error_message)

    def test_notification_deduplication(self):
        """Test notification deduplication"""
        # Create multiple notifications for the same task with different scheduled times
        notifications = []
        base_time = timezone.now() - timezone.timedelta(minutes=1)
        
        for i in range(3):
            notification = TaskNotification.objects.create(
                task=self.due_soon_task,
                user=self.user,
                scheduled_time=base_time + timezone.timedelta(minutes=i),
                status='PENDING'
            )
            notifications.append(notification)
        
        # Run the notification sender with email backend for testing
        from django.core import mail
        with self.settings(
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
            DEFAULT_FROM_EMAIL='test@example.com'
        ):
            send_task_notifications()
            
            # Verify email was sent
            self.assertEqual(len(mail.outbox), 1)
            
            # Verify only one notification was sent and others were marked as duplicates
            sent_count = TaskNotification.objects.filter(
                task=self.due_soon_task,
                status='SENT'
            ).count()
            self.assertEqual(sent_count, 1)
            
            duplicate_count = TaskNotification.objects.filter(
                task=self.due_soon_task,
                status='DUPLICATE'
            ).count()
            self.assertEqual(duplicate_count, 2)
            
            # Verify email content
            email = mail.outbox[0]
            self.assertEqual(email.subject, f'Task Due Soon: {self.due_soon_task.title}')
            self.assertIn(self.due_soon_task.title, email.body) 