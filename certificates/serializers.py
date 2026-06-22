from rest_framework import serializers

from .models import AuditLog, Certificate, CertificateRequest, UserEntity


class UserEntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEntity
        fields = ['id', 'nombre', 'correo', 'empresa', 'fecha_creacion']


class CertificateSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.nombre', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'serial', 'usuario', 'usuario_nombre',
            'fecha_emision', 'fecha_expiracion', 'estado',
            'ruta_certificado', 'ruta_clave_publica',
        ]


class CertificateRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateRequest
        fields = ['id', 'usuario', 'fecha_solicitud', 'estado']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ['id', 'fecha', 'accion', 'descripcion', 'usuario_responsable']


class CreateCertificateSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()


class ValidateCertificateSerializer(serializers.Serializer):
    certificado = serializers.FileField()


class RevokeCertificateSerializer(serializers.Serializer):
    serial = serializers.CharField(max_length=64)
