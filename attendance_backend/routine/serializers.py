from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Routine, RoutineEntry, DayOfWeek
from academic.serializers import SubjectSerializer


class RoutineEntrySerializer(serializers.ModelSerializer):
    """Serializer for RoutineEntry model."""
    
    subject_details = SubjectSerializer(source="subject", read_only=True)
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = RoutineEntry
        fields = [
            "id", "routine", "subject", "subject_details", "day_of_week",
            "day_name", "start_time", "end_time", "room", "notes",
            "duration_minutes", "duration_hours", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "subject_details", "day_name", "duration_minutes",
            "duration_hours", "created_at", "updated_at"
        ]


class RoutineEntryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating routine entries."""
    
    class Meta:
        model = RoutineEntry
        fields = [
            "id", "routine", "subject", "day_of_week",
            "start_time", "end_time", "room", "notes"
        ]
        read_only_fields = ["id"]
    
    def validate(self, attrs):
        """Validate routine entry."""
        routine = attrs.get("routine")
        subject = attrs.get("subject")
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        day_of_week = attrs.get("day_of_week")
        
        # Ensure subject belongs to the same semester as routine
        if subject.semester != routine.semester:
            raise serializers.ValidationError({
                "subject": "Subject must belong to the same semester as the routine."
            })
        
        # Validate time range
        if start_time >= end_time:
            raise serializers.ValidationError({
                "end_time": "End time must be after start time."
            })
        
        # Check for overlapping entries
        instance = getattr(self, "instance", None)
        overlapping = RoutineEntry.objects.filter(
            routine=routine,
            day_of_week=day_of_week
        )
        
        if instance:
            overlapping = overlapping.exclude(pk=instance.pk)
        
        for entry in overlapping:
            if start_time < entry.end_time and end_time > entry.start_time:
                raise serializers.ValidationError(
                    f"This time slot overlaps with {entry.subject.name} "
                    f"({entry.start_time.strftime('%H:%M')}-{entry.end_time.strftime('%H:%M')})"
                )
        
        return attrs
    
    def validate_routine(self, value):
        """Ensure user owns the routine."""
        request = self.context.get("request")
        if request and value.user != request.user:
            raise serializers.ValidationError(
                "You don't have permission to add entries to this routine."
            )
        return value


class RoutineSerializer(serializers.ModelSerializer):
    """Serializer for Routine model."""
    
    entries = RoutineEntrySerializer(many=True, read_only=True)
    semester_name = serializers.CharField(source="semester.name", read_only=True)
    entries_by_day = serializers.SerializerMethodField()
    
    class Meta:
        model = Routine
        fields = [
            "id", "semester", "semester_name", "name", "is_active",
            "entries", "entries_by_day", "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "entries", "entries_by_day", "semester_name",
            "created_at", "updated_at"
        ]
    
    def get_entries_by_day(self, obj):
        """Group entries by day of week."""
        entries_by_day = {}
        
        for day_value, day_name in DayOfWeek.choices:
            day_entries = obj.entries.filter(day_of_week=day_value).order_by("start_time")
            entries_by_day[day_name] = RoutineEntrySerializer(day_entries, many=True).data
        
        return entries_by_day


class RoutineCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating routines."""
    
    class Meta:
        model = Routine
        fields = ["id", "semester", "name", "is_active"]
        read_only_fields = ["id"]
    
    def validate_semester(self, value):
        """Ensure user owns the semester and no routine exists."""
        request = self.context.get("request")
        
        if request and value.user != request.user:
            raise serializers.ValidationError(
                "You don't have permission to create a routine for this semester."
            )
        
        # Check if routine already exists
        if hasattr(value, "routine"):
            raise serializers.ValidationError(
                "A routine already exists for this semester. "
                "Each semester can only have one routine."
            )
        
        return value


class BulkRoutineEntrySerializer(serializers.Serializer):
    """Serializer for bulk creating routine entries."""
    
    entries = RoutineEntryCreateSerializer(many=True)
    
    def validate_entries(self, value):
        """Validate all entries for overlaps among themselves."""
        # Group by day
        by_day = {}
        for entry in value:
            day = entry["day_of_week"]
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(entry)
        
        # Check for overlaps within each day
        for day, entries in by_day.items():
            for i, entry1 in enumerate(entries):
                for entry2 in entries[i+1:]:
                    if (entry1["start_time"] < entry2["end_time"] and 
                        entry1["end_time"] > entry2["start_time"]):
                        raise serializers.ValidationError(
                            f"Entries overlap on {DayOfWeek(day).label}: "
                            f"{entry1['subject']} and {entry2['subject']}"
                        )
        
        return value
