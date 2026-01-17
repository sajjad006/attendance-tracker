from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from datetime import datetime

from academic.models import Semester, Subject
from attendance.models import AttendanceRecord
from .exports import CSVExportService


class ExportAttendanceView(APIView):
    """
    Export attendance records to CSV.
    
    GET /api/exports/attendance/?semester_id=1&subject_id=2&start_date=&end_date=
    """
    
    def get(self, request):
        semester_id = request.query_params.get("semester_id")
        subject_id = request.query_params.get("subject_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        
        # Build queryset
        records = AttendanceRecord.objects.filter(
            subject__semester__user=request.user
        ).select_related("subject")
        
        if semester_id:
            records = records.filter(subject__semester_id=semester_id)
        
        if subject_id:
            records = records.filter(subject_id=subject_id)
        
        if start_date:
            records = records.filter(date__gte=datetime.strptime(start_date, "%Y-%m-%d").date())
        
        if end_date:
            records = records.filter(date__lte=datetime.strptime(end_date, "%Y-%m-%d").date())
        
        records = records.order_by("-date", "start_time")
        
        if not records.exists():
            return Response(
                {"error": "No records found matching the criteria."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        csv_content = CSVExportService.export_attendance_records(list(records))
        
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="attendance_records.csv"'
        
        return response


class ExportSubjectSummaryView(APIView):
    """
    Export subject-wise attendance summary to CSV.
    
    GET /api/exports/subjects/?semester_id=1
    """
    
    def get(self, request):
        semester_id = request.query_params.get("semester_id")
        
        subjects = Subject.objects.filter(semester__user=request.user)
        
        if semester_id:
            subjects = subjects.filter(semester_id=semester_id)
        
        if not subjects.exists():
            return Response(
                {"error": "No subjects found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        csv_content = CSVExportService.export_subject_summary(list(subjects))
        
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="subject_summary.csv"'
        
        return response


class ExportSemesterReportView(APIView):
    """
    Export comprehensive semester report to CSV.
    
    GET /api/exports/semester/{semester_id}/
    """
    
    def get(self, request, semester_id):
        try:
            semester = Semester.objects.get(pk=semester_id, user=request.user)
        except Semester.DoesNotExist:
            return Response(
                {"error": "Semester not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        csv_content = CSVExportService.export_semester_report(semester)
        
        filename = f"semester_report_{semester.name.replace(' ', '_')}.csv"
        
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        
        return response
