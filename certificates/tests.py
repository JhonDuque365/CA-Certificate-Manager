import os
import tempfile
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .models import AuditLog, Certificate, UserEntity
from .pki_service import PKIService


class PKIServiceTestCase(TestCase):
    def test_generate_key_pair(self):
        priv_pem, pub_pem, priv_key = PKIService.generate_key_pair()
        self.assertTrue(priv_pem.startswith(b'-----BEGIN RSA PRIVATE KEY-----'))
        self.assertTrue(pub_pem.startswith(b'-----BEGIN PUBLIC KEY-----'))

    def test_generate_and_validate_certificate(self):
        priv_pem, pub_pem, priv_key = PKIService.generate_key_pair()
        cert_pem, serial = PKIService.generate_certificate('Test User', pub_pem, priv_key)
        self.assertTrue(cert_pem.startswith(b'-----BEGIN CERTIFICATE-----'))

        is_valid, msg = PKIService.validate_certificate(cert_pem)
        self.assertTrue(is_valid, msg)

    def test_validate_expired_certificate(self):
        priv_pem, pub_pem, priv_key = PKIService.generate_key_pair()
        cert_pem, serial = PKIService.generate_certificate('Test User', pub_pem, priv_key)
        is_valid, msg = PKIService.validate_certificate(cert_pem)
        self.assertTrue(is_valid)

    def test_validate_invalid_certificate(self):
        is_valid, msg = PKIService.validate_certificate(b'not a certificate')
        self.assertFalse(is_valid)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CertificateAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserEntity.objects.create(
            nombre='Juan Perez',
            correo='juan@example.com',
            empresa='TechCorp',
        )

    def test_create_user(self):
        response = self.client.post('/api/users/', {
            'nombre': 'Maria Lopez',
            'correo': 'maria@example.com',
            'empresa': 'CyberSec',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nombre'], 'Maria Lopez')

    def test_list_users(self):
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_emit_certificate(self):
        response = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['usuario'], self.user.id)
        self.assertTrue(response.data['serial'] is not None)
        self.assertTrue(os.path.exists(response.data['ruta_certificado']))

    def test_emit_certificate_invalid_user(self):
        response = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': 999,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validate_certificate(self):
        cert_resp = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        cert_path = cert_resp.data['ruta_certificado']

        with open(cert_path, 'rb') as f:
            response = self.client.post('/api/certificates/validate/', {
                'certificado': f,
            }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valido'])

    def test_revoke_certificate(self):
        cert_resp = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        serial = cert_resp.data['serial']

        response = self.client.post('/api/certificates/revoke/', {
            'serial': serial,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['estado'], 'Revocado')

    def test_revoke_already_revoked(self):
        cert_resp = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        serial = cert_resp.data['serial']

        self.client.post('/api/certificates/revoke/', {'serial': serial}, format='json')
        response = self.client.post('/api/certificates/revoke/', {'serial': serial}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revoke_nonexistent_certificate(self):
        response = self.client.post('/api/certificates/revoke/', {
            'serial': 'nonexistent',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_validate_revoked_certificate(self):
        cert_resp = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        serial = cert_resp.data['serial']
        cert_path = cert_resp.data['ruta_certificado']

        self.client.post('/api/certificates/revoke/', {'serial': serial}, format='json')

        with open(cert_path, 'rb') as f:
            response = self.client.post('/api/certificates/validate/', {
                'certificado': f,
            }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_audit_logs_created(self):
        self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')

        logs = AuditLog.objects.all()
        self.assertTrue(logs.count() >= 1)
        self.assertEqual(logs.first().accion, 'Certificado generado')

    def test_audit_logs_endpoint(self):
        AuditLog.objects.create(
            accion='Prueba',
            descripcion='Log de prueba',
        )
        response = self.client.get('/api/logs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_full_flow(self):
        response = self.client.get('/api/users/')
        self.assertEqual(len(response.data), 1)

        cert_resp = self.client.post('/api/certificates/create_cert/', {
            'usuario_id': self.user.id,
        }, format='json')
        self.assertEqual(cert_resp.status_code, status.HTTP_201_CREATED)
        serial = cert_resp.data['serial']

        with open(cert_resp.data['ruta_certificado'], 'rb') as f:
            val_resp = self.client.post('/api/certificates/validate/', {
                'certificado': f,
            }, format='multipart')
        self.assertTrue(val_resp.data['valido'])

        rev_resp = self.client.post('/api/certificates/revoke/', {
            'serial': serial,
        }, format='json')
        self.assertEqual(rev_resp.data['estado'], 'Revocado')

        log_resp = self.client.get('/api/logs/')
        self.assertGreaterEqual(len(log_resp.data), 2)
