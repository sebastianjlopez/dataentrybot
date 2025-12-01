"""
Telegram Bot implementation using python-telegram-bot.
Handles user interactions and integrates with the FastAPI backend.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
import json
from src.app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot for Data Entry automation."""
    
    def __init__(self):
        """Initialize Telegram bot."""
        self.token = settings.telegram_bot_token
        self.webapp_url = settings.telegram_webapp_url
        self.api_url = f"{settings.api_base_url}/api"
        self.application = None
        logger.info("Telegram bot initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = """
🤖 *Bienvenido al Bot de Data Entry Automatizado*

Este bot te ayuda a:
• Subir y procesar documentos (fotos, PDFs)
• Leer cheques con OCR
• Validar información crediticia (BCRA)
• Editar y confirmar datos en la Mini App

*Comandos disponibles:*
/start - Mostrar este mensaje
/help - Ayuda y guía de uso

*¿Cómo usar?*
1. Envía una foto o PDF
2. El bot procesará el documento
3. Revisa y edita los datos en la Mini App
4. Confirma para procesar

¡Envía un documento para comenzar!
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
📖 *Guía de Uso del Bot*

*Procesamiento de Documentos:*
• Envía cualquier imagen o PDF
• El bot detectará automáticamente si es un cheque
• Los cheques se procesan con validación BCRA

*Procesamiento de Cheques:*
• Extrae: CUIT, Banco, Fechas, Importe, Número
• Valida situación crediticia del librador
• Muestra cheques rechazados y riesgo crediticio

*Mini App:*
• Abre la Mini App para revisar y editar datos
• Todos los campos son editables
• Confirma cuando estés listo

*Soporte:*
Para más información, contacta al administrador.
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads (photos, PDFs, etc.)."""
        try:
            message = update.message
            
            # Get file
            if message.photo:
                file = await context.bot.get_file(message.photo[-1].file_id)
            elif message.document:
                file = await context.bot.get_file(message.document.file_id)
            else:
                await message.reply_text("❌ Por favor envía una imagen o PDF válido.")
                return
            
            # Download file
            file_data = await file.download_as_bytearray()
            filename = file.file_path.split('/')[-1] if file.file_path else "document.jpg"
            
            # Notify user
            processing_msg = await message.reply_text("⏳ Procesando documento...")
            
            # Send to API
            async with aiohttp.ClientSession() as session:
                form_data = aiohttp.FormData()
                form_data.add_field('file', file_data, filename=filename, content_type='application/octet-stream')
                
                async with session.post(
                    f"{self.api_url}/upload",
                    data=form_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Delete processing message
                        await processing_msg.delete()
                        
                        # Process result
                        if result.get("success"):
                            tipo = result.get("tipo_documento", "documento")
                            data = result.get("data", {})
                            
                            if tipo == "cheque":
                                await self._handle_cheque_result(message, data)
                            else:
                                await self._handle_document_result(message, data, result)
                        else:
                            await message.reply_text("❌ Error al procesar el documento. Intenta nuevamente.")
                    else:
                        await processing_msg.delete()
                        await message.reply_text("❌ Error al procesar el documento.")
                        
        except Exception as e:
            logger.error(f"Error handling document: {str(e)}")
            await update.message.reply_text("❌ Ocurrió un error. Por favor intenta nuevamente.")
    
    async def _handle_cheque_result(self, message, cheque_data: dict):
        """Handle cheque processing result."""
        cuit = cheque_data.get("cuit_librador", "N/A")
        banco = cheque_data.get("banco", "N/A")
        importe = cheque_data.get("importe", 0)
        estado_bcra = cheque_data.get("estado_bcra", "N/A")
        cheques_rechazados = cheque_data.get("cheques_rechazados", 0)
        riesgo = cheque_data.get("riesgo_crediticio", "N/A")
        
        # Build summary message
        summary = f"""
✅ *Cheque procesado correctamente*

*Datos extraídos:*
• CUIT Librador: `{cuit}`
• Banco: {banco}
• Importe: ${importe:,.2f}
• Número: {cheque_data.get("numero_cheque", "N/A")}
• Fecha Emisión: {cheque_data.get("fecha_emision", "N/A")}
• Fecha Pago: {cheque_data.get("fecha_pago", "N/A")}

*Validación BCRA:*
• Estado: {estado_bcra}
• Cheques Rechazados: {cheques_rechazados}
• Riesgo Crediticio: {riesgo}

¿Querés revisar y editar los datos?
        """
        
        # Create Mini App button
        keyboard = [
            [InlineKeyboardButton(
                "📝 Revisar y Editar",
                web_app=WebAppInfo(url=f"{self.webapp_url}?data={json.dumps(cheque_data)}")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _handle_document_result(self, message, document_data: dict, result: dict):
        """Handle general document processing result."""
        contenido = document_data.get("contenido", "")[:500]  # First 500 chars
        
        summary = f"""
✅ *Documento procesado*

*Contenido extraído:*
{contenido}...

¿Querés revisar y editar los datos?
        """
        
        # Create Mini App button
        keyboard = [
            [InlineKeyboardButton(
                "📝 Revisar y Editar",
                web_app=WebAppInfo(url=f"{self.webapp_url}?data={json.dumps(document_data)}")
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            summary,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    def setup_handlers(self):
        """Setup bot command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(
                filters.PHOTO | filters.Document.ALL,
                self.handle_document
            )
        )
    
    async def run(self):
        """Run the bot."""
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start bot
        logger.info("Starting Telegram bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Telegram bot is running...")
    
    async def stop(self):
        """Stop the bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            logger.info("Telegram bot stopped")


