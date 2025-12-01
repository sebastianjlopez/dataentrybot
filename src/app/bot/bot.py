"""
Telegram Bot implementation using python-telegram-bot.
Handles user interactions and integrates with the FastAPI backend.
"""
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import aiohttp
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
• Leer cheques con inteligencia artificial
• Validar información crediticia (BCRA)
• Mostrar resultados estructurados

*Comandos disponibles:*
/start - Mostrar este mensaje
/help - Ayuda y guía de uso

*¿Cómo usar?*
1. Envía una foto o PDF
2. El bot procesará el documento automáticamente
3. Recibirás los resultados extraídos en formato comanda

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
• El bot detectará automáticamente si contiene cheques
• Los cheques se procesan con validación BCRA

*Procesamiento de Cheques:*
• Extrae automáticamente: CUIT, Banco, Fechas, Importe, Número
• Valida situación crediticia del librador con BCRA
• Muestra cheques rechazados y riesgo crediticio
• Si hay múltiples cheques, muestra uno por uno

*Resultados:*
• Los resultados se muestran en formato comanda estructurado
• Cada cheque se muestra con todos sus datos extraídos
• No se requiere confirmación ni edición

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
                            
                            if tipo == "cheques" or (tipo == "cheque" and isinstance(data, list)):
                                # Multiple cheques or single cheque in list format
                                cheques_list = data if isinstance(data, list) else [data]
                                cantidad = result.get("cantidad", len(cheques_list))
                                
                                # Send summary message first
                                await message.reply_text(
                                    f"✅ *Se encontraron {cantidad} cheque(s) en el documento*",
                                    parse_mode='Markdown'
                                )
                                
                                # Send formatted messages for each cheque (tipo comanda)
                                for idx, cheque_data in enumerate(cheques_list, 1):
                                    await self._send_cheque_comanda(
                                        message, 
                                        cheque_data, 
                                        numero=idx, 
                                        total=cantidad
                                    )
                            elif tipo == "cheque":
                                # Single cheque (old format)
                                await self._send_cheque_comanda(message, data)
                            else:
                                # General document - just show extracted content
                                contenido = data.get("contenido", "")[:1000]
                                await message.reply_text(
                                    f"✅ *Documento procesado*\n\n`{contenido[:800]}...`",
                                    parse_mode='Markdown'
                                )
                        else:
                            await message.reply_text("❌ Error al procesar el documento. Intenta nuevamente.")
                    else:
                        await processing_msg.delete()
                        await message.reply_text("❌ Error al procesar el documento.")
                        
        except Exception as e:
            logger.error(f"Error handling document: {str(e)}")
            await update.message.reply_text("❌ Ocurrió un error. Por favor intenta nuevamente.")
    
    async def _send_cheque_comanda(self, message, cheque_data: dict, numero: int = 1, total: int = 1):
        """
        Send cheque data in comanda format (structured, readable format).
        No editing options, just display the extracted data.
        """
        cuit = cheque_data.get("cuit_librador", "N/A")
        banco = cheque_data.get("banco", "N/A")
        importe = cheque_data.get("importe", 0)
        estado_bcra = cheque_data.get("estado_bcra", "N/A")
        cheques_rechazados = cheque_data.get("cheques_rechazados", 0)
        riesgo = cheque_data.get("riesgo_crediticio", "N/A")
        numero_cheque = cheque_data.get("numero_cheque", "N/A")
        fecha_emision = cheque_data.get("fecha_emision", "N/A")
        fecha_pago = cheque_data.get("fecha_pago", "N/A")
        cbu_beneficiario = cheque_data.get("cbu_beneficiario") or "N/A"
        
        # Format as comanda (structured receipt-like format)
        # Use plain text to avoid Markdown parsing errors
        header = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n" \
                 f"📋 CHEQUE {numero}/{total}\n" \
                 f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        comanda = f"""
{header}

🏦 BANCO: {banco}
🔢 NÚMERO: {numero_cheque}
💰 IMPORTE: ${importe:,.2f}

👤 LIBRADOR:
   CUIT: {cuit}

📅 FECHAS:
   Emisión: {fecha_emision}
   Vencimiento: {fecha_pago}

🏦 VALIDACIÓN BCRA:
   Estado: {estado_bcra}
   Rechazados: {cheques_rechazados}
   Riesgo: {riesgo}

💳 BENEFICIARIO:
   CBU/CUIT: {cbu_beneficiario}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        
        # Always use plain text to avoid Markdown parsing errors
        await message.reply_text(
            comanda,
            parse_mode=None
        )
    
    def _format_cheque_from_json(self, cheque_json: dict) -> dict:
        """
        Format cheque data from Gemini JSON response.
        Extracts and normalizes all fields.
        
        Args:
            cheque_json: Raw cheque data from Gemini
            
        Returns:
            Formatted cheque data dictionary
        """
        return {
            "cuit_librador": cheque_json.get("cuit_librador", ""),
            "banco": cheque_json.get("banco", ""),
            "fecha_emision": cheque_json.get("fecha_emision", ""),
            "fecha_pago": cheque_json.get("fecha_pago", ""),
            "importe": cheque_json.get("importe", 0),
            "numero_cheque": cheque_json.get("numero_cheque", ""),
            "cbu_beneficiario": cheque_json.get("cbu_beneficiario") or None
        }
    
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


