from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom user model for authentication.
    Students use username-based authentication.
    """
    email = models.EmailField(unique=False, blank=True, null=True)
    timezone = models.CharField(
        max_length=50, 
        default="UTC",
        help_text="User's preferred timezone for display"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "users_user"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.username} ({self.get_full_name()})"
