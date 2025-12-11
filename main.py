from urllib import request
from fastapi import FastAPI, Request
import asyncio
import os

# CRITICAL: Clear ALL proxy env vars before any other imports
# This prevents telebot from passing proxies to OpenAI client
for var in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(var, None)

# Patch requests.Session to not use proxies by default
import requests
_original_session = requests.Session

class PatchedSession(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trust_env = False  # Disable env proxy detection

requests.Session = PatchedSession

# Also patch OpenAI to remove proxies kwarg if passed
def patch_openai():
    """Monkeypatch OpenAI client to reject proxies kwarg"""
    try:
        from openai import OpenAI as OriginalOpenAI
        
        class PatchedOpenAI(OriginalOpenAI):
            def __init__(self, *args, **kwargs):
                # Remove proxies kwarg if present
                kwargs.pop('proxies', None)
                super().__init__(*args, **kwargs)
        
        # Replace in sys.modules
        import openai
        openai.OpenAI = PatchedOpenAI
    except:
        pass

patch_openai()

from config import WEBHOOK_URL
from bot import bot, types

app = FastAPI()

@app.get("/")
async def root():
    """Health check endpoint for Render"""
    return {"status": "ok", "service": "cooking-bot"}

@app.on_event('startup')
async def start_app():
    try:
        # Try to set webhook with retry logic for rate limiting
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await bot.set_webhook(WEBHOOK_URL+'/webhook')
                print(f"✅ Webhook set successfully: {WEBHOOK_URL}/webhook")
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                    print(f"⚠️  Rate limited. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                elif attempt == max_retries - 1:
                    print(f"⚠️  Could not set webhook (rate limited). Webhook may already be set: {e}")
                else:
                    raise
    except Exception as e:
        print(f"⚠️  Webhook setup failed: {e}")

@app.post("/webhook")
async def handle_webhook(request: Request):
    json_data = await request.json()
    update = types.Update.de_json(json_data)
    await bot.process_new_updates([update])
    return "OK"