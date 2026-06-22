from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditLogViewSet, CertificateViewSet, UserEntityViewSet

router = DefaultRouter()
router.register(r'users', UserEntityViewSet)
router.register(r'certificates', CertificateViewSet)
router.register(r'logs', AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
