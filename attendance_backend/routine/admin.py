from django.contrib import admin
from .models import Routine, RoutineEntry


class RoutineEntryInline(admin.TabularInline):
    model = RoutineEntry
    extra = 1
    fields = ["subject", "day_of_week", "start_time", "end_time", "room"]


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ["name", "semester", "is_active", "is_deleted", "created_at"]
    list_filter = ["is_active", "is_deleted"]
    search_fields = ["name", "semester__name"]
    inlines = [RoutineEntryInline]


@admin.register(RoutineEntry)
class RoutineEntryAdmin(admin.ModelAdmin):
    list_display = ["subject", "routine", "day_of_week", "start_time", "end_time", "room"]
    list_filter = ["day_of_week", "routine"]
    search_fields = ["subject__name", "routine__name"]
    ordering = ["routine", "day_of_week", "start_time"]
