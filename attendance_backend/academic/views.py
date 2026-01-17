from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Semester, Subject
from .serializers import (
    SemesterSerializer,
    SemesterCreateSerializer,
    SemesterListSerializer,
    SubjectSerializer,
    SubjectCreateSerializer,
)
from analytics.services import AttendanceAnalyticsService


class SemesterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing semesters.
    
    Endpoints:
    - GET /semesters/ - List all semesters
    - POST /semesters/ - Create a new semester
    - GET /semesters/{id}/ - Get semester details
    - PUT/PATCH /semesters/{id}/ - Update semester
    - DELETE /semesters/{id}/ - Soft delete semester
    - POST /semesters/{id}/set_current/ - Set as current semester
    - GET /semesters/current/ - Get current semester
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["start_date", "end_date", "name", "created_at"]
    ordering = ["-start_date"]
    filterset_fields = ["status", "is_current"]
    
    def get_queryset(self):
        return Semester.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return SemesterCreateSerializer
        if self.action == "list":
            return SemesterListSerializer
        return SemesterSerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()
    
    @action(detail=True, methods=["post"])
    def set_current(self, request, pk=None):
        """Set this semester as the current semester."""
        semester = self.get_object()
        
        # Unset other current semesters
        Semester.objects.filter(user=request.user, is_current=True).update(is_current=False)
        
        semester.is_current = True
        semester.save()
        
        return Response({
            "message": f"'{semester.name}' is now the current semester.",
            "semester": SemesterSerializer(semester).data
        })
    
    @action(detail=False, methods=["get"])
    def current(self, request):
        """Get the current semester."""
        try:
            semester = Semester.objects.get(user=request.user, is_current=True)
            return Response(SemesterSerializer(semester).data)
        except Semester.DoesNotExist:
            return Response(
                {"message": "No current semester set."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        """Get analytics for this semester."""
        semester = self.get_object()
        analytics = AttendanceAnalyticsService.get_semester_analytics(semester)
        return Response(analytics)


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subjects.
    
    Endpoints:
    - GET /subjects/ - List all subjects (can filter by semester)
    - POST /subjects/ - Create a new subject
    - GET /subjects/{id}/ - Get subject details
    - PUT/PATCH /subjects/{id}/ - Update subject
    - DELETE /subjects/{id}/ - Soft delete subject
    - GET /subjects/{id}/analytics/ - Get subject analytics
    """
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "credit", "created_at"]
    ordering = ["name"]
    filterset_fields = ["semester"]
    
    def get_queryset(self):
        return Subject.objects.filter(semester__user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == "create":
            return SubjectCreateSerializer
        return SubjectSerializer
    
    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.soft_delete()
    
    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        """Get analytics for this subject."""
        subject = self.get_object()
        analytics = AttendanceAnalyticsService.get_subject_analytics(subject)
        
        return Response({
            "subject_id": analytics.subject_id,
            "subject_name": analytics.subject_name,
            "subject_code": analytics.subject_code,
            "total_conducted": analytics.total_conducted,
            "total_attended": analytics.total_attended,
            "total_absent": analytics.total_absent,
            "total_cancelled": analytics.total_cancelled,
            "attendance_percentage": str(analytics.attendance_percentage),
            "min_required_percentage": str(analytics.min_required_percentage),
            "status": analytics.status,
            "classes_can_miss": analytics.classes_can_miss,
            "classes_need_to_attend": analytics.classes_need_to_attend,
        })
    
    @action(detail=True, methods=["get"])
    def weekly_trends(self, request, pk=None):
        """Get weekly attendance trends for this subject."""
        subject = self.get_object()
        weeks = int(request.query_params.get("weeks", 8))
        trends = AttendanceAnalyticsService.get_weekly_trends(subject, weeks)
        return Response(trends)
    
    @action(detail=True, methods=["get"])
    def monthly_trends(self, request, pk=None):
        """Get monthly attendance trends for this subject."""
        subject = self.get_object()
        months = int(request.query_params.get("months", 6))
        trends = AttendanceAnalyticsService.get_monthly_trends(subject, months)
        return Response(trends)
