from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction

from .models import Routine, RoutineEntry
from .serializers import (
    RoutineSerializer,
    RoutineCreateSerializer,
    RoutineEntrySerializer,
    RoutineEntryCreateSerializer,
    BulkRoutineEntrySerializer,
)
from attendance.services import ClassGenerationService


class RoutineViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing routines.
    
    Endpoints:
    - GET /routines/ - List all routines
    - POST /routines/ - Create a new routine
    - GET /routines/{id}/ - Get routine details
    - PUT/PATCH /routines/{id}/ - Update routine
    - DELETE /routines/{id}/ - Soft delete routine
    - POST /routines/{id}/generate_classes/ - Generate classes from routine
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ["name"]
    filterset_fields = ["semester", "is_active"]
    
    def get_queryset(self):
        return Routine.objects.filter(semester__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return RoutineCreateSerializer
        return RoutineSerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()
    
    @action(detail=True, methods=["post"])
    def generate_classes(self, request, pk=None):
        """Generate class sessions from this routine."""
        routine = self.get_object()
        
        from datetime import date, datetime
        
        start_date_str = request.data.get("start_date")
        end_date_str = request.data.get("end_date")
        
        if not start_date_str or not end_date_str:
            return Response(
                {"error": "start_date and end_date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start_date > end_date:
            return Response(
                {"error": "start_date must be before end_date."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Limit range
        max_days = 90
        if (end_date - start_date).days > max_days:
            return Response(
                {"error": f"Date range cannot exceed {max_days} days."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        generated = ClassGenerationService.generate_classes_for_date_range(
            routine, start_date, end_date
        )
        
        return Response({
            "message": f"Generated {len(generated)} class sessions.",
            "count": len(generated),
            "start_date": start_date_str,
            "end_date": end_date_str,
        })
    
    @action(detail=True, methods=["post"])
    def generate_today(self, request, pk=None):
        """Generate class sessions for today."""
        routine = self.get_object()
        
        from datetime import date
        today = date.today()
        
        generated = ClassGenerationService.generate_classes_for_date(routine, today)
        
        return Response({
            "message": f"Generated {len(generated)} class sessions for today.",
            "count": len(generated),
            "date": today.isoformat(),
        })


class RoutineEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing routine entries.
    
    Endpoints:
    - GET /routine-entries/ - List all entries
    - POST /routine-entries/ - Create a new entry
    - GET /routine-entries/{id}/ - Get entry details
    - PUT/PATCH /routine-entries/{id}/ - Update entry
    - DELETE /routine-entries/{id}/ - Soft delete entry
    - POST /routine-entries/bulk_create/ - Create multiple entries
    """
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ["day_of_week", "start_time"]
    ordering = ["day_of_week", "start_time"]
    filterset_fields = ["routine", "subject", "day_of_week"]
    
    def get_queryset(self):
        return RoutineEntry.objects.filter(routine__semester__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return RoutineEntryCreateSerializer
        return RoutineEntrySerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()
    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_create(self, request):
        """Create multiple routine entries at once."""
        serializer = BulkRoutineEntrySerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        
        created = []
        for entry_data in serializer.validated_data["entries"]:
            entry_serializer = RoutineEntryCreateSerializer(
                data=entry_data,
                context={"request": request}
            )
            entry_serializer.is_valid(raise_exception=True)
            entry = entry_serializer.save()
            created.append(entry)
        
        return Response({
            "message": f"Created {len(created)} routine entries.",
            "entries": RoutineEntrySerializer(created, many=True).data
        }, status=status.HTTP_201_CREATED)
