from rest_framework import serializers
from .models import Task
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class TaskSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'completed',
            'due_date',
            'user',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # Get the current user from the context
        user = self.context['request'].user
        # Create the task with the current user
        task = Task.objects.create(user=user, **validated_data)
        return task