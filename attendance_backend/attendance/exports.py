"""
CSV export services for attendance data.
"""
import csv
import io
from datetime import date
from typing import List, Dict, Any

from academic.models import Semester, Subject
from attendance.models import AttendanceRecord, AttendanceStatus
from analytics.services import AttendanceAnalyticsService


class CSVExportService:
    """
    Service for generating CSV exports of attendance data.
    """
    
    @staticmethod
    def export_attendance_records(
        records: List[AttendanceRecord],
        include_headers: bool = True
    ) -> str:
        """
        Export attendance records to CSV format.
        
        Args:
            records: List of AttendanceRecord instances
            include_headers: Whether to include header row
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        if include_headers:
            writer.writerow([
                "Date",
                "Subject",
                "Subject Code",
                "Status",
                "Type",
                "Start Time",
                "End Time",
                "Duration (min)",
                "Notes",
                "Is Holiday",
            ])
        
        for record in records:
            writer.writerow([
                record.date.isoformat(),
                record.subject.name,
                record.subject.code or "",
                record.get_status_display(),
                record.get_attendance_type_display(),
                record.start_time.strftime("%H:%M") if record.start_time else "",
                record.end_time.strftime("%H:%M") if record.end_time else "",
                record.duration_minutes or "",
                record.notes or "",
                "Yes" if record.is_holiday else "No",
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_subject_summary(subjects: List[Subject]) -> str:
        """
        Export subject-wise attendance summary to CSV.
        
        Args:
            subjects: List of Subject instances
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Subject",
            "Code",
            "Credits",
            "Total Conducted",
            "Total Attended",
            "Total Absent",
            "Total Cancelled",
            "Attendance %",
            "Required %",
            "Status",
            "Classes Can Miss",
            "Classes Need to Attend",
        ])
        
        for subject in subjects:
            analytics = AttendanceAnalyticsService.get_subject_analytics(subject)
            
            writer.writerow([
                analytics.subject_name,
                analytics.subject_code or "",
                subject.credit,
                analytics.total_conducted,
                analytics.total_attended,
                analytics.total_absent,
                analytics.total_cancelled,
                f"{analytics.attendance_percentage}%",
                f"{analytics.min_required_percentage}%",
                analytics.status.capitalize(),
                analytics.classes_can_miss,
                analytics.classes_need_to_attend,
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_semester_report(semester: Semester) -> str:
        """
        Export comprehensive semester report to CSV.
        
        Args:
            semester: Semester instance
            
        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Semester info
        writer.writerow(["SEMESTER ATTENDANCE REPORT"])
        writer.writerow([])
        writer.writerow(["Semester", semester.name])
        writer.writerow(["Start Date", semester.start_date.isoformat()])
        writer.writerow(["End Date", semester.end_date.isoformat()])
        writer.writerow(["Status", semester.get_status_display()])
        writer.writerow(["Generated On", date.today().isoformat()])
        writer.writerow([])
        
        # Overall summary
        analytics = AttendanceAnalyticsService.get_semester_analytics(semester)
        
        writer.writerow(["OVERALL SUMMARY"])
        writer.writerow([])
        writer.writerow(["Total Subjects", analytics["overview"]["total_subjects"]])
        writer.writerow(["Overall Attendance", f"{analytics['overview']['overall_attendance']}%"])
        writer.writerow(["Subjects Safe", analytics["overview"]["subjects_safe"]])
        writer.writerow(["Subjects Borderline", analytics["overview"]["subjects_borderline"]])
        writer.writerow(["Subjects in Shortage", analytics["overview"]["subjects_shortage"]])
        writer.writerow([])
        
        # Subject-wise breakdown
        writer.writerow(["SUBJECT-WISE BREAKDOWN"])
        writer.writerow([])
        writer.writerow([
            "Subject",
            "Code",
            "Conducted",
            "Attended",
            "Absent",
            "Cancelled",
            "Attendance %",
            "Required %",
            "Status",
        ])
        
        for subject_data in analytics["subjects"]:
            writer.writerow([
                subject_data["subject_name"],
                subject_data["subject_code"] or "",
                subject_data["total_conducted"],
                subject_data["total_attended"],
                subject_data["total_absent"],
                subject_data["total_cancelled"],
                f"{subject_data['attendance_percentage']}%",
                f"{subject_data['min_required_percentage']}%",
                subject_data["status"].capitalize(),
            ])
        
        writer.writerow([])
        
        # Detailed attendance records
        writer.writerow(["DETAILED ATTENDANCE RECORDS"])
        writer.writerow([])
        writer.writerow([
            "Date",
            "Subject",
            "Status",
            "Type",
            "Start Time",
            "End Time",
        ])
        
        records = AttendanceRecord.objects.filter(
            subject__semester=semester
        ).select_related("subject").order_by("-date", "start_time")
        
        for record in records:
            writer.writerow([
                record.date.isoformat(),
                record.subject.name,
                record.get_status_display(),
                record.get_attendance_type_display(),
                record.start_time.strftime("%H:%M") if record.start_time else "",
                record.end_time.strftime("%H:%M") if record.end_time else "",
            ])
        
        return output.getvalue()
