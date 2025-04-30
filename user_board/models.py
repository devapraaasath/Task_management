from django.db import models
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils import timezone
import uuid

from .manager import CustomUserManager

class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model that uses email as the unique identifier
    instead of username for authentication.
    """
    # Role constants
    ADMIN = 1
    PROJECT_MANAGER = 2
    DEVELOPER = 3

    ROLE_CHOICES = (
        (ADMIN, 'Admin'),
        (PROJECT_MANAGER, 'Project Manager'),
        (DEVELOPER, 'Developer')
    )

    uuid = models.UUIDField(
        unique=True,
        editable=True, 
        default=uuid.uuid4, 
        verbose_name='Public Identifier'
    )
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.PositiveSmallIntegerField(
        choices=ROLE_CHOICES, 
        blank=True, 
        null=True, 
        default=DEVELOPER
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    create_by = models.EmailField(null=True, blank=True)  # Keep original field name to match DB schema
    modified_by = models.EmailField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        
    def __str__(self):
        return self.email
    
class Project(models.Model):
    """
    Project model to group related tasks and track timelines.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=255)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_projects'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class Task(models.Model):
    """
    Task model for tracking individual work items within projects.
    """
    # Status options
    STATUS_TODO = 'To-Do'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_DONE = 'Done'
    
    STATUS_CHOICES = [
        (STATUS_TODO, 'To-Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_DONE, 'Done'),
    ]
    
    # Priority options
    PRIORITY_LOW = 'Low'
    PRIORITY_MEDIUM = 'Medium'
    PRIORITY_HIGH = 'High'
    
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=255)
    project = models.ForeignKey(
        Project, 
        on_delete=models.CASCADE, 
        related_name='tasks', 
        null=True, 
        blank=True
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_tasks'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=STATUS_TODO
    )
    priority = models.CharField(
        max_length=20, 
        choices=PRIORITY_CHOICES, 
        default=PRIORITY_MEDIUM
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
