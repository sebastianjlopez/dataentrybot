# 📋 Variables de Entorno - Data Entry Bot

Este documento lista todas las variables de entorno necesarias para el proyecto.

## 🔴 Variables Requeridas

Estas variables son **obligatorias** para que el bot funcione:

```env
# Telegram Bot Token (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aqui

# Gemini API Key (obtenido de Google AI Studio)
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
```

## 🟡 Variables Opcionales con Defaults

Estas variables tienen valores por defecto, pero puedes cambiarlas:

```env
# Gemini Model
GEMINI_MODEL=gemini-2.5-flash
# Opciones: gemini-2.5-flash (rápido) o gemini-2.5-pro (más potente)

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000
WEBHOOK_URL=https://dataentrybot.onrender.com/api/webhook
# URL completa del webhook de Telegram (solo necesario si quieres auto-configuración)

# BCRA API
BCRA_API_URL=https://api.bcra.gob.ar

# Logging
LOG_LEVEL=INFO
# Opciones: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 📝 Ejemplo de archivo .env completo

```env
# ============================================
# REQUERIDAS
# ============================================
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# ============================================
# OPCIONALES CON DEFAULTS
# ============================================
GEMINI_MODEL=gemini-2.5-flash
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000
WEBHOOK_URL=https://dataentrybot.onrender.com/api/webhook
# URL completa del webhook (solo necesario para auto-configuración en Render)

# BCRA API
BCRA_API_URL=https://api.bcra.gob.ar

# Logging
LOG_LEVEL=INFO
```

## 🔍 Cómo obtener las credenciales

### Telegram Bot Token
1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Envía `/newbot` y sigue las instrucciones
3. Copia el token que te proporciona

### Gemini API Key
1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API key
3. Copia la key generada

## 🌐 Variables para Render/Producción

Para Render, configura estas variables en el panel de configuración:

**Variables Requeridas:**
- `TELEGRAM_BOT_TOKEN` - Tu token del bot
- `GEMINI_API_KEY` - Tu API key de Gemini

**Variables Recomendadas para Webhook:**
- `WEBHOOK_URL` - URL completa del webhook (ej: `https://dataentrybot.onrender.com/api/webhook`)
  - Si configuras esta variable, el webhook se configurará automáticamente al iniciar
  - Si no la configuras, puedes configurar el webhook manualmente usando la API de Telegram

**Variables Opcionales:**
- `GEMINI_MODEL` - Modelo a usar (default: `gemini-2.5-flash`)
- `BCRA_API_URL` - URL de la API BCRA (default: `https://api.bcra.gob.ar`)
- `LOG_LEVEL` - Nivel de logging (default: `INFO`)

## ⚠️ Importante

- **Nunca subas el archivo `.env` a Git** (ya está en `.gitignore`)
- Usa `.env.example` como plantilla si es necesario
- En producción (Render, etc.), configura las variables en el panel de configuración del servicio
- **Para Render:** Configura `WEBHOOK_URL` con la URL completa de tu servicio (ej: `https://dataentrybot.onrender.com/api/webhook`)

