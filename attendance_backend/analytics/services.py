"""
Analytics service for calculating attendance metrics and insights.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db.models import Count, Q, F
from django.db.models.functions import TruncWeek, TruncMonth

from academic.models import Semester, Subject
from attendance.models import AttendanceRecord, AttendanceStatus


@dataclass
class SubjectAnalytics:
    """Data class for subject-level analytics."""
    subject_id: int
    subject_name: str
    subject_code: Optional[str]
    total_conducted: int
    total_attended: int
    total_absent: int
    total_cancelled: int
    attendance_percentage: Decimal
    min_required_percentage: Decimal
    status: str  # 'safe', 'borderline', 'shortage'
    classes_can_miss: int
    classes_need_to_attend: int


@dataclass
class SemesterAnalytics:
    """Data class for semester-level analytics."""
    semester_id: int
    semester_name: str
    total_subjects: int
    overall_attendance: Decimal
    subjects_in_shortage: int
    subjects_borderline: int
    subjects_safe: int


class AttendanceAnalyticsService:
    """
    Service for calculating attendance analytics.
    Calculates from semester start date to today.
    Unmarked classes are considered absent.
    """
    
    BORDERLINE_THRESHOLD = 5  # Within 5% of minimum
    
    @classmethod
    def _count_expected_classes(cls, subject: Subject) -> int:
        """
        Count how many classes should have happened from semester start to today.
        Based on routine entries for this subject.
        
        Args:
            subject: The subject to analyze
            
        Returns:
            Number of expected classes
        """
        semester = subject.semester
        today = date.today()
        
        # Use the earlier of today or semester end date
        end_date = min(today, semester.end_date)
        start_date = semester.start_date
        
        if start_date > end_date:
            return 0
        
        try:
            routine = semester.routine
        except:
            return 0
        
        # Get routine entries for this subject
        routine_entries = routine.entries.filter(subject=subject)
        
        if not routine_entries.exists():
            return 0
        
        # Count by day of week
        entries_by_day = {}
        for entry in routine_entries:
            day = entry.day_of_week
            if day not in entries_by_day:
                entries_by_day[day] = 0
            entries_by_day[day] += 1
        
        # Count how many times each day of week occurs from start to end
        expected_classes = 0
        current_date = start_date
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            if day_of_week in entries_by_day:
                expected_classes += entries_by_day[day_of_week]
            current_date += timedelta(days=1)
        
        return expected_classes
    
    @classmethod
    def get_subject_analytics(cls, subject: Subject) -> SubjectAnalytics:
        """
        Calculate comprehensive analytics for a subject.
        Uses all classes from semester start to today.
        Unmarked classes count as absent.
        
        Args:
            subject: The subject to analyze
            
        Returns:
            SubjectAnalytics dataclass with all metrics
        """
        semester = subject.semester
        today = date.today()
        end_date = min(today, semester.end_date)
        
        # Get attendance records within the date range
        records = AttendanceRecord.objects.filter(
            subject=subject,
            date__gte=semester.start_date,
            date__lte=end_date
        )
        
        # Count by status from existing records
        marked_present = records.filter(status=AttendanceStatus.PRESENT).count()
        marked_absent = records.filter(status=AttendanceStatus.ABSENT).count()
        marked_cancelled = records.filter(status=AttendanceStatus.CANCELLED).count()
        
        # Count expected classes based on routine
        expected_classes = cls._count_expected_classes(subject)
        
        # Total marked classes
        total_marked = marked_present + marked_absent + marked_cancelled
        
        # Unmarked classes (expected but not recorded) are considered absent
        unmarked_classes = max(0, expected_classes - total_marked)
        
        # Total absent = marked absent + unmarked classes
        total_absent = marked_absent + unmarked_classes
        
        # Total conducted = expected classes - cancelled
        # (classes that were supposed to happen and weren't cancelled)
        total_conducted = expected_classes - marked_cancelled
        
        # Total attended = marked present
        total_attended = marked_present
        
        # Calculate percentage
        if total_conducted > 0:
            attendance_percentage = Decimal(total_attended * 100 / total_conducted).quantize(Decimal("0.01"))
        else:
            attendance_percentage = Decimal("100.00")  # No classes = 100%
        
        min_required = subject.min_attendance_percentage
        
        # Determine status
        if attendance_percentage >= min_required:
            if attendance_percentage - min_required <= cls.BORDERLINE_THRESHOLD:
                status = "borderline"
            else:
                status = "safe"
        else:
            status = "shortage"
        
        # Calculate classes can miss while staying above minimum
        classes_can_miss = cls._calculate_classes_can_miss(
            total_attended, total_conducted, min_required
        )
        
        # Calculate classes needed to reach minimum
        classes_need = cls._calculate_classes_needed(
            total_attended, total_conducted, min_required
        )
        
        return SubjectAnalytics(
            subject_id=subject.id,
            subject_name=subject.name,
            subject_code=subject.code,
            total_conducted=total_conducted,
            total_attended=total_attended,
            total_absent=total_absent,
            total_cancelled=marked_cancelled,
            attendance_percentage=attendance_percentage,
            min_required_percentage=min_required,
            status=status,
            classes_can_miss=classes_can_miss,
            classes_need_to_attend=classes_need
        )
    
    @staticmethod
    def _calculate_classes_can_miss(
        present: int,
        total: int,
        min_percentage: Decimal
    ) -> int:
        """
        Calculate maximum classes that can be missed while staying above minimum.
        
        Formula: Find n where (present / (total + n)) * 100 >= min_percentage
        Rearranged: n <= (present * 100 / min_percentage) - total
        """
        if min_percentage <= 0:
            return 999  # Effectively unlimited
        
        min_ratio = float(min_percentage) / 100
        
        if min_ratio >= 1:
            return 0
        
        # Calculate how many more classes can be missed
        # present / (total + n) >= min_ratio
        # present >= min_ratio * (total + n)
        # present >= min_ratio * total + min_ratio * n
        # present - min_ratio * total >= min_ratio * n
        # n <= (present - min_ratio * total) / min_ratio
        
        max_additional = (present - min_ratio * total) / min_ratio
        
        return max(0, int(max_additional))
    
    @staticmethod
    def _calculate_classes_needed(
        present: int,
        total: int,
        min_percentage: Decimal
    ) -> int:
        """
        Calculate classes needed to attend to reach minimum percentage.
        
        Formula: Find n where ((present + n) / (total + n)) * 100 >= min_percentage
        """
        if total == 0:
            return 0
        
        current_percentage = Decimal(present * 100 / total)
        
        if current_percentage >= min_percentage:
            return 0
        
        min_ratio = float(min_percentage) / 100
        
        # (present + n) / (total + n) >= min_ratio
        # present + n >= min_ratio * (total + n)
        # present + n >= min_ratio * total + min_ratio * n
        # n - min_ratio * n >= min_ratio * total - present
        # n * (1 - min_ratio) >= min_ratio * total - present
        # n >= (min_ratio * total - present) / (1 - min_ratio)
        
        if min_ratio >= 1:
            return 999  # Impossible to reach 100%+
        
        needed = (min_ratio * total - present) / (1 - min_ratio)
        
        return max(0, int(needed) + 1)  # Round up
    
    @classmethod
    def get_semester_analytics(cls, semester: Semester) -> Dict[str, Any]:
        """
        Calculate comprehensive analytics for a semester.
        
        Args:
            semester: The semester to analyze
            
        Returns:
            Dictionary with semester overview and subject analytics
        """
        subjects = semester.subjects.all()
        subject_analytics = [cls.get_subject_analytics(s) for s in subjects]
        
        # Calculate overall statistics
        total_conducted = sum(s.total_conducted for s in subject_analytics)
        total_attended = sum(s.total_attended for s in subject_analytics)
        
        if total_conducted > 0:
            overall_percentage = Decimal(total_attended * 100 / total_conducted).quantize(Decimal("0.01"))
        else:
            overall_percentage = Decimal("100.00")  # No classes yet = 100%
        
        subjects_safe = len([s for s in subject_analytics if s.status == "safe"])
        subjects_borderline = len([s for s in subject_analytics if s.status == "borderline"])
        subjects_shortage = len([s for s in subject_analytics if s.status == "shortage"])
        
        return {
            "semester": {
                "id": semester.id,
                "name": semester.name,
                "start_date": semester.start_date.isoformat(),
                "end_date": semester.end_date.isoformat(),
            },
            "overview": {
                "total_subjects": len(subjects),
                "overall_attendance": str(overall_percentage),
                "subjects_safe": subjects_safe,
                "subjects_borderline": subjects_borderline,
                "subjects_shortage": subjects_shortage,
            },
            "subjects": [
                {
                    "subject_id": s.subject_id,
                    "subject_name": s.subject_name,
                    "subject_code": s.subject_code,
                    "total_conducted": s.total_conducted,
                    "total_attended": s.total_attended,
                    "total_absent": s.total_absent,
                    "total_cancelled": s.total_cancelled,
                    "attendance_percentage": str(s.attendance_percentage),
                    "min_required_percentage": str(s.min_required_percentage),
                    "status": s.status,
                    "classes_can_miss": s.classes_can_miss,
                    "classes_need_to_attend": s.classes_need_to_attend,
                }
                for s in subject_analytics
            ]
        }
    
    @classmethod
    def get_weekly_trends(
        cls,
        subject: Subject,
        weeks: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get weekly attendance trends for a subject.
        
        Args:
            subject: The subject to analyze
            weeks: Number of weeks to include
            
        Returns:
            List of weekly attendance data
        """
        end_date = date.today()
        start_date = end_date - timedelta(weeks=weeks)
        
        records = AttendanceRecord.objects.filter(
            subject=subject,
            date__gte=start_date,
            date__lte=end_date
        ).annotate(
            week=TruncWeek("date")
        ).values("week").annotate(
            present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
            cancelled=Count("id", filter=Q(status=AttendanceStatus.CANCELLED)),
        ).order_by("week")
        
        trends = []
        for record in records:
            conducted = record["present"] + record["absent"]
            percentage = (record["present"] * 100 / conducted) if conducted > 0 else 0
            
            trends.append({
                "week_start": record["week"].isoformat(),
                "present": record["present"],
                "absent": record["absent"],
                "cancelled": record["cancelled"],
                "conducted": conducted,
                "percentage": round(percentage, 2)
            })
        
        return trends
    
    @classmethod
    def get_monthly_trends(
        cls,
        subject: Subject,
        months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Get monthly attendance trends for a subject.
        
        Args:
            subject: The subject to analyze
            months: Number of months to include
            
        Returns:
            List of monthly attendance data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        records = AttendanceRecord.objects.filter(
            subject=subject,
            date__gte=start_date,
            date__lte=end_date
        ).annotate(
            month=TruncMonth("date")
        ).values("month").annotate(
            present=Count("id", filter=Q(status=AttendanceStatus.PRESENT)),
            absent=Count("id", filter=Q(status=AttendanceStatus.ABSENT)),
            cancelled=Count("id", filter=Q(status=AttendanceStatus.CANCELLED)),
        ).order_by("month")
        
        trends = []
        for record in records:
            conducted = record["present"] + record["absent"]
            percentage = (record["present"] * 100 / conducted) if conducted > 0 else 0
            
            trends.append({
                "month": record["month"].strftime("%B %Y"),
                "present": record["present"],
                "absent": record["absent"],
                "cancelled": record["cancelled"],
                "conducted": conducted,
                "percentage": round(percentage, 2)
            })
        
        return trends
    
    @classmethod
    def get_attendance_history(
        cls,
        subject: Subject,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get detailed attendance history timeline for a subject.
        
        Args:
            subject: The subject to analyze
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            List of attendance records with details
        """
        records = AttendanceRecord.objects.filter(subject=subject)
        
        if start_date:
            records = records.filter(date__gte=start_date)
        if end_date:
            records = records.filter(date__lte=end_date)
        
        return [
            {
                "id": r.id,
                "date": r.date.isoformat(),
                "status": r.status,
                "type": r.attendance_type,
                "start_time": r.start_time.isoformat() if r.start_time else None,
                "end_time": r.end_time.isoformat() if r.end_time else None,
                "duration_minutes": r.duration_minutes,
                "notes": r.notes,
                "is_holiday": r.is_holiday,
            }
            for r in records.order_by("-date", "-start_time")
        ]


class AlertService:
    """
    Service for generating attendance alerts and warnings.
    """
    
    @classmethod
    def get_alerts(cls, semester: Semester) -> List[Dict[str, Any]]:
        """
        Generate alerts for subjects with attendance issues.
        
        Args:
            semester: The semester to check
            
        Returns:
            List of alert dictionaries
        """
        alerts = []
        subjects = semester.subjects.all()
        
        for subject in subjects:
            analytics = AttendanceAnalyticsService.get_subject_analytics(subject)
            
            if analytics.status == "shortage":
                alerts.append({
                    "type": "shortage",
                    "severity": "high",
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                    "message": f"Attendance shortage! Current: {analytics.attendance_percentage}%, "
                              f"Required: {analytics.min_required_percentage}%",
                    "current_percentage": str(analytics.attendance_percentage),
                    "required_percentage": str(analytics.min_required_percentage),
                    "classes_needed": analytics.classes_need_to_attend,
                })
            elif analytics.status == "borderline":
                alerts.append({
                    "type": "borderline",
                    "severity": "medium",
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                    "message": f"Near minimum! Current: {analytics.attendance_percentage}%, "
                              f"Required: {analytics.min_required_percentage}%",
                    "current_percentage": str(analytics.attendance_percentage),
                    "required_percentage": str(analytics.min_required_percentage),
                    "classes_can_miss": analytics.classes_can_miss,
                })
        
        # Sort by severity (high first)
        severity_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return alerts
