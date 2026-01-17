from django.contrib import admin
from .models import Semester, Subject


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "start_date", "end_date", "status", "is_current", "is_deleted"]
    list_filter = ["status", "is_current", "is_deleted"]
    search_fields = ["name", "user__username"]
    ordering = ["-start_date"]
    date_hierarchy = "start_date"


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "semester", "credit", "min_attendance_percentage", "is_deleted"]
    list_filter = ["semester", "is_deleted"]
    search_fields = ["name", "code", "semester__name"]
    ordering = ["semester", "name"]
