import os
import asyncio
from dotenv import load_dotenv
from flask import app
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from telegram.ext import CallbackQueryHandler # ត្រូវប្រាកដថាមាន CallbackQueryHandler នេះ
from handlers.messages import handle_normal_message, handle_callback_query # 👈 បន្ថែម ", handle_callback_query" ត្រង់នេះ

from handlers.commands import (
    init_db,
    start_command,
    help_command,
    share_location_command,
    scan_location_command,
    track_command,
)
from handlers.messages import handle_normal_message

# 🔥 ហៅការទាញយកការកំណត់ (Settings) ពី config មកប្រើ
from config import settings as SETTINGS

# 🔥 បន្ថែមបណ្ណាល័យ aiohttp ដើម្បីបង្កើត Web Server សម្រាប់បោក Render
from aiohttp import web

# ប្រើប្រាស់ BOT_TOKEN ដែលបានផ្ទៀងផ្ទាត់រួចជាស្រេចពី config
BOT_TOKEN = SETTINGS.BOT_TOKEN

# មុខងារស្វាគមន៍ពេល Render មកពិនិត្យមើល Port (Health Check)
async def handle_health_check(request):
    return web.Response(text="Bot is running successfully with Online Database!")

async def main():
    # ----------------------------------------------------
    # ១. បង្កើត និងរត់ Web Server ស្ងាត់ៗនៅពីក្រោយខ្នង
    # ----------------------------------------------------
    app_web = web.Application()
    app_web.router.add_get('/', handle_health_check)
    
    
    # ចាប់យក Port ពី Render (Render ផ្តល់ឱ្យតាមរយៈ Environment Variable ឈ្មោះ PORT)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    # បើកដំណើរការ Web Server ចោល
    asyncio.create_task(site.start())
    print(f"📡 Fake Web Server started on port {port}")

    # ----------------------------------------------------
    # ២. បើកដំណើរការ Telegram Bot ទម្រង់ Polling ធម្មតា
    # ----------------------------------------------------
    print("🤖 Telegram Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Initialize DB schema before starting the bot
    try:
        init_db()
    except Exception as err:
        print(f"⚠️ DB initialization warning: {err}")
        print("The bot will continue starting, but database actions may fail until the connection is restored.")

    # បន្ថែម Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("share_location", share_location_command))
    application.add_handler(CommandHandler("scan_location", scan_location_command))
    application.add_handler(CommandHandler("track", track_command))
    # application.add_handler(MessageHandler(filters.TEXT | filters.CONTACT | filters.LOCATION, handle_normal_message))
    # 📝 កែតម្រូវជួរនេះនៅក្នុង main.py
    application.add_handler(MessageHandler((filters.TEXT | filters.CONTACT | filters.LOCATION) & ~filters.COMMAND, handle_normal_message))
    
    # ជួរនេះត្រឹមត្រូវហើយ ទុកដដែលបាទ
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # រត់ Bot រហូត
    async with application:
        await application.initialize()
        await application.start()
        print("🚀 Bot is running successfully with Online Database!")
        await application.updater.start_polling()
        
        # រក្សាឱ្យកម្មវិធីរត់ទាំងពីរព្រមគ្នាដោយមិនបិទ
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # រត់មុខងារ main តាមទម្រង់ Asyncio
    asyncio.run(main())