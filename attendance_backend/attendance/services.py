"""
Service layer for attendance business logic.
Contains class generation, validation, and calculations.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ValidationError

from academic.models import Semester, Subject
from routine.models import Routine, RoutineEntry
from attendance.models import AttendanceRecord, AttendanceStatus, AttendanceType


class ClassGenerationService:
    """
    Service for generating class sessions from routine entries.
    """
    
    @staticmethod
    def generate_classes_for_date(
        routine: Routine,
        target_date: date,
        auto_save: bool = True
    ) -> List[AttendanceRecord]:
        """
        Generate class sessions for a specific date based on routine.
        
        Args:
            routine: The routine to generate classes from
            target_date: The date to generate classes for
            auto_save: Whether to save the records immediately
            
        Returns:
            List of generated AttendanceRecord instances
        """
        day_of_week = target_date.weekday()
        entries = routine.entries.filter(day_of_week=day_of_week)
        
        generated_classes = []
        
        for entry in entries:
            # Check if attendance already exists for this slot
            existing = AttendanceRecord.objects.filter(
                subject=entry.subject,
                date=target_date,
                start_time=entry.start_time
            ).exists()
            
            if not existing:
                record = AttendanceRecord(
                    subject=entry.subject,
                    routine_entry=entry,
                    date=target_date,
                    status=AttendanceStatus.ABSENT,  # Default status
                    attendance_type=AttendanceType.ROUTINE,
                    start_time=entry.start_time,
                    end_time=entry.end_time,
                    duration_minutes=entry.duration_minutes
                )
                
                if auto_save:
                    record.save()
                
                generated_classes.append(record)
        
        return generated_classes
    
    @staticmethod
    def generate_classes_for_date_range(
        routine: Routine,
        start_date: date,
        end_date: date,
        skip_existing: bool = True
    ) -> List[AttendanceRecord]:
        """
        Generate class sessions for a date range.
        
        Args:
            routine: The routine to generate classes from
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            skip_existing: Whether to skip dates with existing records
            
        Returns:
            List of all generated AttendanceRecord instances
        """
        all_generated = []
        current_date = start_date
        
        while current_date <= end_date:
            generated = ClassGenerationService.generate_classes_for_date(
                routine, current_date, auto_save=True
            )
            all_generated.extend(generated)
            current_date += timedelta(days=1)
        
        return all_generated
    
    @staticmethod
    def generate_daily_classes(semester: Semester) -> List[AttendanceRecord]:
        """
        Generate classes for today based on semester's routine.
        
        Args:
            semester: The semester to generate classes for
            
        Returns:
            List of generated AttendanceRecord instances
        """
        try:
            routine = semester.routine
        except Routine.DoesNotExist:
            return []
        
        today = date.today()
        
        # Only generate if within semester date range
        if semester.start_date <= today <= semester.end_date:
            return ClassGenerationService.generate_classes_for_date(routine, today)
        
        return []


class AttendanceValidationService:
    """
    Service for validating attendance records.
    """
    
    @staticmethod
    def check_duplicate(
        subject: Subject,
        target_date: date,
        start_time: Optional[datetime] = None,
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Check if a duplicate attendance record exists.
        
        Args:
            subject: The subject
            target_date: The date
            start_time: Optional start time
            exclude_id: ID to exclude from check
            
        Returns:
            True if duplicate exists, False otherwise
        """
        query = AttendanceRecord.objects.filter(
            subject=subject,
            date=target_date
        )
        
        if start_time:
            query = query.filter(start_time=start_time)
        
        if exclude_id:
            query = query.exclude(pk=exclude_id)
        
        return query.exists()
    
    @staticmethod
    def validate_date_in_semester(
        subject: Subject,
        target_date: date
    ) -> Tuple[bool, str]:
        """
        Validate that the date falls within the semester period.
        
        Args:
            subject: The subject
            target_date: The date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        semester = subject.semester
        
        if target_date < semester.start_date:
            return False, f"Date is before semester start ({semester.start_date})"
        
        if target_date > semester.end_date:
            return False, f"Date is after semester end ({semester.end_date})"
        
        return True, ""


class AdHocClassService:
    """
    Service for managing ad-hoc (extra) classes.
    """
    
    @staticmethod
    @transaction.atomic
    def create_adhoc_class(
        subject: Subject,
        target_date: date,
        start_time: datetime,
        end_time: datetime,
        status: str = AttendanceStatus.ABSENT,
        notes: str = ""
    ) -> AttendanceRecord:
        """
        Create an ad-hoc (extra) class.
        
        Args:
            subject: The subject
            target_date: The date
            start_time: Start time
            end_time: End time
            status: Attendance status
            notes: Optional notes
            
        Returns:
            Created AttendanceRecord
            
        Raises:
            ValidationError: If duplicate exists
        """
        # Check for duplicates
        if AttendanceValidationService.check_duplicate(subject, target_date, start_time):
            raise ValidationError(
                f"An attendance record already exists for {subject.name} "
                f"on {target_date} at {start_time}"
            )
        
        # Validate date is in semester
        is_valid, error_msg = AttendanceValidationService.validate_date_in_semester(
            subject, target_date
        )
        if not is_valid:
            raise ValidationError(error_msg)
        
        record = AttendanceRecord.objects.create(
            subject=subject,
            date=target_date,
            status=status,
            attendance_type=AttendanceType.ADHOC,
            start_time=start_time,
            end_time=end_time,
            notes=notes
        )
        
        return record


class BulkAttendanceService:
    """
    Service for bulk attendance operations.
    """
    
    @staticmethod
    @transaction.atomic
    def mark_attendance_bulk(
        records: List[int],
        status: str
    ) -> int:
        """
        Mark multiple attendance records with the same status.
        
        Args:
            records: List of AttendanceRecord IDs
            status: The status to set
            
        Returns:
            Number of records updated
        """
        if status not in AttendanceStatus.values:
            raise ValidationError(f"Invalid status: {status}")
        
        return AttendanceRecord.objects.filter(pk__in=records).update(status=status)
    
    @staticmethod
    @transaction.atomic
    def mark_day_attendance(
        semester: Semester,
        target_date: date,
        status: str
    ) -> int:
        """
        Mark all classes for a specific day with the same status.
        
        Args:
            semester: The semester
            target_date: The date
            status: The status to set
            
        Returns:
            Number of records updated
        """
        subject_ids = semester.subjects.values_list("id", flat=True)
        
        return AttendanceRecord.objects.filter(
            subject_id__in=subject_ids,
            date=target_date
        ).update(status=status)
    
    @staticmethod
    @transaction.atomic
    def mark_as_holiday(
        semester: Semester,
        target_date: date
    ) -> int:
        """
        Mark all classes for a day as holiday (cancelled).
        
        Args:
            semester: The semester
            target_date: The date
            
        Returns:
            Number of records updated
        """
        subject_ids = semester.subjects.values_list("id", flat=True)
        
        return AttendanceRecord.objects.filter(
            subject_id__in=subject_ids,
            date=target_date
        ).update(
            status=AttendanceStatus.CANCELLED,
            is_holiday=True
        )
