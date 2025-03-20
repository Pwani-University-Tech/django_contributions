from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import Task, Category, Tag, TaskShare, NotificationPreference
import json

class ViewEdgeCaseTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create users
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = get_user_model().objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)
        
        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        self.tag = Tag.objects.create(
            name='Test Tag',
            color='#FF0000',
            user=self.user
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            user=self.user,
            category=self.category,
            priority='HIGH',
            due_date=timezone.now() + timezone.timedelta(days=1)
        )
        self.task.tags.add(self.tag)

    def test_task_creation_invalid_data(self):
        """Test task creation with invalid data"""
        url = reverse('task-list')
        
        # Test empty title
        data = {
            'title': '',
            'description': 'Test description',
            'priority': 'HIGH'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('title', response.data)
        
        # Test invalid priority
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'priority': 'INVALID'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('priority', response.data)
        
        # Test invalid due date format
        data = {
            'title': 'Test Task',
            'description': 'Test description',
            'priority': 'HIGH',
            'due_date': 'invalid-date'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)

    def test_task_filtering_edge_cases(self):
        """Test task filtering with invalid parameters"""
        url = reverse('task-list')
        
        # Test invalid priority filter
        response = self.client.get(f"{url}?priority=INVALID")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('priority', response.data)
        
        # Test invalid completion status filter
        response = self.client.get(f"{url}?completed=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('completed', response.data)
        
        # Test invalid date range
        response = self.client.get(f"{url}?due_date_before=invalid-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)

    def test_task_sharing_edge_cases(self):
        """Test task sharing edge cases"""
        # Create a task to share
        task = Task.objects.create(
            title='Test Task',
            user=self.user
        )
        url = reverse('task-share', kwargs={'pk': task.pk})
        
        # Test sharing with non-existent user
        data = {'username': 'nonexistent'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "User 'nonexistent' not found")
        
        # Test sharing with invalid username format
        data = {'username': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "Username is required")
        
        # Test sharing with invalid permission
        data = {'username': self.other_user.username, 'permission': 'INVALID'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('Invalid permission' in response.data['error'])
        
        # Test sharing task that doesn't exist
        url = reverse('task-share', kwargs={'pk': 9999})
        data = {'username': 'testuser'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test sharing with self
        url = reverse('task-share', kwargs={'pk': task.pk})
        data = {'username': self.user.username}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], "You cannot share a task with yourself")
        
        # Test sharing with same user twice with same permission
        data = {'username': self.other_user.username, 'permission': 'VIEW'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("already shared with user" in response.data['error'])
        
        # Test updating share permission
        data = {'username': self.other_user.username, 'permission': 'EDIT'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['permission'], 'EDIT')

    def test_notification_preferences_edge_cases(self):
        """Test notification preferences edge cases"""
        url = reverse('notification-preference-list')
        
        # Test invalid timing value
        data = {
            'notification_timing': 'INVALID',
            'email_notifications': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_timing', response.data)
        
        # Test empty timing value
        data = {
            'notification_timing': '',
            'email_notifications': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('notification_timing', response.data)
        
        # Test creating first preference
        data = {
            'notification_timing': '24H',
            'email_notifications': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['notification_timing'], '24H')
        
        # Test creating duplicate preference
        data = {
            'notification_timing': '12H',
            'email_notifications': True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
        
        # Test updating existing preference
        pref = NotificationPreference.objects.get(user=self.user)
        url = reverse('notification-preference-detail', kwargs={'pk': pref.id})
        data = {
            'notification_timing': '12H',
            'email_notifications': True
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['notification_timing'], '12H')

    def test_authentication_edge_cases(self):
        """Test authentication edge cases"""
        # Test accessing protected endpoint without authentication
        self.client.force_authenticate(user=None)
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test accessing another user's task
        self.client.force_authenticate(user=self.other_user)
        url = reverse('task-detail', kwargs={'pk': self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test modifying another user's task
        data = {'title': 'Unauthorized Update'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tag_edge_cases(self):
        """Test tag edge cases"""
        url = reverse('tag-list')
        
        # Test invalid color format
        data = {
            'name': 'New Tag',
            'color': 'invalid-color'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('color', response.data)
        
        # Test duplicate tag name for same user
        data = {
            'name': self.tag.name,  # Using existing tag name
            'color': '#00FF00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        
        # Test empty tag name
        data = {
            'name': '',
            'color': '#00FF00'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)

    def test_category_edge_cases(self):
        """Test category edge cases"""
        url = reverse('category-list')
        
        # Test empty category name
        data = {'name': ''}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        
        # Test duplicate category name for same user
        data = {'name': self.category.name}  # Using existing category name
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)
        
        # Test category name too long
        data = {'name': 'a' * 101}  # Assuming max_length is 100
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data) 