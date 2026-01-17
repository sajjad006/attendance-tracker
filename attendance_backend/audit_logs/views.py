from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogListSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs (read-only).
    
    Endpoints:
    - GET /audit-logs/ - List all audit logs
    - GET /audit-logs/{id}/ - Get log details
    - GET /audit-logs/my_activity/ - Get user's own activity
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["object_repr", "action"]
    ordering_fields = ["timestamp"]
    ordering = ["-timestamp"]
    filterset_fields = ["action", "content_type"]
    
    def get_queryset(self):
        # Users can only see logs for their own data
        return AuditLog.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "list":
            return AuditLogListSerializer
        return AuditLogSerializer
    
    @action(detail=False, methods=["get"])
    def my_activity(self, request):
        """Get the current user's recent activity."""
        limit = int(request.query_params.get("limit", 50))
        logs = AuditLog.get_user_activity(request.user, limit)
        serializer = AuditLogListSerializer(logs, many=True)
        
        return Response({
            "count": logs.count(),
            "logs": serializer.data,
        })
    
    @action(detail=False, methods=["get"])
    def for_object(self, request):
        """Get audit logs for a specific object."""
        content_type_id = request.query_params.get("content_type")
        object_id = request.query_params.get("object_id")
        
        if not content_type_id or not object_id:
            return Response({
                "error": "content_type and object_id are required."
            }, status=400)
        
        logs = self.get_queryset().filter(
            content_type_id=content_type_id,
            object_id=object_id
        )
        
        serializer = AuditLogSerializer(logs, many=True)
        
        return Response({
            "count": logs.count(),
            "logs": serializer.data,
        })
