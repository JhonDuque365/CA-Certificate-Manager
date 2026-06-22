from django.contrib import admin

from .models import AuditLog, Certificate, CertificateRequest, UserEntity


@admin.register(UserEntity)
class UserEntityAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'correo', 'empresa', 'fecha_creacion']
    search_fields = ['nombre', 'correo']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['id', 'serial', 'usuario', 'fecha_emision', 'fecha_expiracion', 'estado']
    list_filter = ['estado']
    search_fields = ['serial', 'usuario__nombre']


@admin.register(CertificateRequest)
class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'fecha_solicitud', 'estado']
    list_filter = ['estado']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'fecha', 'accion', 'usuario_responsable']
    list_filter = ['accion']
    readonly_fields = ['fecha', 'accion', 'descripcion', 'usuario_responsable']
