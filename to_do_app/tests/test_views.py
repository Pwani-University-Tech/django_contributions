from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import Task, Category, Tag, TaskShare

class ViewTestCase(TestCase):
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
            priority='HIGH'
        )
        self.task.tags.add(self.tag)

    def test_user_registration(self):
        """Test user registration endpoint"""
        url = reverse('user-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        
        # Log out for registration test
        self.client.force_authenticate(user=None)
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())

    def test_category_crud(self):
        """Test category CRUD operations"""
        # Create
        url = reverse('category-list')
        data = {'name': 'New Category', 'description': 'New Description'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Read
        category_id = response.data['id']
        url = reverse('category-detail', args=[category_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Category')
        
        # Update
        data = {'name': 'Updated Category', 'description': 'Updated Description'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Category')
        
        # Delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_tag_crud(self):
        """Test tag CRUD operations"""
        # Create
        url = reverse('tag-list')
        data = {'name': 'New Tag', 'color': '#00FF00'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Read
        tag_id = response.data['id']
        url = reverse('tag-detail', args=[tag_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'New Tag')
        
        # Update
        data = {'name': 'Updated Tag', 'color': '#0000FF'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Updated Tag')
        
        # Delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_crud(self):
        """Test task CRUD operations"""
        # Create
        url = reverse('task-list')
        data = {
            'title': 'New Task',
            'description': 'New Description',
            'priority': 'MEDIUM',
            'category_id': self.category.id,
            'tag_ids': [self.tag.id]
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Read
        task_id = response.data['id']
        url = reverse('task-detail', args=[task_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'New Task')
        
        # Update
        data = {
            'title': 'Updated Task',
            'description': 'Updated Description',
            'priority': 'HIGH'
        }
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        
        # Delete
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_task_sharing(self):
        """Test task sharing functionality"""
        # Create a task to share
        task = Task.objects.create(
            title='Task to Share',
            description='Test Description',
            user=self.user,
            priority='HIGH'
        )
        
        # Share task
        url = reverse('task-share', kwargs={'pk': task.id})
        data = {
            'username': self.other_user.username,
            'permission': 'VIEW'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify other user can access the task
        self.client.force_authenticate(user=self.other_user)
        url = reverse('task-detail', kwargs={'pk': task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify other user cannot edit the task
        data = {'title': 'Unauthorized Update'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify task owner can still edit the task
        self.client.force_authenticate(user=self.user)
        data = {'title': 'Authorized Update'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Authorized Update')

    def test_task_filtering(self):
        """Test task filtering and search"""
        url = reverse('task-list')
        
        # Filter by category
        response = self.client.get(url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Filter by priority
        response = self.client.get(url, {'priority': 'HIGH'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Search by title
        response = self.client.get(url, {'search': 'Test Task'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Filter by tag
        response = self.client.get(url, {'tags': self.tag.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) 