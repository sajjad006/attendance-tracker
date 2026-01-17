from rest_framework import serializers


class SubjectAnalyticsSerializer(serializers.Serializer):
    """Serializer for subject analytics response."""
    
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    subject_code = serializers.CharField(allow_null=True)
    total_conducted = serializers.IntegerField()
    total_attended = serializers.IntegerField()
    total_absent = serializers.IntegerField()
    total_cancelled = serializers.IntegerField()
    attendance_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    min_required_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.ChoiceField(choices=["safe", "borderline", "shortage"])
    classes_can_miss = serializers.IntegerField()
    classes_need_to_attend = serializers.IntegerField()


class SemesterOverviewSerializer(serializers.Serializer):
    """Serializer for semester overview."""
    
    total_subjects = serializers.IntegerField()
    overall_attendance = serializers.CharField()
    subjects_safe = serializers.IntegerField()
    subjects_borderline = serializers.IntegerField()
    subjects_shortage = serializers.IntegerField()


class SemesterAnalyticsSerializer(serializers.Serializer):
    """Serializer for complete semester analytics."""
    
    semester = serializers.DictField()
    overview = SemesterOverviewSerializer()
    subjects = SubjectAnalyticsSerializer(many=True)


class WeeklyTrendSerializer(serializers.Serializer):
    """Serializer for weekly attendance trend."""
    
    week_start = serializers.CharField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    conducted = serializers.IntegerField()
    percentage = serializers.FloatField()


class MonthlyTrendSerializer(serializers.Serializer):
    """Serializer for monthly attendance trend."""
    
    month = serializers.CharField()
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    conducted = serializers.IntegerField()
    percentage = serializers.FloatField()


class AlertSerializer(serializers.Serializer):
    """Serializer for attendance alerts."""
    
    type = serializers.ChoiceField(choices=["shortage", "borderline"])
    severity = serializers.ChoiceField(choices=["high", "medium", "low"])
    subject_id = serializers.IntegerField()
    subject_name = serializers.CharField()
    message = serializers.CharField()
    current_percentage = serializers.CharField()
    required_percentage = serializers.CharField()
    classes_needed = serializers.IntegerField(required=False)
    classes_can_miss = serializers.IntegerField(required=False)


class AttendanceHistoryItemSerializer(serializers.Serializer):
    """Serializer for attendance history items."""
    
    id = serializers.IntegerField()
    date = serializers.CharField()
    status = serializers.CharField()
    type = serializers.CharField()
    start_time = serializers.CharField(allow_null=True)
    end_time = serializers.CharField(allow_null=True)
    duration_minutes = serializers.IntegerField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    is_holiday = serializers.BooleanField()
