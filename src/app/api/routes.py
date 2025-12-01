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
        from src.app.services.afip_client import AFIPClient
        from src.app.services.gemini_client import GeminiClient
        import asyncio
        
        if _bot_lock is None:
            _bot_lock = asyncio.Lock()
        
        async with _bot_lock:
            if _bot_handlers is None:
                # Create bot and handlers directly without Application/Updater
                bot = Bot(token=settings.telegram_bot_token)
                cheques_processor = ChequesProcessor()
                afip_client = AFIPClient()
                gemini_client = GeminiClient()
                
                _bot_handlers = {
                    "bot": bot,
                    "cheques_processor": cheques_processor,
                    "afip_client": afip_client,
                    "gemini_client": gemini_client
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
        afip_client = handlers["afip_client"]
        gemini_client = handlers["gemini_client"]
        
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
                    "🤖 *Bienvenido al Data Entry Bot*\n\n"
                    "Puedo ayudarte con:\n"
                    "• Procesar cheques y extraer datos\n"
                    "• Consultar padrón AFIP A13\n"
                    "• Validar información crediticia BCRA\n\n"
                    "📋 *Comandos disponibles:*\n"
                    "/start - Mostrar este mensaje\n"
                    "/help - Ver ayuda detallada\n"
                    "/padron <CUIT> - Consultar padrón AFIP\n\n"
                    "💡 *Tipos de archivos soportados:*\n"
                    "• Imágenes (JPG, PNG)\n"
                    "• PDFs\n"
                    "• Texto con CUIT\n\n"
                    "Envía una foto o PDF para comenzar!"
                )
                await message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
            
            elif text.startswith("/help"):
                help_message = (
                    "📖 *Ayuda - Data Entry Bot*\n\n"
                    "🔹 *Comandos:*\n"
                    "• `/start` - Mensaje de bienvenida\n"
                    "• `/help` - Mostrar esta ayuda\n"
                    "• `/padron <CUIT>` - Consultar padrón AFIP A13\n\n"
                    "🔹 *Uso del Padrón:*\n"
                    "• `/padron 30-69163759-6` - Consulta por CUIT\n"
                    "• Envía una foto con CUIT visible\n"
                    "• El bot extraerá el CUIT automáticamente\n\n"
                    "🔹 *Procesamiento de Cheques:*\n"
                    "• Envía una foto o PDF de un cheque\n"
                    "• El bot extraerá todos los datos\n"
                    "• Validará automáticamente con BCRA\n\n"
                    "🔹 *Información del Padrón:*\n"
                    "El bot mostrará:\n"
                    "• Razón Social\n"
                    "• Domicilio Fiscal\n"
                    "• Provincia (alerta Convenio Multilateral)\n"
                    "• Condición de IVA\n"
                    "• Actividades"
                )
                await message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
            
            elif text.startswith("/padron"):
                # Extract CUIT from command
                parts = text.split()
                if len(parts) > 1:
                    cuit = " ".join(parts[1:])
                    await _process_padron_query(bot, message, afip_client, cuit)
                else:
                    await message.reply_text(
                        "❌ Por favor proporciona un CUIT.\n\n"
                        "Ejemplo: `/padron 30-69163759-6`\n\n"
                        "O envía una foto con el CUIT visible.",
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            elif message.photo or (message.document and message.document.mime_type and "image" in message.document.mime_type):
                # Handle images
                await _handle_image_webhook(bot, message, cheques_processor, afip_client, gemini_client)
            
            elif message.document and message.document.mime_type == "application/pdf":
                # Handle PDFs
                await _handle_document_webhook(bot, message, cheques_processor)
            
            elif text:
                # Handle text (try to extract CUIT)
                import re
                cuit_pattern = r'\b\d{2}[-]?\d{8}[-]?\d{1}\b'
                match = re.search(cuit_pattern, text)
                if match:
                    cuit = match.group(0)
                    digits = re.sub(r'\D', '', cuit)
                    if len(digits) == 11:
                        cuit = f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
                        await message.reply_text(
                            f"🔍 CUIT detectado: {cuit}\n\nConsultando padrón AFIP...",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        await _process_padron_query(bot, message, afip_client, cuit)
                    else:
                        await message.reply_text(
                            "❌ CUIT inválido. Debe tener 11 dígitos.\n\n"
                            "Ejemplo: `30-69163759-6`",
                            parse_mode=ParseMode.MARKDOWN
                        )
                else:
                    await message.reply_text(
                        "💡 No se detectó un CUIT en el mensaje.\n\n"
                        "Envía:\n"
                        "• Un CUIT (ej: `30-69163759-6`)\n"
                        "• Una foto con CUIT visible\n"
                        "• O usa `/padron <CUIT>`",
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return 200 even on error to avoid Telegram retrying
        return {"ok": False, "error": str(e)}


async def _process_padron_query(bot, message, afip_client, cuit: str):
    """Process AFIP padrón query."""
    try:
        result = await afip_client.get_taxpayer_details(cuit)
        formatted = afip_client.format_taxpayer_info(result)
        await message.reply_text(formatted, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error querying AFIP padrón: {str(e)}")
        await message.reply_text(f"❌ Error al consultar el padrón AFIP: {str(e)}")


async def _handle_image_webhook(bot, message, cheques_processor, afip_client, gemini_client):
    """Handle image messages in webhook mode."""
    try:
        await message.reply_text(
            "📸 Procesando imagen...\n\nBuscando CUIT y/o cheques...",
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
        
        # Try to extract CUIT first
        cuit = await _extract_cuit_from_image(gemini_client, image_bytes)
        
        if cuit:
            await message.reply_text(
                f"✅ CUIT detectado: `{cuit}`\n\nConsultando padrón AFIP...",
                parse_mode=ParseMode.MARKDOWN
            )
            await _process_padron_query(bot, message, afip_client, cuit)
        else:
            # Try to process as cheque
            await message.reply_text(
                "🔍 No se detectó CUIT. Procesando como cheque...",
                parse_mode=ParseMode.MARKDOWN
            )
            await _process_cheque_webhook(bot, message, cheques_processor, image_bytes, "image/jpeg")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        await message.reply_text(f"❌ Error al procesar la imagen: {str(e)}")


async def _handle_document_webhook(bot, message, cheques_processor):
    """Handle PDF documents in webhook mode."""
    try:
        await message.reply_text("📄 Procesando PDF...", parse_mode=ParseMode.MARKDOWN)
        
        file = await bot.get_file(message.document.file_id)
        
        # Download PDF
        pdf_data = io.BytesIO()
        await file.download_to_memory(pdf_data)
        pdf_bytes = pdf_data.getvalue()
        
        await _process_cheque_webhook(bot, message, cheques_processor, pdf_bytes, "application/pdf")
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        await message.reply_text(f"❌ Error al procesar el documento: {str(e)}")


async def _extract_cuit_from_image(gemini_client, image_data: bytes) -> Optional[str]:
    """Extract CUIT from image using Gemini."""
    try:
        prompt = """
        Extrae el CUIT de esta imagen. El CUIT tiene formato XX-XXXXXXXX-X (11 dígitos con guiones).
        
        Responde SOLO con el CUIT en formato XX-XXXXXXXX-X, sin texto adicional.
        Si no encuentras un CUIT, responde solo con "NO".
        """
        
        result = await gemini_client.process_image(image_data, "image/jpeg", prompt)
        text = result.get("extracted_text", "").strip()
        
        # Try to find CUIT in response
        cuit_pattern = r'\b\d{2}[-]?\d{8}[-]?\d{1}\b'
        match = re.search(cuit_pattern, text)
        
        if match:
            cuit = match.group(0)
            # Normalize format
            digits = re.sub(r'\D', '', cuit)
            if len(digits) == 11:
                return f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
        
        return None
    except Exception as e:
        logger.error(f"Error extracting CUIT from image: {str(e)}")
        return None


async def _process_cheque_webhook(bot, message, cheques_processor, file_data: bytes, mime_type: str):
    """Process cheque document in webhook mode."""
    try:
        cheques = await cheques_processor.detect_and_process_cheques(file_data, mime_type)
        
        if not cheques:
            await message.reply_text(
                "❌ No se detectaron cheques en el documento.\n\n"
                "Asegúrate de que la imagen sea clara y contenga un cheque válido."
            )
            return
        
        # Send each cheque as formatted message
        for idx, cheque in enumerate(cheques):
            message_text = _format_cheque_message(cheque, idx + 1, len(cheques))
            await message.reply_text(message_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error processing cheque: {str(e)}")
        await message.reply_text(f"❌ Error al procesar el cheque: {str(e)}")


def _format_cheque_message(cheque, index: int, total: int) -> str:
    """Format cheque data as message."""
    message = f"📋 *CHEQUE {index}/{total}*\n\n"
    message += f"🏦 *Banco:* {cheque.banco or 'N/A'}\n"
    message += f"💰 *Importe:* ${cheque.importe:,.2f}\n"
    message += f"📅 *Fecha Emisión:* {cheque.fecha_emision or 'N/A'}\n"
    message += f"📅 *Fecha Pago:* {cheque.fecha_pago or 'N/A'}\n"
    message += f"🔢 *Número:* {cheque.numero_cheque or 'N/A'}\n"
    message += f"🆔 *CUIT Librador:* {cheque.cuit_librador or 'N/A'}\n\n"
    
    if cheque.estado_bcra:
        message += f"🏛️ *Estado BCRA:* {cheque.estado_bcra}\n"
    if cheque.cheques_rechazados > 0:
        message += f"⚠️ *Cheques Rechazados:* {cheque.cheques_rechazados}\n"
    if cheque.riesgo_crediticio:
        message += f"📊 *Riesgo Crediticio:* {cheque.riesgo_crediticio}\n"
    
    return message


