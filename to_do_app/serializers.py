from rest_framework import serializers
from .models import Task, Category, TaskShare
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['date_joined']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs

class TaskShareSerializer(serializers.ModelSerializer):
    shared_with_username = serializers.CharField(source='shared_with.username', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = TaskShare
        fields = ['id', 'task', 'task_title', 'shared_with', 'shared_with_username', 
                 'permission', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        task = data.get('task')
        shared_with = data.get('shared_with')
        
        # Check if user is trying to share with themselves
        if shared_with == self.context['request'].user:
            raise serializers.ValidationError("You cannot share a task with yourself")
        
        # Check if task belongs to the user
        if task.user != self.context['request'].user:
            raise serializers.ValidationError("You can only share tasks that you own")
        
        return data

class TaskSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    shares = TaskShareSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'created_at', 
                 'updated_at', 'due_date', 'user', 'owner_username', 'category', 
                 'category_id', 'priority', 'priority_display', 'shares']
        read_only_fields = ['created_at', 'updated_at', 'user']

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        validated_data['user'] = self.context['request'].user
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=validated_data['user'])
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_id': 'Category not found or does not belong to user'})
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=instance.user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_id': 'Category not found or does not belong to user'})
        
        return super().update(instance, validated_data)