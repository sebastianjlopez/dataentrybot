"""
Telegram Bot implementation for Data Entry Bot.
Handles document processing, cheque validation, and AFIP padrón queries.
"""
import logging
import re
from typing import Optional
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
import io

from src.app.core.config import settings
from src.app.services.cheques_processor import ChequesProcessor
from src.app.services.afip_client import AFIPClient
from src.app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot for Data Entry automation."""
    
    def __init__(self):
        """Initialize Telegram Bot."""
        self.token = settings.telegram_bot_token
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        
        self.application = Application.builder().token(self.token).build()
        self.cheques_processor = ChequesProcessor()
        self.afip_client = AFIPClient()
        self.gemini_client = GeminiClient()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Telegram Bot initialized")
    
    def _register_handlers(self):
        """Register all command and message handlers."""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("padron", self.padron_command))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.PHOTO | filters.Document.IMAGE, self.handle_image)
        )
        self.application.add_handler(
            MessageHandler(filters.Document.PDF, self.handle_document)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text)
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
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
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
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
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def padron_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /padron command."""
        if not context.args:
            await update.message.reply_text(
                "❌ Por favor proporciona un CUIT.\n\n"
                "Ejemplo: `/padron 30-69163759-6`\n\n"
                "O envía una foto con el CUIT visible.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        cuit = " ".join(context.args)
        await self._process_padron_query(update, cuit)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - try to extract CUIT."""
        text = update.message.text.strip()
        
        # Try to extract CUIT from text
        cuit_pattern = r'\b\d{2}[-]?\d{8}[-]?\d{1}\b'
        match = re.search(cuit_pattern, text)
        
        if match:
            cuit = match.group(0)
            # Normalize CUIT format
            digits = re.sub(r'\D', '', cuit)
            if len(digits) == 11:
                cuit = f"{digits[:2]}-{digits[2:10]}-{digits[10]}"
                await update.message.reply_text(
                    f"🔍 CUIT detectado: {cuit}\n\nConsultando padrón AFIP...",
                    parse_mode=ParseMode.MARKDOWN
                )
                await self._process_padron_query(update, cuit)
            else:
                await update.message.reply_text(
                    "❌ CUIT inválido. Debe tener 11 dígitos.\n\n"
                    "Ejemplo: `30-69163759-6`",
                    parse_mode=ParseMode.MARKDOWN
                )
        else:
            await update.message.reply_text(
                "💡 No se detectó un CUIT en el mensaje.\n\n"
                "Envía:\n"
                "• Un CUIT (ej: `30-69163759-6`)\n"
                "• Una foto con CUIT visible\n"
                "• O usa `/padron <CUIT>`",
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages."""
        await update.message.reply_text(
            "📸 Procesando imagen...\n\n"
            "Buscando CUIT y/o cheques...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Get photo file
            photo = update.message.photo[-1]  # Get highest resolution
            file = await context.bot.get_file(photo.file_id)
            
            # Download image
            image_data = io.BytesIO()
            await file.download_to_memory(image_data)
            image_bytes = image_data.getvalue()
            
            # Try to extract CUIT first
            cuit = await self._extract_cuit_from_image(image_bytes)
            
            if cuit:
                await update.message.reply_text(
                    f"✅ CUIT detectado: `{cuit}`\n\nConsultando padrón AFIP...",
                    parse_mode=ParseMode.MARKDOWN
                )
                await self._process_padron_query(update, cuit)
            else:
                # Try to process as cheque
                await update.message.reply_text(
                    "🔍 No se detectó CUIT. Procesando como cheque...",
                    parse_mode=ParseMode.MARKDOWN
                )
                await self._process_cheque(update, image_bytes, "image/jpeg")
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            await update.message.reply_text(
                f"❌ Error al procesar la imagen: {str(e)}"
            )
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF documents."""
        await update.message.reply_text(
            "📄 Procesando PDF...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            file = await context.bot.get_file(update.message.document.file_id)
            
            # Download PDF
            pdf_data = io.BytesIO()
            await file.download_to_memory(pdf_data)
            pdf_bytes = pdf_data.getvalue()
            
            # Try to process as cheque
            await self._process_cheque(update, pdf_bytes, "application/pdf")
        
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            await update.message.reply_text(
                f"❌ Error al procesar el documento: {str(e)}"
            )
    
    async def _extract_cuit_from_image(self, image_data: bytes) -> Optional[str]:
        """Extract CUIT from image using Gemini."""
        try:
            prompt = """
            Extrae el CUIT de esta imagen. El CUIT tiene formato XX-XXXXXXXX-X (11 dígitos con guiones).
            
            Responde SOLO con el CUIT en formato XX-XXXXXXXX-X, sin texto adicional.
            Si no encuentras un CUIT, responde solo con "NO".
            """
            
            result = await self.gemini_client.process_image(image_data, "image/jpeg", prompt)
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
    
    async def _process_padron_query(self, update: Update, cuit: str):
        """Process AFIP padrón query."""
        try:
            result = await self.afip_client.get_taxpayer_details(cuit)
            formatted = self.afip_client.format_taxpayer_info(result)
            
            await update.message.reply_text(
                formatted,
                parse_mode=ParseMode.MARKDOWN
            )
        
        except Exception as e:
            logger.error(f"Error querying AFIP padrón: {str(e)}")
            await update.message.reply_text(
                f"❌ Error al consultar el padrón AFIP: {str(e)}"
            )
    
    async def _process_cheque(self, update: Update, file_data: bytes, mime_type: str):
        """Process cheque document."""
        try:
            cheques = await self.cheques_processor.detect_and_process_cheques(
                file_data,
                mime_type
            )
            
            if not cheques:
                await update.message.reply_text(
                    "❌ No se detectaron cheques en el documento.\n\n"
                    "Asegúrate de que la imagen sea clara y contenga un cheque válido."
                )
                return
            
            # Send each cheque as formatted message
            for idx, cheque in enumerate(cheques):
                message = self._format_cheque_message(cheque, idx + 1, len(cheques))
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error processing cheque: {str(e)}")
            await update.message.reply_text(
                f"❌ Error al procesar el cheque: {str(e)}"
            )
    
    def _format_cheque_message(self, cheque, index: int, total: int) -> str:
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
    
    async def run(self):
        """Start the bot."""
        logger.info("Starting Telegram Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram Bot is running")
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping Telegram Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram Bot stopped")
