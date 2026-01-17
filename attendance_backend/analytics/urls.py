from django.urls import path
from .views import (
    SemesterAnalyticsView,
    SubjectAnalyticsView,
    WeeklyTrendsView,
    MonthlyTrendsView,
    AttendanceHistoryView,
    AlertsView,
    DashboardView,
)

app_name = "analytics"

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("semester/<int:semester_id>/", SemesterAnalyticsView.as_view(), name="semester-analytics"),
    path("semester/<int:semester_id>/alerts/", AlertsView.as_view(), name="semester-alerts"),
    path("subject/<int:subject_id>/", SubjectAnalyticsView.as_view(), name="subject-analytics"),
    path("subject/<int:subject_id>/weekly/", WeeklyTrendsView.as_view(), name="weekly-trends"),
    path("subject/<int:subject_id>/monthly/", MonthlyTrendsView.as_view(), name="monthly-trends"),
    path("subject/<int:subject_id>/history/", AttendanceHistoryView.as_view(), name="attendance-history"),
]
