"""
FastAPI routes for the Data Entry Bot API.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from src.app.core.models import ChequeData, DocumentData
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


# Global bot instance for webhook (lazy initialization)
_bot_instance = None
_bot_lock = None

async def get_bot_instance():
    """Get or create bot instance for webhook (async)."""
    global _bot_instance, _bot_lock
    if _bot_instance is None:
        from src.app.bot.bot import TelegramBot
        import asyncio
        
        if _bot_lock is None:
            _bot_lock = asyncio.Lock()
        
        async with _bot_lock:
            if _bot_instance is None:
                # Initialize in webhook mode (no Updater needed)
                _bot_instance = TelegramBot(webhook_mode=True)
                await _bot_instance.application.initialize()
                await _bot_instance.application.start()
                logger.info("Bot instance initialized for webhook")
    
    return _bot_instance


@router.post("/webhook")
async def telegram_webhook(request: dict):
    """
    Webhook endpoint for Telegram Bot updates.
    Telegram sends updates as JSON in the request body.
    """
    try:
        from telegram import Update
        
        # Get bot instance (will initialize if needed)
        bot = await get_bot_instance()
        
        # Process update
        update_obj = Update.de_json(request, bot.application.bot)
        if update_obj:
            await bot.application.process_update(update_obj)
        
        return {"ok": True}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return 200 even on error to avoid Telegram retrying
        return {"ok": False, "error": str(e)}


