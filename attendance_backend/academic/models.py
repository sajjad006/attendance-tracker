from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class SoftDeleteManager(models.Manager):
    """Manager that filters out soft-deleted records by default."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
    def with_deleted(self):
        return super().get_queryset()
    
    def deleted_only(self):
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality."""
    
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class Semester(SoftDeleteModel):
    """
    Represents an academic semester.
    Each semester contains unique subjects and one routine.
    """
    
    class SemesterStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        UPCOMING = "upcoming", "Upcoming"
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="semesters"
    )
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=SemesterStatus.choices,
        default=SemesterStatus.ACTIVE
    )
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "academic_semester"
        ordering = ["-start_date"]
        unique_together = ["user", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def save(self, *args, **kwargs):
        # Ensure only one semester is marked as current per user
        if self.is_current:
            Semester.objects.filter(user=self.user, is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class Subject(SoftDeleteModel):
    """
    Represents a subject within a semester.
    Subjects are unique per semester.
    """
    
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="subjects"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    credit = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Credit value (for reference only, does not affect attendance)"
    )
    min_attendance_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=75.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Minimum required attendance percentage"
    )
    color = models.CharField(
        max_length=7, 
        default="#3B82F6",
        help_text="Hex color code for UI display"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "academic_subject"
        ordering = ["name"]
        unique_together = ["semester", "name"]
    
    def __str__(self):
        code_str = f" ({self.code})" if self.code else ""
        return f"{self.name}{code_str}"
    
    @property
    def user(self):
        return self.semester.user
