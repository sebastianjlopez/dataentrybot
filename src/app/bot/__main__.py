#!/usr/bin/env python3
"""
Entry point to run the Telegram bot as a module.
Usage: python -m src.app.bot.bot
"""
import asyncio
import logging
from src.app.bot.bot import TelegramBot
from src.app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    bot = TelegramBot()
    try:
        await bot.run()
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        await bot.stop()
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        await bot.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())





