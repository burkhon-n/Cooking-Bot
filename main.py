from urllib import request
from fastapi import FastAPI, Request
from bot import bot, types
from config import WEBHOOK_URL
import asyncio

app = FastAPI()

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