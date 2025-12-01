# 🤖 Data Entry Bot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Sistema profesional de automatización de Data Entry con Telegram Bot, Gemini 2.5 LLM y validación BCRA**

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Documentación](#-documentación) • [Contribuir](#-contribuir)

</div>

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Stack Tecnológico](#-stack-tecnológico)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Arquitectura](#-arquitectura)
- [Desarrollo](#-desarrollo)
- [Despliegue](#-despliegue)
- [Troubleshooting](#-troubleshooting)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🎯 Descripción

**Data Entry Bot** es un sistema completo de automatización de data entry diseñado para roles administrativos. Permite procesar documentos, leer cheques mediante razonamiento avanzado con Gemini 2.5 LLM, validar información crediticia con la API del BCRA, y gestionar todo el flujo a través de un bot de Telegram.

### Casos de Uso

- ✅ Procesamiento automatizado de cheques
- ✅ Extracción de datos de documentos (fotos, PDFs)
- ✅ Validación crediticia en tiempo real
- ✅ Detección y procesamiento de múltiples cheques en un solo documento
- ✅ Formato comanda estructurado para visualización de resultados

---

## ✨ Características

### 🤖 Bot de Telegram
- Interfaz conversacional intuitiva
- Soporte para comandos `/start` y `/help`
- Procesamiento automático de imágenes y PDFs
- Formato comanda estructurado para mostrar resultados
- Detección automática de múltiples cheques en un documento

### 🔍 Procesamiento Inteligente con LLM
- **Gemini 2.5 LLM** (Flash/Pro) con capacidades de razonamiento avanzado
- Análisis estructural y contextual de documentos
- Detección automática de cheques con razonamiento
- Extracción estructurada de campos específicos con validación
- Soporte para múltiples formatos (JPG, PNG, PDF)

### 💰 Procesamiento de Cheques
- Extracción de datos clave:
  - CUIT del librador
  - Banco emisor
  - Fechas de emisión y pago
  - Importe y número de cheque
  - CBU/CUIT del beneficiario
- Validación automática con BCRA
- Normalización de formatos

### 🏦 Validación BCRA
- Consulta de situación crediticia
- Verificación de cheques rechazados
- Evaluación de riesgo crediticio
- Modo mock para desarrollo

### 🚀 API REST
- Endpoints RESTful con FastAPI
- Documentación automática (Swagger/OpenAPI)
- Manejo de errores robusto
- Health checks para monitoreo

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.11+** - Lenguaje principal
- **FastAPI** - Framework web moderno y rápido
- **Uvicorn** - Servidor ASGI de alto rendimiento
- **Pydantic** - Validación de datos y configuración
- **python-telegram-bot** - Biblioteca para Telegram Bot API

### Servicios Externos
- **Google Gemini 2.5 LLM** - Procesamiento inteligente de imágenes con razonamiento avanzado (Flash/Pro)
- **BCRA API** - Validación crediticia (con modo mock)

### Infraestructura
- **Docker** - Containerización
- **Docker Compose** - Orquestación de servicios
- **Python-dotenv** - Gestión de variables de entorno

---

## 📁 Estructura del Proyecto

```
dataentrybot/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI application entry point
│       ├── api/                     # API routes
│       │   ├── __init__.py
│       │   └── routes.py            # API endpoints
│       ├── bot/                     # Telegram Bot
│       │   ├── __init__.py
│       │   └── bot.py               # Bot implementation
│       ├── core/                    # Core modules
│       │   ├── __init__.py
│       │   ├── config.py            # Configuration management
│       │   └── models.py            # Pydantic models
│       ├── services/                # External services
│       │   ├── __init__.py
│       │   ├── gemini_client.py    # Gemini API client
│       │   ├── bcra_client.py      # BCRA API client
│       │   └── cheques_processor.py # Cheque processing logic
│       └── utils/                   # Utilities
│           ├── __init__.py
│           └── file.py             # File handling utilities
├── docker/                          # Docker configuration
│   ├── Dockerfile                   # Docker image definition
│   └── docker-compose.yml           # Docker Compose config
├── scripts/                         # Utility scripts
│   └── run_bot.py                   # Bot runner script
├── .env.example                     # Environment variables template
├── .dockerignore                    # Docker ignore file
├── .gitignore                       # Git ignore file
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚀 Instalación

### Prerrequisitos

- **Python 3.11 o superior**
- **Docker y Docker Compose** (opcional, para despliegue con Docker)
- **Token de Bot de Telegram** ([Cómo obtenerlo](https://core.telegram.org/bots/tutorial#obtain-your-bot-token))
- **API Key de Google Gemini** ([Obtener aquí](https://makersuite.google.com/app/apikey))

### Opción 1: Instalación Local

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/sebastianjlopez/dataentrybot.git
   cd dataentrybot
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```
   
   Editar `.env` con tus credenciales:
   ```env
   TELEGRAM_BOT_TOKEN=tu_token_aqui
   GEMINI_API_KEY=tu_api_key_aqui
   GEMINI_MODEL=gemini-2.5-flash
   ```

### Opción 2: Instalación con Docker

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/sebastianjlopez/dataentrybot.git
   cd dataentrybot
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

3. **Construir y ejecutar con Docker Compose**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

---

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Requerido | Default |
|----------|-------------|-----------|---------|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | ✅ | - |
| `GEMINI_API_KEY` | API Key de Google Gemini | ✅ | - |
| `GEMINI_MODEL` | Modelo de Gemini a usar (gemini-2.5-flash o gemini-2.5-pro) | ❌ | `gemini-2.5-flash` |
| `API_HOST` | Host del servidor API | ❌ | `0.0.0.0` |
| `API_PORT` | Puerto del servidor API | ❌ | `8000` |
| `API_BASE_URL` | URL base de la API | ❌ | `http://localhost:8000` |
| `BCRA_API_URL` | URL de la API BCRA | ❌ | `https://api.bcra.gov.ar` |
| `BCRA_API_KEY` | API Key de BCRA | ❌ | - |
| `BCRA_MOCK_MODE` | Usar modo mock de BCRA | ❌ | `true` |
| `LOG_LEVEL` | Nivel de logging | ❌ | `INFO` |

### Configurar Bot de Telegram

1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Crea un nuevo bot con `/newbot`
3. Copia el token proporcionado
4. El bot está listo para usar - no requiere configuración adicional

---

## 📖 Uso

### Iniciar la API

**Local:**
```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Docker:**
```bash
docker-compose -f docker/docker-compose.yml up
```

La API estará disponible en `http://localhost:8000`
- Documentación Swagger: `http://localhost:8000/docs`
- Documentación ReDoc: `http://localhost:8000/redoc`

### Iniciar el Bot

**Local:**
```bash
python scripts/run_bot.py
```

**O directamente:**
```bash
python -m src.app.bot.bot
```

### Uso del Bot

1. **Iniciar conversación**
   - Busca tu bot en Telegram
   - Envía `/start` para comenzar

2. **Subir un documento**
   - Envía una foto o PDF al bot
   - El bot procesará automáticamente el documento

3. **Procesar un cheque**
   - Si el documento es un cheque, el bot:
     - Extraerá todos los campos relevantes
     - Validará con BCRA
     - Mostrará un resumen en formato comanda
   - Si hay múltiples cheques, se mostrarán uno por uno

---

## 🔌 API Endpoints

### `POST /api/upload`
Sube y procesa un archivo.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@cheque.jpg"
```

**Response:**
```json
{
  "success": true,
  "tipo_documento": "cheque",
  "data": {
    "cuit_librador": "20-12345678-9",
    "banco": "Banco Nación",
    "importe": 50000.0,
    ...
  },
  "filename": "cheque.jpg"
}
```

### `GET /api/health`
Health check del servicio.

**Response:**
```json
{
  "status": "healthy",
  "service": "data-entry-bot-api",
  "version": "1.0.0"
}
```

---

## 🏗️ Arquitectura

### Flujo de Procesamiento de Cheques

```
Usuario envía foto/PDF
    ↓
Bot recibe archivo
    ↓
API /upload procesa
    ↓
Detección automática de cheques
    ↓
Gemini 2.5 LLM analiza y extrae datos con razonamiento
    ↓
BCRA valida CUIT (si está disponible)
    ↓
Bot muestra resultados en formato comanda
    ↓
Múltiples cheques se muestran individualmente
```

### Componentes Principales

- **`TelegramBot`**: Maneja interacciones con usuarios
- **`GeminiClient`**: Procesa imágenes con Gemini 2.5 LLM usando razonamiento avanzado
- **`BCRAClient`**: Valida información crediticia
- **`ChequesProcessor`**: Orquesta el procesamiento de cheques
- **`FastAPI Routes`**: Endpoints REST para procesamiento

---

## 💻 Desarrollo

### Estructura de Módulos

- **`src/app/core/`**: Configuración y modelos base
- **`src/app/api/`**: Endpoints de la API
- **`src/app/bot/`**: Lógica del bot de Telegram
- **`src/app/services/`**: Clientes de servicios externos
- **`src/app/utils/`**: Utilidades compartidas

### Agregar Nuevos Tipos de Documentos

1. Crear modelo en `src/app/core/models.py`
2. Agregar procesador en `src/app/services/`
3. Actualizar `src/app/api/routes.py`
4. Actualizar `src/app/bot/bot.py` para manejar el nuevo tipo

### Ejecutar Tests

```bash
# Próximamente
pytest
```

---

## 🚢 Despliegue

### Despliegue con Docker

```bash
# Construir imagen
docker build -f docker/Dockerfile -t dataentrybot:latest .

# Ejecutar contenedor
docker run -d \
  --name dataentrybot \
  -p 8000:8000 \
  --env-file .env \
  dataentrybot:latest
```

### Despliegue en Render

El proyecto está optimizado para servicios cloud como Render:

✅ **Procesamiento en memoria**: Los archivos se procesan directamente en memoria, no se guardan en disco
✅ **Sin dependencias de sistema de archivos**: Compatible con sistemas de archivos efímeros
✅ **Configuración simple**: Solo necesitas las variables de entorno
✅ **Archivo render.yaml incluido**: Configuración lista para usar

**Opción 1: Usando render.yaml (Recomendado)**

1. **Conectar tu repositorio de GitHub** a Render
2. **Crear un nuevo Blueprint** en Render
3. **Seleccionar el archivo `render.yaml`** del repositorio
4. **Configurar variables de entorno** en Render Dashboard:
   - `TELEGRAM_BOT_TOKEN` (requerido)
   - `GEMINI_API_KEY` (requerido)
   - `GEMINI_MODEL` (opcional, default: `gemini-2.5-flash`)
   - `BCRA_MOCK_MODE=true` (o `false` si tienes API key real)
5. **Render creará automáticamente**:
   - Un Web Service para la API
   - Un Background Worker para el Bot

**Opción 2: Configuración Manual**

**Para el API Service (Web Service):**

1. **Crear un nuevo Web Service** en Render
2. **Conectar tu repositorio de GitHub**
3. **Configurar**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn src.app.main:app --host 0.0.0.0 --port $PORT`
4. **Variables de entorno**:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL` (opcional)
   - `BCRA_MOCK_MODE=true`
   - `LOG_LEVEL=INFO`

**Para el Bot Service (Background Worker):**

1. **Crear un nuevo Background Worker** en Render
2. **Conectar el mismo repositorio de GitHub**
3. **Configurar**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m src.app.bot`
4. **Variables de entorno**:
   - `TELEGRAM_BOT_TOKEN` (mismo que el API)
   - `GEMINI_API_KEY` (mismo que el API)
   - `GEMINI_MODEL` (opcional)
   - `API_BASE_URL` (URL del API Service de Render, ej: `https://dataentrybot-api.onrender.com`)
   - `BCRA_MOCK_MODE=true`
   - `LOG_LEVEL=INFO`

**Notas importantes:**

- Render asigna un puerto dinámico en `$PORT` para Web Services
- El API Service debe estar disponible públicamente para que el Bot pueda conectarse
- Usa la URL completa del API Service (con `https://`) en `API_BASE_URL` del Bot
- Los archivos se procesan en memoria, no se requiere almacenamiento persistente

### Despliegue en Producción (VPS/Dedicated)

1. **Configurar dominio y SSL**
2. **Configurar `API_BASE_URL`** con la URL de producción (con HTTPS)
3. **Configurar `BCRA_MOCK_MODE=false`** si usas API real
4. **Configurar logging** apropiado
5. **Usar un servidor WSGI/ASGI** como Gunicorn con Uvicorn workers
6. **Usar Docker Compose** para facilitar el despliegue (ver `docker/docker-compose.yml`)

---

## 🔧 Troubleshooting

### El bot no responde
- Verifica que el token de Telegram sea correcto
- Asegúrate de que el bot esté corriendo
- Revisa los logs para errores

### Error al procesar imágenes
- Verifica que la API Key de Gemini sea válida
- Revisa que la imagen sea válida y no esté corrupta
- Verifica los límites de la API de Gemini

### El bot no se conecta a la API
- Verifica que `API_BASE_URL` sea correcta (debe incluir `https://` en producción)
- Asegúrate de que la API esté accesible públicamente
- Revisa los logs del bot para ver errores de conexión

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es una demo profesional para roles administrativos y automatización de data entry.

---

## 👤 Autor

**Sebastián López**

- GitHub: [@sebastianjlopez](https://github.com/sebastianjlopez)
- Repositorio: [dataentrybot](https://github.com/sebastianjlopez/dataentrybot)

---

## 🔗 Enlaces Útiles

- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Documentación python-telegram-bot](https://python-telegram-bot.org/)
- [Google Gemini API](https://ai.google.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BCRA API](https://www.bcra.gob.ar/)

---

<div align="center">

**⭐ Si este proyecto te resultó útil, considera darle una estrella ⭐**

</div>
