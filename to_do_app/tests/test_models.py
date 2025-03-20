from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Task, Category, Tag, TaskShare, NotificationPreference

class ModelTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test Description',
            user=self.user
        )
        
        # Create a tag
        self.tag = Tag.objects.create(
            name='Test Tag',
            color='#FF0000',
            user=self.user
        )
        
        # Create a task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            user=self.user,
            category=self.category,
            priority='HIGH'
        )
        self.task.tags.add(self.tag)

    def test_category_str(self):
        """Test the string representation of Category"""
        self.assertEqual(str(self.category), 'Test Category')

    def test_tag_str(self):
        """Test the string representation of Tag"""
        self.assertEqual(str(self.tag), 'Test Tag (testuser)')

    def test_task_str(self):
        """Test the string representation of Task"""
        self.assertEqual(str(self.task), 'Test Task')

    def test_task_tag_list(self):
        """Test the tag_list method of Task"""
        self.assertEqual(self.task.tag_list(), ['Test Tag'])

    def test_tag_task_count(self):
        """Test the task_count method of Tag"""
        self.assertEqual(self.tag.task_count(), 1)

    def test_category_unique_constraint(self):
        """Test that a user cannot have two categories with the same name"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name='Test Category',  # Same name as existing category
                description='Another Description',
                user=self.user
            )

    def test_tag_unique_constraint(self):
        """Test that a user cannot have two tags with the same name"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Tag.objects.create(
                name='Test Tag',  # Same name as existing tag
                color='#00FF00',
                user=self.user
            )

    def test_task_share(self):
        """Test task sharing functionality"""
        other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        share = TaskShare.objects.create(
            task=self.task,
            shared_with=other_user,
            permission='VIEW'
        )
        
        self.assertEqual(str(share), 'Test Task shared with otheruser')
        self.assertTrue(self.task.shared_with.filter(id=other_user.id).exists())

    def test_notification_preference(self):
        """Test notification preferences"""
        pref = NotificationPreference.objects.create(
            user=self.user,
            email_notifications=True,
            notification_timing='24H'
        )
        
        self.assertEqual(str(pref), "testuser's notification preferences")
        self.assertTrue(pref.email_notifications)
        self.assertEqual(pref.notification_timing, '24H') 