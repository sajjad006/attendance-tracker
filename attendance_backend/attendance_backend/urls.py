"""
URL configuration for attendance_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """API root endpoint with information about available endpoints."""
    return Response({
        "message": "Student Attendance Tracker API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "register": "/api/auth/register/",
                "login": "/api/auth/login/",
                "logout": "/api/auth/logout/",
                "profile": "/api/auth/profile/",
                "change_password": "/api/auth/change-password/",
            },
            "academic": {
                "semesters": "/api/semesters/",
                "subjects": "/api/subjects/",
            },
            "routine": {
                "routines": "/api/routines/",
                "routine_entries": "/api/routine-entries/",
            },
            "attendance": "/api/attendance/",
            "analytics": {
                "dashboard": "/api/analytics/dashboard/",
                "semester": "/api/analytics/semester/{id}/",
                "subject": "/api/analytics/subject/{id}/",
            },
            "audit_logs": "/api/audit-logs/",
            "exports": "/api/exports/",
        }
    })


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root, name="api-root"),
    
    # Authentication
    path("api/auth/", include("users.urls", namespace="users")),
    
    # Academic (Semesters & Subjects)
    path("api/", include("academic.urls", namespace="academic")),
    
    # Routine (Timetable)
    path("api/", include("routine.urls", namespace="routine")),
    
    # Attendance
    path("api/attendance/", include("attendance.urls", namespace="attendance")),
    
    # Analytics
    path("api/analytics/", include("analytics.urls", namespace="analytics")),
    
    # Audit Logs
    path("api/audit-logs/", include("audit_logs.urls", namespace="audit_logs")),
]

