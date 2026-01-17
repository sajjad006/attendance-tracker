from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .services import AttendanceAnalyticsService, AlertService
from academic.models import Semester, Subject


class SemesterAnalyticsView(APIView):
    """
    Get comprehensive analytics for a semester.
    
    GET /analytics/semester/{semester_id}/
    """
    
    def get(self, request, semester_id):
        try:
            semester = Semester.objects.get(pk=semester_id, user=request.user)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        analytics = AttendanceAnalyticsService.get_semester_analytics(semester)
        return Response(analytics)


class SubjectAnalyticsView(APIView):
    """
    Get comprehensive analytics for a subject.
    
    GET /analytics/subject/{subject_id}/
    """
    
    def get(self, request, subject_id):
        try:
            subject = Subject.objects.get(pk=subject_id, semester__user=request.user)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
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


class WeeklyTrendsView(APIView):
    """
    Get weekly attendance trends for a subject.
    
    GET /analytics/subject/{subject_id}/weekly/?weeks=8
    """
    
    def get(self, request, subject_id):
        try:
            subject = Subject.objects.get(pk=subject_id, semester__user=request.user)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        weeks = int(request.query_params.get("weeks", 8))
        trends = AttendanceAnalyticsService.get_weekly_trends(subject, weeks)
        
        return Response({
            "subject_id": subject_id,
            "subject_name": subject.name,
            "weeks_count": weeks,
            "trends": trends,
        })


class MonthlyTrendsView(APIView):
    """
    Get monthly attendance trends for a subject.
    
    GET /analytics/subject/{subject_id}/monthly/?months=6
    """
    
    def get(self, request, subject_id):
        try:
            subject = Subject.objects.get(pk=subject_id, semester__user=request.user)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        months = int(request.query_params.get("months", 6))
        trends = AttendanceAnalyticsService.get_monthly_trends(subject, months)
        
        return Response({
            "subject_id": subject_id,
            "subject_name": subject.name,
            "months_count": months,
            "trends": trends,
        })


class AttendanceHistoryView(APIView):
    """
    Get attendance history timeline for a subject.
    
    GET /analytics/subject/{subject_id}/history/?start_date=&end_date=
    """
    
    def get(self, request, subject_id):
        try:
            subject = Subject.objects.get(pk=subject_id, semester__user=request.user)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from datetime import datetime
        
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        history = AttendanceAnalyticsService.get_attendance_history(
            subject, start_date, end_date
        )
        
        return Response({
            "subject_id": subject_id,
            "subject_name": subject.name,
            "count": len(history),
            "history": history,
        })


class AlertsView(APIView):
    """
    Get attendance alerts for a semester.
    
    GET /analytics/semester/{semester_id}/alerts/
    """
    
    def get(self, request, semester_id):
        try:
            semester = Semester.objects.get(pk=semester_id, user=request.user)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        alerts = AlertService.get_alerts(semester)
        
        return Response({
            "semester_id": semester_id,
            "semester_name": semester.name,
            "alert_count": len(alerts),
            "alerts": alerts,
        })


class DashboardView(APIView):
    """
    Get dashboard data for current semester.
    
    GET /analytics/dashboard/
    GET /analytics/dashboard/?semester_id=1
    """
    
    def get(self, request):
        semester_id = request.query_params.get("semester_id")
        
        if semester_id:
            try:
                semester = Semester.objects.get(pk=semester_id, user=request.user)
            except Semester.DoesNotExist:
                return Response(
                    {"error": "Semester not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get current semester
            try:
                semester = Semester.objects.get(user=request.user, is_current=True)
            except Semester.DoesNotExist:
                # Get most recent semester
                semester = Semester.objects.filter(user=request.user).first()
                
                if not semester:
                    return Response({
                        "message": "No semesters found. Please create a semester first.",
                        "has_data": False,
                    })
        
        # Get analytics and alerts
        analytics = AttendanceAnalyticsService.get_semester_analytics(semester)
        alerts = AlertService.get_alerts(semester)
        
        # Get today's attendance
        from datetime import date
        from attendance.models import AttendanceRecord
        
        today = date.today()
        today_records = AttendanceRecord.objects.filter(
            subject__semester=semester,
            date=today
        ).select_related("subject")
        
        today_attendance = [
            {
                "id": r.id,
                "subject_name": r.subject.name,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "status": r.status,
            }
            for r in today_records
        ]
        
        return Response({
            "has_data": True,
            "semester": analytics["semester"],
            "overview": analytics["overview"],
            "subjects": analytics["subjects"],
            "alerts": alerts[:5],  # Top 5 alerts
            "today": {
                "date": today.isoformat(),
                "classes": today_attendance,
                "count": len(today_attendance),
            },
        })
