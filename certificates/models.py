from django.db import models


class UserEntity(models.Model):
    nombre = models.CharField(max_length=255)
    correo = models.EmailField(unique=True)
    empresa = models.CharField(max_length=255, blank=True, default='')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.correo})"


class Certificate(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'Activo', 'Activo'
        REVOCADO = 'Revocado', 'Revocado'
        EXPIRADO = 'Expirado', 'Expirado'

    serial = models.CharField(max_length=64, unique=True)
    usuario = models.ForeignKey(
        UserEntity, on_delete=models.CASCADE, related_name='certificados'
    )
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ACTIVO
    )
    ruta_certificado = models.CharField(max_length=512)
    ruta_clave_publica = models.CharField(max_length=512)

    def __str__(self):
        return f"Cert-{self.serial} [{self.estado}]"


class CertificateRequest(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        APROBADA = 'Aprobada', 'Aprobada'
        RECHAZADA = 'Rechazada', 'Rechazada'

    usuario = models.ForeignKey(
        UserEntity, on_delete=models.CASCADE, related_name='solicitudes'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )

    def __str__(self):
        return f"Solicitud-{self.id} - {self.usuario.nombre} [{self.estado}]"


class AuditLog(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=100)
    descripcion = models.TextField()
    usuario_responsable = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"[{self.fecha}] {self.accion}"
