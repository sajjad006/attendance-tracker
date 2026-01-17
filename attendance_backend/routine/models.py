from django.db import models
from django.core.exceptions import ValidationError
from academic.models import Semester, Subject, SoftDeleteModel, SoftDeleteManager


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class Routine(SoftDeleteModel):
    """
    Represents a weekly timetable for a semester.
    Each semester has exactly one routine.
    """
    
    semester = models.OneToOneField(
        Semester,
        on_delete=models.CASCADE,
        related_name="routine"
    )
    name = models.CharField(max_length=100, default="Weekly Routine")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "routine_routine"
        ordering = ["-created_at"]
    
    def __str__(self):
        return f"{self.name} - {self.semester.name}"
    
    @property
    def user(self):
        return self.semester.user


class RoutineEntry(SoftDeleteModel):
    """
    Represents a single class slot in the routine.
    Contains day, time, subject, and duration information.
    """
    
    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="entries"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="routine_entries"
    )
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "routine_entry"
        ordering = ["day_of_week", "start_time"]
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}: {self.subject.name}"
    
    @property
    def duration_minutes(self):
        """Calculate duration in minutes."""
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        delta = end - start
        return int(delta.total_seconds() / 60)
    
    @property
    def duration_hours(self):
        """Calculate duration in hours."""
        return self.duration_minutes / 60
    
    def clean(self):
        """Validate that times are correct and no overlaps exist."""
        super().clean()
        
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                "end_time": "End time must be after start time."
            })
        
        # Only check for overlaps if we have a saved routine
        if self.routine_id and self.day_of_week is not None:
            # Check for overlapping entries on the same day
            overlapping = RoutineEntry.objects.filter(
                routine_id=self.routine_id,
                day_of_week=self.day_of_week
            ).exclude(pk=self.pk)
            
            for entry in overlapping:
                # Check if time ranges overlap
                if (self.start_time < entry.end_time and self.end_time > entry.start_time):
                    raise ValidationError(
                        f"This time slot overlaps with {entry.subject.name} "
                        f"({entry.start_time}-{entry.end_time})"
                    )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def user(self):
        return self.routine.user
