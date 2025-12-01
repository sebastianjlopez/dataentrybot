#!/usr/bin/env python3
"""Script to check Telegram webhook status."""
import requests

TOKEN = "8565998519:AAFqoL-Zd8iGE7dgK__92hKlqsoe_AmzNFE"

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

