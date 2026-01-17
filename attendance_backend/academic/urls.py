from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SemesterViewSet, SubjectViewSet

app_name = "academic"

router = DefaultRouter()
router.register(r"semesters", SemesterViewSet, basename="semester")
router.register(r"subjects", SubjectViewSet, basename="subject")

urlpatterns = [
    path("", include(router.urls)),
]
