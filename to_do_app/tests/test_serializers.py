from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from ..models import Task, Category, Tag
from ..serializers import (
    TaskSerializer,
    CategorySerializer,
    TagSerializer,
    UserRegistrationSerializer
)

class SerializerTestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/')
        self.request.user = self.user

    def test_user_registration_serializer(self):
        """Test user registration serializer"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password2': 'newpass123'
        }
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Test password mismatch
        data['password2'] = 'wrongpass'
        serializer = UserRegistrationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_category_serializer(self):
        """Test category serializer"""
        data = {
            'name': 'Test Category',
            'description': 'Test Description'
        }
        serializer = CategorySerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        category = serializer.save()
        self.assertEqual(category.user, self.user)
        self.assertEqual(category.name, data['name'])

    def test_tag_serializer(self):
        """Test tag serializer"""
        data = {
            'name': 'Test Tag',
            'color': '#FF0000'
        }
        serializer = TagSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertEqual(tag.user, self.user)
        self.assertEqual(tag.name, data['name'])
        
        # Test invalid color format
        data['color'] = 'invalid'
        serializer = TagSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('color', serializer.errors)

    def test_task_serializer(self):
        """Test task serializer"""
        # Test task creation without category
        data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'priority': 'HIGH',
            'tag_names': ['New Tag']
        }
        
        serializer = TaskSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        task = serializer.save()
        
        # Check if task was created correctly
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.title, data['title'])
        self.assertIsNone(task.category)
        self.assertEqual(task.tags.count(), 1)  # One new tag
        
        # Test task creation with category
        category = Category.objects.create(
            name='Test Category',
            user=self.user
        )
        tag = Tag.objects.create(
            name='Test Tag',
            color='#FF0000',
            user=self.user
        )
        
        data = {
            'title': 'Test Task with Category',
            'description': 'Test Description',
            'priority': 'HIGH',
            'category_id': category.id,
            'tag_ids': [tag.id],
            'tag_names': ['Another Tag']
        }
        
        serializer = TaskSerializer(
            data=data,
            context={'request': self.request}
        )
        self.assertTrue(serializer.is_valid())
        task = serializer.save()
        
        # Check if task was created correctly
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.title, data['title'])
        self.assertEqual(task.category, category)
        self.assertEqual(task.tags.count(), 2)  # One existing tag + one new tag
        
        # Test task update
        update_data = {
            'title': 'Updated Task',
            'description': 'Updated Description',
            'priority': 'LOW'
        }
        serializer = TaskSerializer(
            task,
            data=update_data,
            context={'request': self.request},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_task = serializer.save()
        self.assertEqual(updated_task.title, update_data['title'])
        self.assertEqual(updated_task.priority, update_data['priority']) 