"""
Telegram Bot implementation for Data Entry Bot.
Handles document processing and cheque validation.
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
from src.app.services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot for Data Entry automation."""
    
    def __init__(self, webhook_mode: bool = False):
        """
        Initialize Telegram Bot.
        
        Args:
            webhook_mode: If True, initializes for webhook mode (no Updater needed)
        """
        self.token = settings.telegram_bot_token
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        
        # Always use ApplicationBuilder - it handles both webhook and polling modes
        # The Updater is created lazily only when needed for polling
        builder = Application.builder().token(self.token)
        
        if webhook_mode:
            # For webhook mode, provide an update_queue to avoid Updater initialization
            from asyncio import Queue
            update_queue = Queue()
            self.application = builder.update_queue(update_queue).build()
        else:
            # Normal mode with Updater for polling
            self.application = builder.build()
        
        self.cheques_processor = ChequesProcessor()
        self.gemini_client = GeminiClient()
        
        # Register handlers
        self._register_handlers()
        
        logger.info(f"Telegram Bot initialized (webhook_mode={webhook_mode})")
    
    def _register_handlers(self):
        """Register all command and message handlers."""
        # Commands
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
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
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
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
        await update.message.reply_text(
            help_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        await update.message.reply_text(
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
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle image messages."""
        await update.message.reply_text(
            "📸 ¡Perfecto! Recibí tu imagen\n\n"
            "🔍 Estoy analizando el documento...\n"
            "⏳ Esto puede tardar unos segundos\n\n"
            "Por favor espera, estoy trabajando en ello... 💪",
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
            
            # Process as cheque
            await self._process_cheque(update, image_bytes, "image/jpeg")
        
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            await update.message.reply_text(
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
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF documents."""
        await update.message.reply_text(
            "📄 ¡Excelente! Recibí tu PDF\n\n"
            "🔍 Estoy analizando el documento...\n"
            "⏳ Esto puede tardar unos segundos\n\n"
            "Por favor espera, estoy trabajando en ello... 💪",
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
    
    async def _process_cheque(self, update: Update, file_data: bytes, mime_type: str):
        """Process cheque document."""
        try:
            cheques = await self.cheques_processor.detect_and_process_cheques(
                file_data,
                mime_type
            )
            
            if not cheques:
                await update.message.reply_text(
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
                message = self._format_cheque_message(cheque, idx + 1, len(cheques))
                await update.message.reply_text(
                    message,
                    parse_mode=ParseMode.MARKDOWN
                )
        
        except Exception as e:
            logger.error(f"Error processing cheque: {str(e)}")
            await update.message.reply_text(
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
    
    def _format_cheque_message(self, cheque, index: int, total: int) -> str:
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
    
    async def run(self, use_webhook: bool = False, webhook_url: Optional[str] = None):
        """Start the bot."""
        logger.info("Starting Telegram Bot...")
        await self.application.initialize()
        await self.application.start()
        
        if use_webhook and webhook_url:
            # Use webhook mode
            await self.application.bot.set_webhook(url=webhook_url)
            logger.info(f"Telegram Bot webhook set to: {webhook_url}")
        else:
            # Use polling mode
            await self.application.updater.start_polling()
            logger.info("Telegram Bot is running (polling mode)")
    
    async def stop(self):
        """Stop the bot."""
        logger.info("Stopping Telegram Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram Bot stopped")
