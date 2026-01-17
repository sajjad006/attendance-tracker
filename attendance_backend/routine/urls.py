from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoutineViewSet, RoutineEntryViewSet

app_name = "routine"

router = DefaultRouter()
router.register(r"routines", RoutineViewSet, basename="routine")
router.register(r"routine-entries", RoutineEntryViewSet, basename="routine-entry")

urlpatterns = [
    path("", include(router.urls)),
]
