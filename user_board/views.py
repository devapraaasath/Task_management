from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import User, Project, Task
from .serializer import (
    UserRegisterationSerializer,
    UserLoginSerializer,
    UserListSerializer, 
    UserRoleUpdateSerializer, 
    TaskSerializer, 
    ProjectSerializer,
    TaskAssignmentSerializer
)
from .permission import (
    IsAdminOrReadOnly, 
    IsAdminUser, 
    IsProjectManagerOrAdmin, 
    ProjectAccessPermission, 
    TaskUpdatePermission
)


class AuthUserRegistrationView(APIView):
    """
    User Registration API View
    
    This API allows new users to register by providing their personal information.
    
    Request body should contain:
    * first_name - First name of the user
    * last_name - Last name of the user
    * email - Email address (used for login)
    * password - Password for the account
    """
    serializer_class = UserRegisterationSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Register a new user
        
        Creates a new user account with the provided information.
        
        Request body format:
        {
            "first_name": "string",
            "last_name": "string",
            "email": "user@example.com",
            "password": "string"
        }
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'success': True,
            'message': 'The user registered successfully',
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)
    

class AuthUserLoginView(APIView):
    """
    User Login API View
    
    This API allows users to login with their email and password.
    It returns JWT tokens (access and refresh) for authentication.
    
    Request body should contain:
    * email - Email address used during registration
    * password - Password for the account
    """
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)
    
    def post(self, request):
        """
        Login a user
        
        Authenticates a user and returns JWT tokens.
        
        Request body format:
        {
            "email": "user@example.com",
            "password": "string"
        }
        
        Returns JWT tokens which should be included in the Authorization
        header as: JWT <access_token>
        """
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        
        if valid:
            status_code = status.HTTP_200_OK
            response_data = {
                'success': True,
                'status_code': status_code,
                'message': 'User logged in successfully',
                'access': serializer.data['access'],
                'refresh': serializer.data['refresh'],
                'authenticatedUser': {
                    'email': serializer.data['email'],
                    'role': serializer.data['role']
                }
            }
            return Response(response_data, status=status_code)


class UserListView(APIView):
    """
    User List API View
    
    This API returns a list of all users. Only accessible by admins (role=1).
    Requires JWT authentication with the Authorization header.
    
    No request body is needed - just authorization.
    
    To authenticate:
    1. Get token from /login/ endpoint
    2. Add header: Authorization: JWT your_token_here
    """
    serializer_class = UserListSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        Get all users
        
        Returns a list of all users if the authenticated user is an admin.
        No request body is required for this endpoint.
        """
        user = request.user

        if user.role != User.ADMIN:
            return Response({
                'success': False,
                'status_code': status.HTTP_403_FORBIDDEN,
                'message': 'Only admins are authorized to view user list.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        response = {
            'success': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Successfully fetched users',
            'users': serializer.data
        }
        return Response(response, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="project",
            description="Filter by project ID",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="status",
            description="Filter by task status (e.g., 'To-Do', 'In Progress', 'Completed')",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="priority",
            description="Filter by task priority (e.g., 'Low', 'Medium', 'High')",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="due_date",
            description="Filter by due date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=OpenApiTypes.INT
        ),
    ]
)
class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    Task List and Create API View
    
    - List: Returns tasks filtered by user role
      * Can filter by project_id with ?project=<id>
      * Can filter by status with ?status=<status>
      * Can filter by priority with ?priority=<priority>
      * Can filter by due date with ?due_date=<YYYY-MM-DD>
    - Create: Only admins and project managers can create tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Set the project creator as the current user"""
        serializer.save()
        
    def get_queryset(self):
        """Filter tasks based on user role"""
        user = self.request.user
        
        # Determine visible tasks based on user role
        if user.role in [User.ADMIN, User.PROJECT_MANAGER]:
            # Admins and Project Managers see all tasks
            queryset = Task.objects.all()
        else:
            # Developers see only tasks assigned to them
            queryset = Task.objects.filter(assigned_to=user)
        
        # Apply filters from query parameters
        project_id = self.request.query_params.get('project')
        status_val = self.request.query_params.get('status')
        priority_val = self.request.query_params.get('priority')
        due_date = self.request.query_params.get('due_date')
        
        # Apply filters if provided
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        if status_val:
            queryset = queryset.filter(status=status_val)
            
        if priority_val:
            queryset = queryset.filter(priority=priority_val)
            
        if due_date:
            queryset = queryset.filter(end_date=due_date)
            
        return queryset.order_by('-created_at')


class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Task Detail, Update and Delete API View
    
    - Retrieve: Returns task details (if user has permission)
    - Update: 
        - Admins can update anything
        - Project Managers can update all tasks
        - Developers can only update status of their assigned tasks
    - Delete: Only admins and project managers can delete tasks
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, TaskUpdatePermission]
    
    def get_queryset(self):
        """Filter tasks based on user role"""
        user = self.request.user
        
        if user.role in [User.ADMIN, User.PROJECT_MANAGER]:
            # Admins and Project Managers see all tasks
            return Task.objects.all()
            
        # Developers see only tasks assigned to them
        return Task.objects.filter(assigned_to=user)
    
    def update(self, request, *args, **kwargs):
        """Update task with appropriate role-based restrictions"""
        task = self.get_object()
        user = request.user
        
        # For developers, only allow status updates
        if user.role == User.DEVELOPER:
            if not request.data or set(request.data.keys()) - {'status'}:
                return Response({
                    'success': False,
                    'status_code': status.HTTP_400_BAD_REQUEST,
                    'message': 'Developers can only update task status.'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(task, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'success': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Task updated successfully',
            'task': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Delete task with permission check"""
        user = request.user
        
        # Only admins and project managers can delete tasks
        if user.role not in [User.ADMIN, User.PROJECT_MANAGER]:
            return Response({
                'success': False,
                'status_code': status.HTTP_403_FORBIDDEN,
                'message': 'Only admins and project managers can delete tasks.'
            }, status=status.HTTP_403_FORBIDDEN)
            
        return super().destroy(request, *args, **kwargs)


# Project CRUD Views
@extend_schema(
    parameters=[
        OpenApiParameter(
            name="title",
            description="Filter by project title (partial match)",
            required=False,
            type=OpenApiTypes.STR
        ),
        OpenApiParameter(
            name="created_by",
            description="Filter by creator user ID",
            required=False,
            type=OpenApiTypes.INT
        ),
        OpenApiParameter(
            name="start_date",
            description="Filter by start date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="end_date",
            description="Filter by end date (format: YYYY-MM-DD)",
            required=False,
            type=OpenApiTypes.DATE
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=OpenApiTypes.INT
        ),
    ]
)
class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    Project List and Create API View
    
    - List: Returns a list of all projects (filtered by role)
      * Can filter by title with ?title=<title>
      * Can filter by created_by with ?created_by=<user_id>
      * Can filter by start_date with ?start_date=<YYYY-MM-DD>
      * Can filter by end_date with ?end_date=<YYYY-MM-DD>
    - Create: Creates a new project (admin only)
    
    Request body for Create:
    {
        "title": "Project Title",
        "description": "Project Description",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectAccessPermission]
    
    def perform_create(self, serializer):
        """Save the current user as the project creator"""
        serializer.save(created_by=self.request.user)
        
    def get_queryset(self):
        """Filter projects based on user role"""
        user = self.request.user
        
        # Determine visible projects based on user role
        if user.role in [User.ADMIN, User.PROJECT_MANAGER]:
            # Admins and Project Managers see all projects
            queryset = Project.objects.all()
        else:
            # Developers see only projects where they have assigned tasks
            developer_task_projects = Task.objects.filter(
                assigned_to=user
            ).values_list('project_id', flat=True).distinct()
            queryset = Project.objects.filter(id__in=developer_task_projects)
            
        # Apply filters from query parameters
        title = self.request.query_params.get('title')
        created_by = self.request.query_params.get('created_by')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        # Apply filters if provided
        if title:
            queryset = queryset.filter(title__icontains=title)
            
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
            
        if start_date:
            queryset = queryset.filter(start_date=start_date)
            
        if end_date:
            queryset = queryset.filter(end_date=end_date)
            
        return queryset.order_by('-created_at')


class ProjectRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Project Detail, Update and Delete API View
    
    - Retrieve: Returns project details (if user has permission)
    - Update: Only admins can update projects
    - Delete: Only admins can delete projects
    """
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectAccessPermission]
    
    def get_queryset(self):
        """Filter projects based on user role"""
        user = self.request.user
        
        if user.role in [User.ADMIN, User.PROJECT_MANAGER]:
            # Admins and Project Managers see all projects
            return Project.objects.all()
            
        # Developers see only projects where they have assigned tasks
        developer_task_projects = Task.objects.filter(
            assigned_to=user
        ).values_list('project_id', flat=True).distinct()
        return Project.objects.filter(id__in=developer_task_projects)


# User Role Management View (Admin only)
class UserRoleUpdateView(generics.UpdateAPIView):
    """
    User Role Management API View
    
    This API allows admins to update user roles and activation status.
    Only accessible by admins (role=1).
    
    Request body format:
    {
        "role": 2,  # 1=Admin, 2=Project Manager, 3=Developer
        "is_active": true
    }
    """
    queryset = User.objects.all()
    serializer_class = UserRoleUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'email'
    
    def update(self, request, *args, **kwargs):
        """Update user role with validation"""
        email = kwargs.get('email')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'status_code': status.HTTP_404_NOT_FOUND,
                'message': f'User with email {email} not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.serializer_class(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'status_code': status.HTTP_200_OK,
            'message': 'User role updated successfully',
            'user': serializer.data
        })


# Task Assignment View (Project Manager & Admin only)
class TaskAssignmentView(generics.UpdateAPIView):
    """
    Task Assignment API View
    
    This API allows project managers and admins to assign tasks to developers.
    
    Request body format (using developer ID):
    {
        "assigned_to": 5,  # User ID of a developer
        "status": "In Progress",  # Optional status update
        "priority": "High"  # Optional priority update
    }
    
    OR assign by email (recommended):
    {
        "developer_email": "dev1@company.com",  # Email of the developer
        "status": "In Progress",  # Optional status update
        "priority": "High"  # Optional priority update
    }
    """
    queryset = Task.objects.all()
    serializer_class = TaskAssignmentSerializer
    permission_classes = [IsAuthenticated, IsProjectManagerOrAdmin]
    
    def get_queryset(self):
        """Filter tasks based on user role"""
        user = self.request.user
        
        if user.role == User.ADMIN:
            # Admins can assign any task
            return Task.objects.all()
        elif user.role == User.PROJECT_MANAGER:
            # Project managers can assign any task
            return Task.objects.all()
            
        # Developers should not be able to access this view
        # (Handled by permission class, but adding as safety)
        return Task.objects.none()
    
    def update(self, request, *args, **kwargs):
        """Assign a task to a developer"""
        task = self.get_object()
        
        # Validate that the task exists
        if not task:
            return Response({
                'success': False,
                'status_code': status.HTTP_404_NOT_FOUND,
                'message': 'Task not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        # Check if developer email is provided
        developer_email = request.data.get('developer_email')
        
        # If email provided, find the user
        if developer_email:
            try:
                developer = User.objects.get(email=developer_email)
                
                # Verify the user is a developer
                if developer.role != User.DEVELOPER:
                    return Response({
                        'success': False,
                        'status_code': status.HTTP_400_BAD_REQUEST,
                        'message': 'Tasks can only be assigned to developers'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                # Add the user ID to the request data
                mutable_data = request.data.copy()
                mutable_data['assigned_to'] = developer.id
                request._full_data = mutable_data
                
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'status_code': status.HTTP_404_NOT_FOUND,
                    'message': f'Developer with email {developer_email} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Use the serializer for validation and updating
        serializer = self.serializer_class(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'status_code': status.HTTP_200_OK,
            'message': 'Task assigned successfully',
            'task': serializer.data
        })
