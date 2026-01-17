from rest_framework import serializers
from datetime import date
from .models import AttendanceRecord, AttendanceStatus, AttendanceType
from academic.models import Subject


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Serializer for AttendanceRecord model."""
    
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    subject_code = serializers.CharField(source="subject.code", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    type_display = serializers.CharField(source="get_attendance_type_display", read_only=True)
    affects_percentage = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "subject", "subject_name", "subject_code", "routine_entry",
            "date", "status", "status_display", "attendance_type", "type_display",
            "start_time", "end_time", "duration_minutes", "notes", "is_holiday",
            "affects_percentage", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "subject_name", "subject_code", "status_display",
            "type_display", "affects_percentage", "created_at", "updated_at"
        ]


class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating attendance records."""
    
    class Meta:
        model = AttendanceRecord
        fields = [
            "id", "subject", "date", "status", "attendance_type",
            "start_time", "end_time", "duration_minutes", "notes", "is_holiday"
        ]
        read_only_fields = ["id"]
    
    def validate_subject(self, value):
        """Ensure user owns the subject."""
        request = self.context.get("request")
        if request and value.user != request.user:
            raise serializers.ValidationError(
                "You don't have permission to add attendance for this subject."
            )
        return value
    
    def validate(self, attrs):
        """Validate attendance record."""
        subject = attrs.get("subject")
        target_date = attrs.get("date")
        start_time = attrs.get("start_time")
        attendance_type = attrs.get("attendance_type", AttendanceType.ROUTINE)
        
        # Validate date is within semester
        semester = subject.semester
        if target_date < semester.start_date:
            raise serializers.ValidationError({
                "date": f"Date is before semester start ({semester.start_date})"
            })
        if target_date > semester.end_date:
            raise serializers.ValidationError({
                "date": f"Date is after semester end ({semester.end_date})"
            })
        
        # Check for duplicates
        instance = getattr(self, "instance", None)
        query = AttendanceRecord.objects.filter(
            subject=subject,
            date=target_date,
            start_time=start_time
        )
        
        if instance:
            query = query.exclude(pk=instance.pk)
        
        if query.exists():
            raise serializers.ValidationError(
                "An attendance record already exists for this subject, date, and time."
            )
        
        # Validate ad-hoc class requirements
        if attendance_type == AttendanceType.ADHOC:
            if not start_time and not attrs.get("duration_minutes"):
                raise serializers.ValidationError(
                    "Ad-hoc classes must have either start/end times or duration."
                )
        
        return attrs


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating attendance records (limited fields)."""
    
    class Meta:
        model = AttendanceRecord
        fields = ["status", "notes", "is_holiday"]


class BulkAttendanceSerializer(serializers.Serializer):
    """Serializer for bulk attendance operations."""
    
    record_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    status = serializers.ChoiceField(choices=AttendanceStatus.choices)


class MarkDayAttendanceSerializer(serializers.Serializer):
    """Serializer for marking all classes on a day."""
    
    semester_id = serializers.IntegerField()
    date = serializers.DateField()
    status = serializers.ChoiceField(choices=AttendanceStatus.choices)


class AdHocClassSerializer(serializers.Serializer):
    """Serializer for creating ad-hoc (extra) classes."""
    
    subject_id = serializers.IntegerField()
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    status = serializers.ChoiceField(
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_subject_id(self, value):
        """Validate subject exists and user owns it."""
        request = self.context.get("request")
        
        try:
            subject = Subject.objects.get(pk=value)
        except Subject.DoesNotExist:
            raise serializers.ValidationError("Subject not found.")
        
        if request and subject.user != request.user:
            raise serializers.ValidationError(
                "You don't have permission to add classes for this subject."
            )
        
        return value
    
    def validate(self, attrs):
        """Validate times."""
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError({
                "end_time": "End time must be after start time."
            })
        return attrs


class GenerateClassesSerializer(serializers.Serializer):
    """Serializer for generating classes from routine."""
    
    semester_id = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    
    def validate(self, attrs):
        """Validate date range."""
        if attrs["start_date"] > attrs["end_date"]:
            raise serializers.ValidationError({
                "end_date": "End date must be after or equal to start date."
            })
        
        # Limit range to prevent excessive generation
        from datetime import timedelta
        max_days = 90
        if (attrs["end_date"] - attrs["start_date"]).days > max_days:
            raise serializers.ValidationError(
                f"Date range cannot exceed {max_days} days."
            )
        
        return attrs


class AttendanceHistoryFilterSerializer(serializers.Serializer):
    """Serializer for filtering attendance history."""
    
    subject_id = serializers.IntegerField(required=False)
    semester_id = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    status = serializers.ChoiceField(
        choices=AttendanceStatus.choices,
        required=False
    )
    attendance_type = serializers.ChoiceField(
        choices=AttendanceType.choices,
        required=False
    )
