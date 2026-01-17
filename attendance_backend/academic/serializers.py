from rest_framework import serializers
from .models import Semester, Subject


class SubjectSerializer(serializers.ModelSerializer):
    """Serializer for Subject model."""
    
    attendance_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = [
            "id", "semester", "name", "code", "credit",
            "min_attendance_percentage", "color",
            "created_at", "updated_at", "attendance_stats"
        ]
        read_only_fields = ["id", "created_at", "updated_at", "attendance_stats"]
    
    def get_attendance_stats(self, obj):
        """Get basic attendance stats for the subject."""
        from analytics.services import AttendanceAnalyticsService
        
        try:
            analytics = AttendanceAnalyticsService.get_subject_analytics(obj)
            return {
                "total_conducted": analytics.total_conducted,
                "total_attended": analytics.total_attended,
                "percentage": str(analytics.attendance_percentage),
                "status": analytics.status,
            }
        except Exception:
            return None


class SubjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subjects."""
    
    class Meta:
        model = Subject
        fields = [
            "id", "semester", "name", "code", "credit",
            "min_attendance_percentage", "color"
        ]
        read_only_fields = ["id"]
    
    def validate_semester(self, value):
        """Ensure user owns the semester."""
        request = self.context.get("request")
        if request and value.user != request.user:
            raise serializers.ValidationError(
                "You don't have permission to add subjects to this semester."
            )
        return value
    
    def validate(self, attrs):
        """Check for duplicate subject name in semester."""
        semester = attrs.get("semester")
        name = attrs.get("name")
        
        if Subject.objects.filter(semester=semester, name=name).exists():
            raise serializers.ValidationError({
                "name": f"A subject named '{name}' already exists in this semester."
            })
        
        return attrs


class SemesterSerializer(serializers.ModelSerializer):
    """Serializer for Semester model."""
    
    subjects = SubjectSerializer(many=True, read_only=True)
    subject_count = serializers.SerializerMethodField()
    has_routine = serializers.SerializerMethodField()
    
    class Meta:
        model = Semester
        fields = [
            "id", "name", "start_date", "end_date", "status",
            "is_current", "subjects", "subject_count", "has_routine",
            "created_at", "updated_at"
        ]
        read_only_fields = [
            "id", "subjects", "subject_count", "has_routine",
            "created_at", "updated_at"
        ]
    
    def get_subject_count(self, obj):
        return obj.subjects.count()
    
    def get_has_routine(self, obj):
        return hasattr(obj, "routine") and obj.routine is not None


class SemesterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating semesters."""
    
    class Meta:
        model = Semester
        fields = [
            "id", "name", "start_date", "end_date", "status", "is_current"
        ]
        read_only_fields = ["id"]
    
    def validate(self, attrs):
        """Validate semester dates."""
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date."
            })
        
        # Check for duplicate semester name
        request = self.context.get("request")
        name = attrs.get("name")
        
        if request and Semester.objects.filter(user=request.user, name=name).exists():
            raise serializers.ValidationError({
                "name": f"A semester named '{name}' already exists."
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create semester with user from request."""
        request = self.context.get("request")
        validated_data["user"] = request.user
        return super().create(validated_data)


class SemesterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for semester list views."""
    
    subject_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Semester
        fields = [
            "id", "name", "start_date", "end_date", "status",
            "is_current", "subject_count"
        ]
    
    def get_subject_count(self, obj):
        return obj.subjects.count()
