from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login

from .models import User, Task, Project


class UserRegisterationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with secure password handling.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')  # Extract the password
        user = User(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login with JWT token generation.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    role = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Not used but required by Serializer class
        pass

    def update(self, instance, validated_data):
        # Not used but required by Serializer class
        pass

    def validate(self, data):
        email = data['email']
        password = data['password']
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid login credentials")

        try:
            refresh = RefreshToken.for_user(user)
            refresh_token = str(refresh)
            access_token = str(refresh.access_token)
            update_last_login(None, user)

            validation = {
                'access': access_token,
                'refresh': refresh_token,
                'email': user.email,
                'role': user.role,
            }

            return validation
        except Exception as e:
            raise serializers.ValidationError(f"Login error: {e}")


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users with their role information.
    """
    role_name = serializers.SerializerMethodField(read_only=True)
    email = serializers.EmailField(read_only=True)
    role = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'email',
            'role',
            'role_name'
        )
        read_only_fields = ['email', 'role', 'role_name']
    
    def get_role_name(self, obj):
        return obj.get_role_display()


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user roles by admin.
    """
    class Meta:
        model = User
        fields = ['role', 'is_active']
        
    def validate_role(self, value):
        if value not in [User.ADMIN, User.PROJECT_MANAGER, User.DEVELOPER]:
            raise serializers.ValidationError("Invalid role selected")
        return value


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for project CRUD operations.
    """
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id',
            'title',
            'description',
            'created_by',
            'created_by_email',
            'start_date',
            'end_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by_email', 'created_by']


class TaskSerializer(serializers.ModelSerializer):
    """
    Serializer for task CRUD operations.
    """
    project_title = serializers.CharField(source='project.title', read_only=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'project',
            'project_title',
            'assigned_to',
            'assigned_to_email',
            'status',
            'priority',
            'start_date',
            'end_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'project_title', 'assigned_to_email']


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning tasks to developers (used by project managers).
    """
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)
    developer_name = serializers.SerializerMethodField(read_only=True)
    developer_email = serializers.EmailField(write_only=True, required=False)
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'project',
            'project_title',
            'assigned_to',
            'assigned_to_email',
            'developer_name',
            'developer_email',
            'status',
            'priority'
        ]
        read_only_fields = [
            'id', 
            'title', 
            'project', 
            'project_title', 
            'assigned_to_email', 
            'developer_name'
        ]
    
    def get_developer_name(self, obj):
        """Get the full name of the assigned developer."""
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}"
        return None
    
    def validate(self, data):
        # If developer_email is provided, find the user by email and set assigned_to
        if 'developer_email' in data:
            email = data.pop('developer_email')
            try:
                user = User.objects.get(email=email)
                if user.role != User.DEVELOPER:
                    raise serializers.ValidationError({"developer_email": "This user is not a developer"})
                data['assigned_to'] = user
            except User.DoesNotExist:
                raise serializers.ValidationError({"developer_email": f"No user found with email {email}"})
        
        return data
        
    def validate_assigned_to(self, user_id):
        # Skip validation if we're using email
        if self.initial_data.get('developer_email'):
            return user_id
            
        # Validate the user ID exists and is a developer
        try:
            user = User.objects.get(id=user_id)
            if user.role != User.DEVELOPER:
                raise serializers.ValidationError("Tasks can only be assigned to users with Developer role")
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("Developer with this ID does not exist")