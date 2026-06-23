# CA-Certificate-Manager

Prototipo de gestión de certificados digitales para una Autoridad Certificadora académica.

## Funcionalidades

- Registro de usuarios o entidades.
- Emisión de certificados digitales autofirmados.
- Validación de certificados.
- Revocación de certificados.
- Registro de logs de auditoría.
- Panel web responsivo para administración.

## Ejecución local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Luego abre el frontend en:

- `frontend/index.html` directamente en el navegador, o
- intégralo con un servidor local simple.

La API queda disponible en:

- `http://127.0.0.1:8000/api/users/`
- `http://127.0.0.1:8000/api/certificates/`
- `http://127.0.0.1:8000/api/logs/`
