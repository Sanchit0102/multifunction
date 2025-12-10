import os
import re
import asyncio
from pyrogram import Client
from aiohttp import web

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
PORT = int(os.environ.get("PORT", "10000"))

app = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)

import commands

# ---------------- WEBHOOK SERVER ----------------
async def telegram_webhook(request):
    update = await request.json()
    await app.process_update(update)
    return web.Response(text="ok")

async def on_startup(app_instance):
    webhook_url = f"{RENDER_EXTERNAL_URL}/telegram"
    await app.set_webhook(webhook_url)

async def main():
    await app.start()
    aio_app = web.Application()
    aio_app.router.add_post("/telegram", telegram_webhook)
    aio_app.on_startup.append(on_startup)

    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    print("Pyrogram webhook running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
