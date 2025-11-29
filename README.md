# Data Entry Bot 🤖

Sistema de automatización de Data Entry accesible mediante un bot de Telegram con Mini App, que utiliza Gemini Vision para procesar documentos y cheques, y valida información crediticia mediante la API del BCRA.

## 🚀 Características

- **Bot de Telegram** con Mini App integrada
- **Procesamiento OCR** con Google Gemini Vision
- **Lectura especializada de cheques** con extracción de campos estructurados
- **Validación BCRA** para verificar situación crediticia
- **Interfaz web** para revisar y editar datos extraídos
- **API REST** con FastAPI
- **Docker** para despliegue fácil

## 📋 Stack Tecnológico

- **Backend**: Python 3.11+, FastAPI, uvicorn
- **Bot**: python-telegram-bot
- **OCR/Vision**: Google Gemini API
- **Validación**: API BCRA (con modo mock)
- **Frontend**: HTML + JavaScript vanilla
- **Infraestructura**: Docker, docker-compose

## 🏗️ Estructura del Proyecto

```
dataentrybot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── routes.py            # API endpoints
│   ├── bot.py                # Telegram bot
│   ├── config.py             # Configuration
│   ├── models.py             # Pydantic models
│   ├── gemini_client.py      # Gemini API client
│   ├── bcra_client.py        # BCRA API client
│   ├── cheques_processor.py  # Cheque processing logic
│   └── utils/
│       └── file.py           # File utilities
├── webapp/
│   ├── index.html            # Mini App HTML
│   └── script.js             # Mini App JavaScript
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## 🔧 Instalación

### Prerrequisitos

- Python 3.11+
- Docker y Docker Compose (opcional)
- Token de bot de Telegram
- API Key de Google Gemini

### Configuración

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/sebastianjlopez/dataentrybot.git
   cd dataentrybot
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```
   
   Editar `.env` y configurar:
   - `TELEGRAM_BOT_TOKEN`: Token de tu bot de Telegram
   - `GEMINI_API_KEY`: API Key de Google Gemini
   - `TELEGRAM_WEBAPP_URL`: URL de la Mini App (ej: `https://tu-dominio.com/webapp`)

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

### Ejecución con Docker

```bash
docker-compose up -d
```

### Ejecución local

1. **Iniciar la API**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Iniciar el bot** (en otra terminal)
   ```bash
   python -m app.bot
   ```

## 📡 Endpoints API

### `POST /api/upload`
Sube y procesa un archivo (imagen, PDF, cheque).

**Request**: `multipart/form-data` con campo `file`

**Response**:
```json
{
  "success": true,
  "tipo_documento": "cheque",
  "data": { ... },
  "filename": "cheque.jpg"
}
```

### `POST /api/process`
Procesa datos validados desde la Mini App.

**Request**:
```json
{
  "tipo_documento": "cheque",
  "datos": { ... },
  "usuario_id": "123456789"
}
```

### `GET /api/health`
Health check del servicio.

## 🤖 Uso del Bot

1. Iniciar conversación: `/start`
2. Enviar una foto o PDF
3. El bot procesará el documento automáticamente
4. Si es un cheque, validará con BCRA
5. Revisar y editar datos en la Mini App
6. Confirmar para procesar

## 📝 Modelo de Datos - Cheque

```json
{
  "tipo_documento": "cheque",
  "cuit_librador": "20-12345678-9",
  "banco": "Banco Nación",
  "fecha_emision": "2024-01-15",
  "fecha_pago": "2024-01-30",
  "importe": 50000.0,
  "numero_cheque": "12345678",
  "cbu_beneficiario": "1234567890123456789012",
  "estado_bcra": "Sin deuda",
  "cheques_rechazados": 0,
  "riesgo_crediticio": "A"
}
```

## 🔐 Validación BCRA

El sistema valida automáticamente la situación crediticia del librador del cheque:
- Estado crediticio (Sin deuda / Deuda moderada / Deuda alta)
- Cantidad de cheques rechazados
- Nivel de riesgo crediticio (A, B, C)

**Nota**: Actualmente funciona en modo mock. Para producción, configurar `BCRA_MOCK_MODE=false` y proporcionar `BCRA_API_KEY`.

## 🛠️ Desarrollo

### Estructura de Módulos

- **`app/main.py`**: Aplicación FastAPI principal
- **`app/routes.py`**: Definición de endpoints
- **`app/bot.py`**: Lógica del bot de Telegram
- **`app/gemini_client.py`**: Cliente para Gemini Vision API
- **`app/bcra_client.py`**: Cliente para BCRA API
- **`app/cheques_processor.py`**: Procesamiento especializado de cheques
- **`app/models.py`**: Modelos Pydantic para validación

### Agregar Nuevos Tipos de Documentos

1. Crear modelo en `app/models.py`
2. Agregar lógica de procesamiento
3. Actualizar `app/routes.py` para manejar el nuevo tipo
4. Actualizar Mini App si es necesario

## 📄 Licencia

Este proyecto es una demo profesional para roles administrativos y automatización de data entry.

## 👤 Autor

Sebastián López

## 🔗 Enlaces

- [Repositorio GitHub](https://github.com/sebastianjlopez/dataentrybot)
- [Documentación FastAPI](http://localhost:8000/docs) (cuando el servidor está corriendo)

