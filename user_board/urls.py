from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from .views import (
    AuthUserRegistrationView, 
    AuthUserLoginView, 
    UserListView, 
    TaskListCreateAPIView, 
    TaskRetrieveUpdateDestroyAPIView,
    ProjectListCreateAPIView, 
    ProjectRetrieveUpdateDestroyAPIView,
    UserRoleUpdateView, 
    TaskAssignmentView
)


urlpatterns = [
    # Authentication endpoints
    path('token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_create'),
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', AuthUserRegistrationView.as_view(), name='register'),
    path('login/', AuthUserLoginView.as_view(), name='login'),
    
    # User management endpoints
    path('users/', UserListView.as_view(), name='users'),
    path('users/<str:email>/role/', UserRoleUpdateView.as_view(), name='user_role_update'),

    # Project endpoints
    path('projects/', ProjectListCreateAPIView.as_view(), name='project_list_create'),
    path('projects/<int:pk>/', ProjectRetrieveUpdateDestroyAPIView.as_view(), name='project_detail'),

    # Task endpoints - using the original URL names to match tests
    path('tasks/', TaskListCreateAPIView.as_view(), name='task_Create'),
    path('tasks/<int:pk>/', TaskRetrieveUpdateDestroyAPIView.as_view(), name='task_update'),
    path('tasks/<int:pk>/assign/', TaskAssignmentView.as_view(), name='task_assignment')
]
