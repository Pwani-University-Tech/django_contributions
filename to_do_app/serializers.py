from rest_framework import serializers
from .models import Task, Category, TaskShare, NotificationPreference, TaskNotification, Tag
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

    def validate_name(self, value):
        """Validate that the category name is unique for the user"""
        user = self.context['request'].user
        if Category.objects.filter(name=value, user=user).exists():
            if self.instance and self.instance.name == value:
                return value
            raise serializers.ValidationError("You already have a category with this name")
        return value

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

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    timing_display = serializers.CharField(source='get_notification_timing_display', read_only=True)

    class Meta:
        model = NotificationPreference
        fields = ['id', 'email_notifications', 'notification_timing', 
                 'timing_display', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_notification_timing(self, value):
        """Validate that the notification timing is valid"""
        valid_timings = dict(NotificationPreference.NOTIFICATION_TIMING_CHOICES)
        if value not in valid_timings:
            raise serializers.ValidationError(
                f"Invalid notification timing. Must be one of: {', '.join(valid_timings.keys())}"
            )
        return value

    def validate(self, data):
        """Validate that the notification preferences are unique"""
        timing = data.get('notification_timing')
        if timing is not None:
            user = self.context['request'].user
            # Check for existing preference with same timing
            if NotificationPreference.objects.filter(
                user=user,
                notification_timing=timing
            ).exclude(id=getattr(self.instance, 'id', None)).exists():
                raise serializers.ValidationError({
                    "notification_timing": "You already have a notification preference with this timing"
                })
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        # Check if user already has preferences
        if NotificationPreference.objects.filter(user=user).exists():
            raise serializers.ValidationError({
                "non_field_errors": "You can only have one notification preference. Use PUT to update existing preferences."
            })
        validated_data['user'] = user
        return super().create(validated_data)

class TaskNotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = TaskNotification
        fields = ['id', 'task', 'task_title', 'scheduled_time', 
                 'status', 'status_display', 'created_at', 'sent_at']
        read_only_fields = ['created_at', 'sent_at', 'status']

class TagSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at', 'updated_at', 'task_count']
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        """Validate that the tag name is unique for the user"""
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            if Tag.objects.filter(name=value, user=user).exists():
                if self.instance and self.instance.name == value:
                    return value
                raise serializers.ValidationError("You already have a tag with this name")
        return value

    def validate_color(self, value):
        """Validate that the color is a valid hex color code"""
        if not value.startswith('#'):
            value = f'#{value}'
        
        if len(value) != 7:  # #RRGGBB format
            raise serializers.ValidationError("Color must be in #RRGGBB format")
        
        try:
            int(value[1:], 16)  # Try to convert hex to int
        except ValueError:
            raise serializers.ValidationError("Invalid hex color code")
        
        return value

    def create(self, validated_data):
        # Assign the current user
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)

class TaskSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    shares = TaskShareSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='user.username', read_only=True)
    notifications = TaskNotificationSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of tag names. New tags will be created if they don't exist."
    )

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'completed', 'created_at', 
                 'updated_at', 'due_date', 'user', 'owner_username', 'category', 
                 'category_id', 'priority', 'priority_display', 'shares',
                 'notifications', 'tags', 'tag_ids', 'tag_names']
        read_only_fields = ['created_at', 'updated_at', 'user']

    def _handle_tags(self, task, tag_ids=None, tag_names=None):
        """
        Handle tag assignment for a task
        - tag_ids: List of existing tag IDs to assign
        - tag_names: List of tag names to assign (creates new tags if needed)
        """
        user = task.user
        
        if tag_ids:
            # Verify all tags exist and belong to the user
            tags = Tag.objects.filter(id__in=tag_ids, user=user)
            if len(tags) != len(tag_ids):
                raise serializers.ValidationError({
                    'tag_ids': 'One or more tags do not exist or do not belong to you'
                })
            task.tags.set(tags)
        
        if tag_names:
            tags = []
            for name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=name,
                    user=user,
                    defaults={'color': '#FF0000'}  # Default color for new tags
                )
                tags.append(tag)
            
            # If tag_ids weren't provided, replace all tags
            if not tag_ids:
                task.tags.set(tags)
            else:
                # Otherwise, add to existing tags
                task.tags.add(*tags)

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        tag_names = validated_data.pop('tag_names', None)
        category_id = validated_data.pop('category_id', None)
        validated_data['user'] = self.context['request'].user
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=validated_data['user'])
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_id': 'Category not found or does not belong to user'})
        
        task = super().create(validated_data)
        
        # Handle tags
        self._handle_tags(task, tag_ids, tag_names)
        
        # Create notification if due date is set
        if task.due_date:
            self._create_notification(task)
        
        return task

    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        tag_names = validated_data.pop('tag_names', None)
        category_id = validated_data.pop('category_id', None)
        old_due_date = instance.due_date
        
        if category_id:
            try:
                category = Category.objects.get(id=category_id, user=instance.user)
                validated_data['category'] = category
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_id': 'Category not found or does not belong to user'})
        
        task = super().update(instance, validated_data)
        
        # Handle tags
        self._handle_tags(task, tag_ids, tag_names)
        
        # Update notification if due date changed
        if task.due_date != old_due_date:
            TaskNotification.objects.filter(task=task, status='PENDING').delete()
            if task.due_date:
                self._create_notification(task)
        
        return task

    def _create_notification(self, task):
        from datetime import timedelta
        
        # Get user's notification preference
        try:
            pref = task.user.notification_preference
        except NotificationPreference.DoesNotExist:
            # Create default preference
            pref = NotificationPreference.objects.create(user=task.user)
        
        if not pref.email_notifications:
            return
        
        # Calculate notification time based on preference
        timing_map = {
            '1H': timedelta(hours=1),
            '3H': timedelta(hours=3),
            '6H': timedelta(hours=6),
            '12H': timedelta(hours=12),
            '24H': timedelta(hours=24),
            '48H': timedelta(hours=48),
            '1W': timedelta(weeks=1),
        }
        
        notification_delta = timing_map[pref.notification_timing]
        scheduled_time = task.due_date - notification_delta
        
        # Create notification
        TaskNotification.objects.create(
            task=task,
            user=task.user,
            scheduled_time=scheduled_time
        )