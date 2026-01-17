from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AttendanceRecordViewSet
from .export_views import (
    ExportAttendanceView,
    ExportSubjectSummaryView,
    ExportSemesterReportView,
)

app_name = "attendance"

router = DefaultRouter()
router.register(r"", AttendanceRecordViewSet, basename="attendance")

urlpatterns = [
    # Export endpoints
    path("exports/attendance/", ExportAttendanceView.as_view(), name="export-attendance"),
    path("exports/subjects/", ExportSubjectSummaryView.as_view(), name="export-subjects"),
    path("exports/semester/<int:semester_id>/", ExportSemesterReportView.as_view(), name="export-semester"),
    
    # Regular attendance endpoints
    path("", include(router.urls)),
]
