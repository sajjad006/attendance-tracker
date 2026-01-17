from django.db import models
from django.core.exceptions import ValidationError
from academic.models import Subject, SoftDeleteModel, SoftDeleteManager
from routine.models import RoutineEntry


class AttendanceStatus(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    CANCELLED = "cancelled", "Cancelled"


class AttendanceType(models.TextChoices):
    ROUTINE = "routine", "Routine-generated"
    ADHOC = "adhoc", "Ad-hoc (Extra class)"


class AttendanceRecordManager(SoftDeleteManager):
    """Custom manager for AttendanceRecord with common queries."""
    
    def for_subject(self, subject):
        return self.get_queryset().filter(subject=subject)
    
    def for_date_range(self, start_date, end_date):
        return self.get_queryset().filter(date__gte=start_date, date__lte=end_date)
    
    def effective(self):
        """Returns records that affect attendance percentage (excludes cancelled)."""
        return self.get_queryset().exclude(status=AttendanceStatus.CANCELLED)
    
    def present(self):
        return self.get_queryset().filter(status=AttendanceStatus.PRESENT)
    
    def absent(self):
        return self.get_queryset().filter(status=AttendanceStatus.ABSENT)


class AttendanceRecord(SoftDeleteModel):
    """
    Represents a single attendance record for a class session.
    Can be routine-generated or ad-hoc (extra class).
    """
    
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )
    routine_entry = models.ForeignKey(
        RoutineEntry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_records",
        help_text="Reference to routine entry if generated from routine"
    )
    date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT
    )
    attendance_type = models.CharField(
        max_length=20,
        choices=AttendanceType.choices,
        default=AttendanceType.ROUTINE
    )
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in minutes (for ad-hoc classes)"
    )
    notes = models.TextField(blank=True, null=True)
    is_holiday = models.BooleanField(
        default=False,
        help_text="Mark if this is a holiday (manually marked)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = AttendanceRecordManager()
    all_objects = models.Manager()
    
    class Meta:
        db_table = "attendance_record"
        ordering = ["-date", "start_time"]
        # Prevent duplicate attendance records for same subject, date, and time
        constraints = [
            models.UniqueConstraint(
                fields=["subject", "date", "start_time"],
                condition=models.Q(is_deleted=False),
                name="unique_attendance_record"
            )
        ]
    
    def __str__(self):
        return f"{self.subject.name} - {self.date} ({self.get_status_display()})"
    
    def clean(self):
        """Validate attendance record."""
        super().clean()
        
        # Ensure subject belongs to the correct semester if routine_entry is provided
        if self.routine_entry:
            if self.routine_entry.subject != self.subject:
                raise ValidationError({
                    "subject": "Subject must match the routine entry's subject."
                })
        
        # Validate times for ad-hoc classes
        if self.attendance_type == AttendanceType.ADHOC:
            if not self.start_time or not self.end_time:
                if not self.duration_minutes:
                    raise ValidationError(
                        "Ad-hoc classes must have either start/end times or duration."
                    )
        
        # Validate end_time > start_time if both are provided
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    "end_time": "End time must be after start time."
                })
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration if times are provided
        if self.start_time and self.end_time and not self.duration_minutes:
            from datetime import datetime, date
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            self.duration_minutes = int((end - start).total_seconds() / 60)
        
        # Copy times from routine entry if not provided
        if self.routine_entry and not self.start_time:
            self.start_time = self.routine_entry.start_time
            self.end_time = self.routine_entry.end_time
        
        super().save(*args, **kwargs)
    
    @property
    def user(self):
        return self.subject.semester.user
    
    @property
    def affects_percentage(self):
        """Returns True if this record affects attendance percentage."""
        return self.status != AttendanceStatus.CANCELLED
