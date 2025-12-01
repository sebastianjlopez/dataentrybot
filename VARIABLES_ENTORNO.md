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

# BCRA API
BCRA_API_URL=https://api.bcra.gob.ar

# Logging
LOG_LEVEL=INFO
# Opciones: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🟢 Variables Opcionales para Funcionalidades Adicionales

### AFIP Padrón A13 (Comando /padron)

Para usar el comando `/padron` que consulta el padrón AFIP, necesitas estas credenciales:

```env
# AFIP SDK Credentials (obtenidas desde https://app.afipsdk.com/)
AFIP_TOKEN=tu_token_afip_aqui
AFIP_SIGN=tu_sign_afip_aqui
AFIP_CUIT_REPRESENTADA=tu_cuit_representada_aqui
AFIP_ENVIRONMENT=dev
# Opciones: dev (desarrollo) o prod (producción)
```

**Nota:** Si no configuras estas variables, el comando `/padron` mostrará un mensaje de error indicando que las credenciales no están configuradas.

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
BCRA_API_URL=https://api.bcra.gob.ar
LOG_LEVEL=INFO

# ============================================
# AFIP (Opcional - para comando /padron)
# ============================================
AFIP_TOKEN=tu_token_afip
AFIP_SIGN=tu_sign_afip
AFIP_CUIT_REPRESENTADA=20-12345678-9
AFIP_ENVIRONMENT=dev
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

### AFIP SDK Credentials
1. Ve a [AFIP SDK](https://app.afipsdk.com/)
2. Crea una cuenta o inicia sesión
3. Obtén tu `token`, `sign` y `cuitRepresentada`
4. Configúralos en las variables de entorno

## ⚠️ Importante

- **Nunca subas el archivo `.env` a Git** (ya está en `.gitignore`)
- Usa `.env.example` como plantilla si es necesario
- En producción (Render, etc.), configura las variables en el panel de configuración del servicio

