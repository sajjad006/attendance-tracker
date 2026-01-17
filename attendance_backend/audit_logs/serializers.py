from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model."""
    
    user_username = serializers.CharField(source="user.username", read_only=True)
    content_type_name = serializers.CharField(source="content_type.model", read_only=True)
    changed_fields = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_username", "action", "content_type",
            "content_type_name", "object_id", "object_repr",
            "old_values", "new_values", "changed_fields",
            "ip_address", "timestamp"
        ]
        read_only_fields = fields
    
    def get_changed_fields(self, obj):
        return obj.get_changed_fields()


class AuditLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for audit log lists."""
    
    user_username = serializers.CharField(source="user.username", read_only=True)
    content_type_name = serializers.CharField(source="content_type.model", read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            "id", "user_username", "action", "content_type_name",
            "object_id", "object_repr", "timestamp"
        ]
