import os
from datetime import datetime, timedelta, timezone

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import AuditLog, Certificate, UserEntity
from .pki_service import PKIService
from .serializers import (
    AuditLogSerializer,
    CertificateSerializer,
    CreateCertificateSerializer,
    RevokeCertificateSerializer,
    UserEntitySerializer,
    ValidateCertificateSerializer,
)


def _log(accion, descripcion, usuario=''):
    AuditLog.objects.create(
        accion=accion,
        descripcion=descripcion,
        usuario_responsable=usuario,
    )


class UserEntityViewSet(viewsets.ModelViewSet):
    queryset = UserEntity.objects.all()
    serializer_class = UserEntitySerializer


class CertificateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializer

    @action(detail=False, methods=['post'])
    def create_cert(self, request):
        serializer = CreateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = UserEntity.objects.get(id=serializer.validated_data['usuario_id'])
        except UserEntity.DoesNotExist:
            return Response(
                {'error': 'Usuario no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        private_pem, public_pem, private_key = PKIService.generate_key_pair()
        cert_pem, serial_number = PKIService.generate_certificate(
            usuario.nombre, public_pem, private_key
        )

        cert_dir = os.path.join(settings.MEDIA_ROOT, 'certificados', str(usuario.id))
        os.makedirs(cert_dir, exist_ok=True)
        cert_path = os.path.join(cert_dir, f'{serial_number}.crt')
        pub_path = os.path.join(cert_dir, f'{serial_number}_public.pem')
        priv_path = os.path.join(cert_dir, f'{serial_number}_private.pem')

        PKIService.save_pem(cert_path, cert_pem)
        PKIService.save_pem(pub_path, public_pem)
        PKIService.save_pem(priv_path, private_pem)

        certificate = Certificate.objects.create(
            serial=str(serial_number),
            usuario=usuario,
            fecha_expiracion=datetime.now(timezone.utc) + timedelta(days=365),
            ruta_certificado=cert_path,
            ruta_clave_publica=pub_path,
        )

        _log(
            'Certificado generado',
            f'Certificado {serial_number} emitido para {usuario.nombre} ({usuario.correo})',
            usuario.nombre,
        )

        return Response(
            CertificateSerializer(certificate).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def validate(self, request):
        serializer = ValidateCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cert_file = serializer.validated_data['certificado']
        cert_pem = cert_file.read()

        is_valid, message = PKIService.validate_certificate(cert_pem)

        log_action = 'Certificado validado' if is_valid else 'Error de validación'
        _log(log_action, message)

        return Response({'valido': is_valid, 'mensaje': message})

    @action(detail=False, methods=['post'])
    def revoke(self, request):
        serializer = RevokeCertificateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            certificate = Certificate.objects.get(
                serial=serializer.validated_data['serial']
            )
        except Certificate.DoesNotExist:
            return Response(
                {'error': 'Certificado no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if certificate.estado == Certificate.Estado.REVOCADO:
            return Response(
                {'error': 'El certificado ya está revocado'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        certificate.estado = Certificate.Estado.REVOCADO
        certificate.save()

        _log(
            'Certificado revocado',
            f'Certificado {certificate.serial} revocado para {certificate.usuario.nombre}',
            certificate.usuario.nombre,
        )

        return Response(CertificateSerializer(certificate).data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-fecha')
    serializer_class = AuditLogSerializer
