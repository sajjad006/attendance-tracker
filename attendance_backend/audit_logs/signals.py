from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.dispatch import receiver
from .models import AuditLog, ActionType
import threading


# Thread-local storage for request context
_thread_locals = threading.local()


def set_current_user(user, ip_address=None, user_agent=None):
    """Set the current user for audit logging."""
    _thread_locals.user = user
    _thread_locals.ip_address = ip_address
    _thread_locals.user_agent = user_agent


def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, "user", None)


def get_request_metadata():
    """Get request metadata from thread-local storage."""
    return {
        "ip_address": getattr(_thread_locals, "ip_address", None),
        "user_agent": getattr(_thread_locals, "user_agent", None)
    }


def clear_current_user():
    """Clear the current user from thread-local storage."""
    _thread_locals.user = None
    _thread_locals.ip_address = None
    _thread_locals.user_agent = None


# Store pre-save state for comparison
_pre_save_state = threading.local()


def get_model_fields_for_audit(instance):
    """Get relevant fields from model instance for audit logging."""
    from decimal import Decimal
    from uuid import UUID
    from datetime import date, datetime, time, timedelta
    
    data = {}
    
    # Iterate through all model fields directly to capture everything
    for field in instance._meta.get_fields():
        # Skip reverse relations and many-to-many for simplicity
        if field.one_to_many or field.many_to_many:
            continue
        
        # Skip auto-generated fields that aren't useful
        if field.name in ['id', 'pk']:
            continue
            
        try:
            if hasattr(field, 'attname'):
                # For foreign keys, get the ID directly
                value = getattr(instance, field.attname, None)
            else:
                value = getattr(instance, field.name, None)
        except Exception:
            continue
            
        # Convert non-serializable fields to JSON-compatible types
        if value is None:
            data[field.name] = None
        elif isinstance(value, Decimal):
            data[field.name] = str(value)
        elif isinstance(value, UUID):
            data[field.name] = str(value)
        elif isinstance(value, (datetime, date, time)):
            data[field.name] = value.isoformat()
        elif isinstance(value, timedelta):
            data[field.name] = str(value)
        elif isinstance(value, bytes):
            data[field.name] = value.decode('utf-8', errors='replace')
        elif isinstance(value, (str, int, float, bool, list, dict)):
            data[field.name] = value
        else:
            # For any other type, convert to string
            data[field.name] = str(value)
    
    return data


# List of models to audit
AUDITED_MODELS = [
    "academic.semester",
    "academic.subject", 
    "routine.routine",
    "routine.routineentry",
    "attendance.attendancerecord",
]



def should_audit_model(instance):
    """Check if this model should be audited."""
    model_label = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return model_label in AUDITED_MODELS


@receiver(pre_save)
def capture_pre_save_state(sender, instance, **kwargs):
    """Capture the state before save for comparison."""
    if not should_audit_model(instance):
        return
    
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            key = f"{sender._meta.label}_{instance.pk}"
            if not hasattr(_pre_save_state, "states"):
                _pre_save_state.states = {}
            _pre_save_state.states[key] = get_model_fields_for_audit(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def log_save_action(sender, instance, created, **kwargs):
    """Log create or update actions."""
    if not should_audit_model(instance):
        return
    
    user = get_current_user()
    metadata = get_request_metadata()
    
    if created:
        AuditLog.log_action(
            user=user,
            action=ActionType.CREATE,
            obj=instance,
            old_values=None,
            new_values=get_model_fields_for_audit(instance),
            **metadata
        )
    else:
        key = f"{sender._meta.label}_{instance.pk}"
        old_values = getattr(_pre_save_state, "states", {}).get(key)
        
        if old_values:
            new_values = get_model_fields_for_audit(instance)
            
            # Only log if values actually changed
            if old_values != new_values:
                # Check if this is a soft delete
                if old_values.get("is_deleted") == False and new_values.get("is_deleted") == True:
                    action = ActionType.SOFT_DELETE
                elif old_values.get("is_deleted") == True and new_values.get("is_deleted") == False:
                    action = ActionType.RESTORE
                else:
                    action = ActionType.UPDATE
                
                AuditLog.log_action(
                    user=user,
                    action=action,
                    obj=instance,
                    old_values=old_values,
                    new_values=new_values,
                    **metadata
                )
            
            # Clean up
            del _pre_save_state.states[key]


@receiver(post_delete)
def log_delete_action(sender, instance, **kwargs):
    """Log hard delete actions."""
    if not should_audit_model(instance):
        return
    
    user = get_current_user()
    metadata = get_request_metadata()
    
    AuditLog.log_action(
        user=user,
        action=ActionType.DELETE,
        obj=instance,
        old_values=get_model_fields_for_audit(instance),
        new_values=None,
        **metadata
    )
