from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "action", "content_type", "object_id", "object_repr"]
    list_filter = ["action", "content_type", "timestamp"]
    search_fields = ["object_repr", "user__username"]
    ordering = ["-timestamp"]
    date_hierarchy = "timestamp"
    
    readonly_fields = [
        "user", "action", "content_type", "object_id", "object_repr",
        "old_values", "new_values", "ip_address", "user_agent", "timestamp"
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
