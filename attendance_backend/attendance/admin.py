from django.contrib import admin
from .models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ["subject", "date", "status", "attendance_type", "start_time", "end_time", "is_holiday"]
    list_filter = ["status", "attendance_type", "is_holiday", "date"]
    search_fields = ["subject__name", "notes"]
    ordering = ["-date", "-start_time"]
    date_hierarchy = "date"
    
    readonly_fields = ["created_at", "updated_at"]
