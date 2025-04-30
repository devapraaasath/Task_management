from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Permission class that allows read-only access to all users,
    but restricts write operations to admin users only.
    """
    def has_permission(self, request, view):
        # Allow GET, HEAD, OPTIONS requests for all users
        if request.method in SAFE_METHODS:
            return True
        # Restrict write operations to admin users
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsAdminUser(BasePermission):
    """
    Permission class that only allows access to admin users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 1  # ADMIN role


class IsProjectManagerOrAdmin(BasePermission):
    """
    Permission class that only allows access to project managers or admins.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [1, 2]  # ADMIN or PROJECT_MANAGER
        )


class ProjectAccessPermission(BasePermission):
    """
    Project permission rules:
    - Admins have full CRUD access
    - Project Managers have read-only access
    - Developers have read-only access to projects
    """
    def has_permission(self, request, view):
        # Everyone who is authenticated can view projects (GET)
        if request.method in SAFE_METHODS:
            return True
        
        # Only admins can create/update/delete projects
        return request.user.role == 1


class TaskUpdatePermission(BasePermission):
    """
    Permission rules for task updates:
    - Admins can perform any operation
    - Project Managers can perform any operation on all tasks
    - Developers can only update the status of their assigned tasks
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Admin can do anything
        if user.role == 1:
            return True
            
        # Project managers can update all tasks
        if user.role == 2:
            return True
            
        # Developers can only update status of their assigned tasks
        if user.role == 3 and obj.assigned_to == user:
            # For developers, only allow partial updates to the status field
            if request.method == 'PATCH':
                # Check if they're only trying to update the status
                if set(request.data.keys()).issubset({'status'}):
                    return True
            return False
            
        return False
