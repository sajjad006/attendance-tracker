from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json


class ActionType(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    SOFT_DELETE = "soft_delete", "Soft Delete"
    RESTORE = "restore", "Restore"


class AuditLog(models.Model):
    """
    Tracks all changes to critical records for audit purposes.
    Stores user, action type, old/new values, and related object.
    """
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs"
    )
    action = models.CharField(max_length=20, choices=ActionType.choices)
    
    # Generic relation to the affected object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="audit_logs"
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    
    # Store object representation for deleted objects
    object_repr = models.CharField(max_length=255)
    
    # Store old and new values as JSON
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    # Additional metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["action"]),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.content_type.model} ({self.object_id})"
    
    @classmethod
    def log_action(
        cls,
        user,
        action,
        obj,
        old_values=None,
        new_values=None,
        ip_address=None,
        user_agent=None
    ):
        """
        Create an audit log entry.
        
        Args:
            user: The user performing the action
            action: ActionType enum value
            obj: The model instance being affected
            old_values: Dictionary of old field values
            new_values: Dictionary of new field values
            ip_address: Optional IP address of the request
            user_agent: Optional user agent string
        """
        content_type = ContentType.objects.get_for_model(obj)
        
        return cls.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=obj.pk,
            object_repr=str(obj)[:255],
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def get_changes_for_object(cls, obj):
        """Get all audit logs for a specific object."""
        content_type = ContentType.objects.get_for_model(obj)
        return cls.objects.filter(
            content_type=content_type,
            object_id=obj.pk
        )
    
    @classmethod
    def get_user_activity(cls, user, limit=50):
        """Get recent activity for a user."""
        return cls.objects.filter(user=user)[:limit]
    
    def get_changed_fields(self):
        """Return a list of fields that changed."""
        if not self.old_values or not self.new_values:
            return []
        
        changed = []
        all_keys = set(self.old_values.keys()) | set(self.new_values.keys())
        
        for key in all_keys:
            old_val = self.old_values.get(key)
            new_val = self.new_values.get(key)
            if old_val != new_val:
                changed.append({
                    "field": key,
                    "old": old_val,
                    "new": new_val
                })
        
        return changed
