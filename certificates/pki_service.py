import os
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID


class PKIService:
    @staticmethod
    def generate_key_pair():
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return private_pem, public_pem, private_key

    @staticmethod
    def generate_certificate(subject_name, public_key_pem, private_key):
        public_key = serialization.load_pem_public_key(public_key_pem)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
        ])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(public_key)
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + timedelta(days=365))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .sign(private_key, hashes.SHA256())
        )
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        return cert_pem, cert.serial_number

    @staticmethod
    def validate_certificate(cert_pem: bytes):
        try:
            cert = x509.load_pem_x509_certificate(cert_pem)
        except Exception as e:
            return False, f"Formato de certificado inválido: {e}"

        errors = []
        now = datetime.now(timezone.utc)

        if now < cert.not_valid_before_utc:
            errors.append("El certificado aún no es válido")
        if now > cert.not_valid_after_utc:
            errors.append("El certificado ha expirado")

        try:
            public_key = cert.public_key()
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
        except Exception as e:
            errors.append(f"Error verificando firma: {e}")

        if errors:
            return False, "; ".join(errors)
        return True, "Certificado válido"

    @staticmethod
    def save_pem(filepath: str, pem_data: bytes):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(pem_data)

    @staticmethod
    def load_pem(filepath: str):
        with open(filepath, 'rb') as f:
            return f.read()
