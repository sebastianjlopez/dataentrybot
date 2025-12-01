#!/usr/bin/env python3
"""Script to check Telegram webhook status."""
import requests
import os
import sys
from pathlib import Path

# Add parent directory to path to import settings
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.core.config import settings

TOKEN = settings.telegram_bot_token

if not TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN no está configurado")
    print("   Configura la variable de entorno TELEGRAM_BOT_TOKEN")
    sys.exit(1)

response = requests.get(f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo")
info = response.json()

if info.get("ok"):
    result = info["result"]
    print(f"✅ Webhook configurado:")
    print(f"   URL: {result['url']}")
    print(f"   Updates pendientes: {result['pending_update_count']}")
    if result.get('last_error_message'):
        print(f"   ⚠️  Último error: {result['last_error_message']}")
        print(f"   Fecha error: {result.get('last_error_date', 'N/A')}")
    else:
        print(f"   ✅ Sin errores")
else:
    print(f"❌ Error: {info}")

