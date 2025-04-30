from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for handling email-based authentication 
    instead of Django's default username-based authentication.
    """
    def create_user(self, email, password, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: User's email address (used as username)
            password: User's password
            extra_fields: Additional fields to store with user
            
        Returns:
            The newly created user object
        
        Raises:
            ValueError: If email or password is not provided
        """
        if not email:
            raise ValueError(_("The email must be set"))
        if not password:
            raise ValueError(_("The password must be set"))

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hash the password
        user.save()
        return user
    
    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        
        Args:
            email: Admin email address
            password: Admin password
            extra_fields: Additional fields to store with admin user
            
        Returns:
            The newly created admin user
            
        Raises:
            ValueError: If the role is not set to admin (1)
        """
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('role', 1)  # Admin role

        if extra_fields.get('role') != 1:
            raise ValueError(_("The superuser must have admin role (role=1)"))
            
        return self.create_user(email, password, **extra_fields)