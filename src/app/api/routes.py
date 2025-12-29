"""
FastAPI routes for the Data Entry Bot API.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
import io
import re
from typing import Optional
from telegram.constants import ParseMode
from src.app.core.models import ChequeData, DocumentData
from src.app.core.config import settings
from src.app.services.cheques_processor import ChequesProcessor
from src.app.services.gemini_client import GeminiClient
from src.app.utils.file import get_file_mime_type

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize processors
cheques_processor = ChequesProcessor()
gemini_client = GeminiClient()


@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file (image, PDF, or cheque).
    
    Detects if the file is a cheque and processes it accordingly.
    Returns structured data extracted from the document.
    """
    try:
        # Read file data
        file_data = await file.read()
        filename = file.filename or "uploaded_file"
        mime_type = get_file_mime_type(filename)
        
        logger.info(f"Processing upload: {filename} ({mime_type})")
        
        # Process file directly from memory (no need to save to disk)
        # This works better in cloud environments like Render where filesystem is ephemeral
        
        # Always try to detect cheques first (Gemini will determine if there are any)
        logger.info("Attempting to detect cheques in document...")
        cheques_list = await cheques_processor.detect_and_process_cheques(file_data, mime_type, filename)
        
        if cheques_list and len(cheques_list) > 0:
            # Found cheques - return them
            logger.info(f"Found {len(cheques_list)} cheque(s)")
            return {
                "success": True,
                "tipo_documento": "cheques",
                "cantidad": len(cheques_list),
                "data": [cheque.model_dump() for cheque in cheques_list],
                "filename": filename
            }
        else:
            # Process as general document
            logger.info("Processing as general document...")
            result = await gemini_client.process_image(file_data, mime_type)
            
            document_data = DocumentData(
                tipo_documento="documento",
                contenido=result.get("extracted_text", ""),
                datos_estructurados={},
                metadata={
                    "filename": filename,
                    "mime_type": mime_type
                }
            )
            
            return {
                "success": result.get("success", False),
                "tipo_documento": "documento",
                "data": document_data.model_dump(),
                "filename": filename
            }
            
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "data-entry-bot-api",
        "version": "1.0.0"
    }


# Global bot handlers for webhook (lazy initialization)
_bot_handlers = None
_bot_lock = None

async def get_bot_handlers():
    """Get or create bot handlers for webhook (async) - without Application to avoid Updater issues."""
    global _bot_handlers, _bot_lock
    if _bot_handlers is None:
        from telegram import Bot
        from src.app.services.cheques_processor import ChequesProcessor
        import asyncio
        
        if _bot_lock is None:
            _bot_lock = asyncio.Lock()
        
        async with _bot_lock:
            if _bot_handlers is None:
                # Create bot and handlers directly without Application/Updater
                bot = Bot(token=settings.telegram_bot_token)
                cheques_processor = ChequesProcessor()
                
                _bot_handlers = {
                    "bot": bot,
                    "cheques_processor": cheques_processor
                }
                logger.info("Bot handlers initialized for webhook")
    
    return _bot_handlers


@router.post("/webhook")
async def telegram_webhook(request: dict):
    """
    Webhook endpoint for Telegram Bot updates.
    Telegram sends updates as JSON in the request body.
    Process updates directly without Application/Updater to avoid Python 3.13 compatibility issues.
    """
    try:
        from telegram import Update
        from telegram.constants import ParseMode
        import io
        
        # Get bot handlers
        handlers = await get_bot_handlers()
        bot = handlers["bot"]
        cheques_processor = handlers["cheques_processor"]
        
        # Parse update
        update_obj = Update.de_json(request, bot)
        if not update_obj:
            return {"ok": True}
        
        # Process update manually
        if update_obj.message:
            message = update_obj.message
            text = message.text or ""
            
            # Handle commands
            if text.startswith("/start"):
                welcome_message = (
                    "👋 ¡Hola! Soy tu *Asistente de Cheques*\n\n"
                    "✨ *¿Qué puedo hacer por ti?*\n"
                    "📸 Tomo una foto de tu cheque y automáticamente:\n"
                    "   ✓ Extraigo todos los datos (banco, importe, fechas, etc.)\n"
                    "   ✓ Valido la información con BCRA\n"
                    "   ✓ Te muestro todo organizado y fácil de leer\n\n"
                    "🚀 *¿Cómo empezar?*\n"
                    "Es súper fácil, solo sigue estos pasos:\n\n"
                    "1️⃣ Toma una foto clara de tu cheque\n"
                    "   (o envía un PDF si lo tienes digital)\n"
                    "2️⃣ Envíamela aquí en el chat\n"
                    "3️⃣ ¡Listo! Te mostraré toda la información\n\n"
                    "📱 *Formatos que acepto:*\n"
                    "• 📷 Fotos (JPG, PNG)\n"
                    "• 📄 PDFs\n\n"
                    "💡 *Tip:* Asegúrate de que la foto esté bien iluminada y se vea todo el cheque completo.\n\n"
                    "¿Listo para probar? ¡Envía tu primer cheque! 📸"
                )
                await message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
            
            elif text.startswith("/help"):
                help_message = (
                    "📚 *Guía de Uso - Paso a Paso*\n\n"
                    "🎯 *¿Qué necesitas hacer?*\n"
                    "Solo enviarme una foto o PDF de un cheque y yo haré el resto.\n\n"
                    "📝 *Instrucciones detalladas:*\n\n"
                    "**Paso 1: Prepara tu cheque**\n"
                    "• Asegúrate de que el cheque esté completo\n"
                    "• Verifica que se vean todos los datos importantes\n"
                    "• Si es una foto, que esté bien iluminada\n\n"
                    "**Paso 2: Envíame la imagen**\n"
                    "• Toca el ícono de 📎 (clip) en Telegram\n"
                    "• Selecciona 'Foto' o 'Archivo'\n"
                    "• Elige tu cheque y envíalo\n\n"
                    "**Paso 3: Espera el resultado**\n"
                    "• Te avisaré cuando esté procesando\n"
                    "• En segundos tendrás toda la información\n"
                    "• Verás datos del banco, importe, fechas, etc.\n\n"
                    "📊 *¿Qué información obtendrás?*\n"
                    "• 🏦 Banco emisor\n"
                    "• 💰 Importe del cheque\n"
                    "• 📅 Fechas (emisión y pago)\n"
                    "• 🔢 Número de cheque\n"
                    "• 🆔 CUIT del librador\n"
                    "• 🏛️ Estado BCRA (si está disponible)\n"
                    "• ⚠️ Alertas de riesgo crediticio\n\n"
                    "❓ *¿Tienes problemas?*\n"
                    "• Si no detecta el cheque, verifica que la imagen sea clara\n"
                    "• Asegúrate de que el cheque esté completo en la foto\n"
                    "• Intenta con mejor iluminación si es necesario\n\n"
                    "💬 *Comandos disponibles:*\n"
                    "• `/start` - Ver mensaje de bienvenida\n"
                    "• `/help` - Ver esta ayuda\n\n"
                    "¿Alguna otra duda? ¡Pregúntame! 😊"
                )
                await message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
            
            elif message.photo or (message.document and message.document.mime_type and "image" in message.document.mime_type):
                # Handle images
                await _handle_image_webhook(bot, message, cheques_processor)
            
            elif message.document and message.document.mime_type == "application/pdf":
                # Handle PDFs
                await _handle_document_webhook(bot, message, cheques_processor)
            
            elif text:
                # Handle text
                await message.reply_text(
                    "👋 ¡Hola!\n\n"
                    "Para procesar un cheque, necesito que me envíes una *foto* o un *PDF* del cheque.\n\n"
                    "📸 *¿Cómo hacerlo?*\n"
                    "1. Toca el ícono de 📎 (clip) en la parte inferior\n"
                    "2. Selecciona 'Foto' o 'Archivo'\n"
                    "3. Elige tu cheque y envíalo\n\n"
                    "💡 *Tip:* Asegúrate de que la foto esté clara y se vea todo el cheque completo.\n\n"
                    "¿Necesitas más ayuda? Escribe `/help` para ver la guía completa. 😊",
                    parse_mode=ParseMode.MARKDOWN
                )
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return 200 even on error to avoid Telegram retrying
        return {"ok": False, "error": str(e)}


async def _handle_image_webhook(bot, message, cheques_processor):
    """Handle image messages in webhook mode."""
    try:
        await message.reply_text(
            "📸 ¡Perfecto! Recibí tu imagen\n\n"
            "🔍 Estoy analizando el documento...\n"
            "⏳ Esto puede tardar unos segundos\n\n"
            "Por favor espera, estoy trabajando en ello... 💪",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Get photo file
        if message.photo:
            photo = message.photo[-1]
        else:
            photo = message.document
        
        file = await bot.get_file(photo.file_id)
        
        # Download image
        image_data = io.BytesIO()
        await file.download_to_memory(image_data)
        image_bytes = image_data.getvalue()
        
        # Process as cheque
        await _process_cheque_webhook(bot, message, cheques_processor, image_bytes, "image/jpeg")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        await message.reply_text(
            "😔 *Ups, algo salió mal*\n\n"
            "No pude procesar tu imagen en este momento.\n\n"
            "🔄 *¿Qué puedes hacer?*\n"
            "• Intenta enviar la imagen nuevamente\n"
            "• Verifica que la imagen no esté corrupta\n"
            "• Si el problema persiste, intenta con otra foto\n\n"
            "Si el error continúa, por favor contacta al soporte.\n\n"
            "¡Lo siento por las molestias! 😊",
            parse_mode=ParseMode.MARKDOWN
        )


async def _handle_document_webhook(bot, message, cheques_processor):
    """Handle PDF documents in webhook mode."""
    try:
        await message.reply_text(
            "📄 ¡Excelente! Recibí tu PDF\n\n"
            "🔍 Estoy analizando el documento...\n"
            "⏳ Esto puede tardar unos segundos\n\n"
            "Por favor espera, estoy trabajando en ello... 💪",
            parse_mode=ParseMode.MARKDOWN
        )
        
        file = await bot.get_file(message.document.file_id)
        
        # Download PDF
        pdf_data = io.BytesIO()
        await file.download_to_memory(pdf_data)
        pdf_bytes = pdf_data.getvalue()
        
        await _process_cheque_webhook(bot, message, cheques_processor, pdf_bytes, "application/pdf")
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        await message.reply_text(
            "😔 *Ups, algo salió mal*\n\n"
            "No pude procesar tu PDF en este momento.\n\n"
            "🔄 *¿Qué puedes hacer?*\n"
            "• Intenta enviar el PDF nuevamente\n"
            "• Verifica que el archivo no esté corrupto\n"
            "• Si el problema persiste, intenta convertir el PDF a imagen\n\n"
            "Si el error continúa, por favor contacta al soporte.\n\n"
            "¡Lo siento por las molestias! 😊",
            parse_mode=ParseMode.MARKDOWN
        )


async def _process_cheque_webhook(bot, message, cheques_processor, file_data: bytes, mime_type: str):
    """Process cheque document in webhook mode."""
    try:
        cheques = await cheques_processor.detect_and_process_cheques(file_data, mime_type)
        
        if not cheques:
            await message.reply_text(
                "😔 *No pude encontrar un cheque en tu imagen*\n\n"
                "🔍 *¿Qué puede estar pasando?*\n\n"
                "**Posibles causas:**\n"
                "• La imagen no es lo suficientemente clara\n"
                "• El cheque no está completo en la foto\n"
                "• La iluminación es muy baja o hay sombras\n"
                "• El documento no es un cheque\n\n"
                "💡 *Sugerencias para mejorar:*\n"
                "1. Asegúrate de que el cheque esté completo en la foto\n"
                "2. Toma la foto con buena iluminación\n"
                "3. Evita sombras sobre el cheque\n"
                "4. Verifica que la imagen no esté borrosa\n"
                "5. Intenta acercarte un poco más al cheque\n\n"
                "🔄 *¿Qué hacer ahora?*\n"
                "Puedes intentar enviar otra foto con mejor calidad. ¡Estoy aquí para ayudarte! 😊",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Send each cheque as formatted message
        for idx, cheque in enumerate(cheques):
            message_text = _format_cheque_message(cheque, idx + 1, len(cheques))
            await message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error processing cheque: {str(e)}")
        await message.reply_text(
            "😔 *Ups, algo salió mal*\n\n"
            "Encontré un cheque pero no pude extraer toda la información.\n\n"
            "🔄 *¿Qué puedes hacer?*\n"
            "• Intenta enviar otra foto con mejor calidad\n"
            "• Asegúrate de que el cheque esté completo y claro\n"
            "• Verifica que la iluminación sea buena\n\n"
            "Si el problema persiste, por favor contacta al soporte.\n\n"
            "¡Lo siento por las molestias! 😊",
            parse_mode=ParseMode.MARKDOWN
        )


def _format_cheque_message(cheque, index: int, total: int) -> str:
    """Format cheque data as message."""
    message = "✅ *¡Listo! Aquí está la información de tu cheque*\n\n"
    
    if total > 1:
        message += f"📋 *Cheque {index} de {total}*\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "📊 *INFORMACIÓN DEL CHEQUE*\n"
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    message += f"🏦 *Banco:* {cheque.banco or 'No disponible'}\n"
    message += f"💰 *Importe:* ${cheque.importe:,.2f}\n"
    message += f"📅 *Fecha de Emisión:* {cheque.fecha_emision or 'No disponible'}\n"
    message += f"📅 *Fecha de Pago:* {cheque.fecha_pago or 'No disponible'}\n"
    message += f"🔢 *Número de Cheque:* {cheque.numero_cheque or 'No disponible'}\n"
    message += f"🆔 *CUIT del Librador:* {cheque.cuit_librador or 'No disponible'}\n\n"
    
    # BCRA Information section
    has_bcra_info = False
    bcra_section = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    bcra_section += "🏛️ *VALIDACIÓN BCRA*\n"
    bcra_section += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if cheque.estado_bcra:
        bcra_section += f"✅ *Estado:* {cheque.estado_bcra}\n"
        has_bcra_info = True
    
    if cheque.cheques_rechazados > 0:
        bcra_section += f"⚠️ *Cheques Rechazados:* {cheque.cheques_rechazados}\n"
        has_bcra_info = True
    
    if cheque.riesgo_crediticio:
        bcra_section += f"📊 *Riesgo Crediticio:* {cheque.riesgo_crediticio}\n"
        has_bcra_info = True
    
    if has_bcra_info:
        message += bcra_section
    else:
        message += "ℹ️ *Nota:* No se pudo obtener información adicional del BCRA en este momento.\n\n"
    
    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "✨ *Procesamiento completado*\n\n"
    message += "¿Necesitas procesar otro cheque? ¡Solo envíame otra foto! 📸"
    
    return message


