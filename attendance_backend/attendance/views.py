from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from datetime import datetime

from .models import AttendanceRecord, AttendanceStatus, AttendanceType
from .serializers import (
    AttendanceRecordSerializer,
    AttendanceRecordCreateSerializer,
    AttendanceUpdateSerializer,
    BulkAttendanceSerializer,
    MarkDayAttendanceSerializer,
    AdHocClassSerializer,
    GenerateClassesSerializer,
)
from .services import (
    ClassGenerationService,
    AdHocClassService,
    BulkAttendanceService,
)
from academic.models import Semester, Subject


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    
    Endpoints:
    - GET /attendance/ - List all attendance records
    - POST /attendance/ - Create a new record
    - GET /attendance/{id}/ - Get record details
    - PUT/PATCH /attendance/{id}/ - Update record
    - DELETE /attendance/{id}/ - Soft delete record
    - POST /attendance/bulk_update/ - Update multiple records
    - POST /attendance/mark_day/ - Mark all classes for a day
    - POST /attendance/add_adhoc/ - Add an ad-hoc class
    - GET /attendance/today/ - Get today's attendance
    - GET /attendance/calendar/ - Get calendar view data
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["subject__name", "notes"]
    ordering_fields = ["date", "start_time", "created_at"]
    ordering = ["-date", "-start_time"]
    filterset_fields = {
        "subject": ["exact"],
        "subject__semester": ["exact"],
        "date": ["exact", "gte", "lte"],
        "status": ["exact"],
        "attendance_type": ["exact"],
        "is_holiday": ["exact"],
    }
    
    def get_queryset(self):
        return AttendanceRecord.objects.filter(
            subject__semester__user=self.request.user
        ).select_related("subject", "routine_entry")
    
    def get_serializer_class(self):
        if self.action == "create":
            return AttendanceRecordCreateSerializer
        if self.action in ["update", "partial_update"]:
            return AttendanceUpdateSerializer
        return AttendanceRecordSerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()
    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def bulk_update(self, request):
        """Update multiple attendance records at once."""
        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        record_ids = serializer.validated_data["record_ids"]
        new_status = serializer.validated_data["status"]
        
        # Verify user owns these records
        records = AttendanceRecord.objects.filter(
            pk__in=record_ids,
            subject__semester__user=request.user
        )
        
        if records.count() != len(record_ids):
            return Response(
                {"error": "Some records not found or not accessible."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = records.update(status=new_status)
        
        return Response({
            "message": f"Updated {updated} attendance records.",
            "count": updated,
            "status": new_status,
        })
    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def mark_day(self, request):
        """Mark all classes for a specific day."""
        serializer = MarkDayAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        semester_id = serializer.validated_data["semester_id"]
        target_date = serializer.validated_data["date"]
        new_status = serializer.validated_data["status"]
        
        try:
            semester = Semester.objects.get(pk=semester_id, user=request.user)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if new_status == AttendanceStatus.CANCELLED:
            updated = BulkAttendanceService.mark_as_holiday(semester, target_date)
        else:
            updated = BulkAttendanceService.mark_day_attendance(semester, target_date, new_status)
        
        return Response({
            "message": f"Updated {updated} attendance records for {target_date}.",
            "count": updated,
            "date": target_date.isoformat(),
            "status": new_status,
        })
    
    @action(detail=False, methods=["post"])
    @transaction.atomic
    def add_adhoc(self, request):
        """Add an ad-hoc (extra) class."""
        serializer = AdHocClassSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        
        subject_id = serializer.validated_data["subject_id"]
        subject = Subject.objects.get(pk=subject_id)
        
        record = AdHocClassService.create_adhoc_class(
            subject=subject,
            target_date=serializer.validated_data["date"],
            start_time=serializer.validated_data["start_time"],
            end_time=serializer.validated_data["end_time"],
            status=serializer.validated_data.get("status", AttendanceStatus.ABSENT),
            notes=serializer.validated_data.get("notes", ""),
        )
        
        return Response(
            AttendanceRecordSerializer(record).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=["get"])
    def today(self, request):
        """Get today's attendance records, auto-generating from routine if needed."""
        from datetime import date
        
        today = date.today()
        semester_id = request.query_params.get("semester_id")
        
        # Auto-generate classes from routine if semester_id is provided
        if semester_id:
            try:
                semester = Semester.objects.get(pk=semester_id, user=request.user)
                # Check if today is within semester date range
                if semester.start_date <= today <= semester.end_date:
                    try:
                        routine = semester.routine
                        # Generate classes for today if none exist
                        ClassGenerationService.generate_classes_for_date(routine, today)
                    except Exception:
                        pass  # No routine exists, that's fine
            except Semester.DoesNotExist:
                pass
        
        queryset = self.get_queryset().filter(date=today)
        
        if semester_id:
            queryset = queryset.filter(subject__semester_id=semester_id)
        
        serializer = AttendanceRecordSerializer(queryset, many=True)
        
        return Response({
            "date": today.isoformat(),
            "count": queryset.count(),
            "records": serializer.data,
        })
    
    @action(detail=False, methods=["get"])
    def calendar(self, request):
        """Get calendar view data for a month."""
        from datetime import date
        from calendar import monthrange
        from django.db.models import Count, Q
        
        year = int(request.query_params.get("year", date.today().year))
        month = int(request.query_params.get("month", date.today().month))
        semester_id = request.query_params.get("semester_id")
        
        _, last_day = monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, last_day)
        
        queryset = self.get_queryset().filter(
            date__gte=start_date,
            date__lte=end_date
        )
        
        if semester_id:
            queryset = queryset.filter(subject__semester_id=semester_id)
        
        # Aggregate by date
        daily_stats = queryset.values("date").annotate(
            total=Count("id"),
            present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
            cancelled=Count("id", filter=Q(status=AttendanceStatus.CANCELLED)),
        ).order_by("date")
        
        # Convert to dictionary keyed by date string
        days_dict = {}
        for stat in daily_stats:
            date_str = stat["date"].isoformat()
            days_dict[date_str] = {
                "total": stat["total"],
                "present": stat["present"],
                "absent": stat["absent"],
                "cancelled": stat["cancelled"],
            }
        
        return Response({
            "year": year,
            "month": month,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days_dict,
        })
    
    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate classes from routine for a date range."""
        serializer = GenerateClassesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        semester_id = serializer.validated_data["semester_id"]
        
        try:
            semester = Semester.objects.get(pk=semester_id, user=request.user)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            routine = semester.routine
        except:
            return Response(
                {"error": "No routine found for this semester."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        generated = ClassGenerationService.generate_classes_for_date_range(
            routine,
            serializer.validated_data["start_date"],
            serializer.validated_data["end_date"],
        )
        
        return Response({
            "message": f"Generated {len(generated)} class sessions.",
            "count": len(generated),
        })
