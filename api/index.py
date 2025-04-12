import os
import tempfile
import requests
import asyncio
from flask import Flask, request
from telegram import Bot, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from utils import split_file, human_readable_size

TOKEN = os.environ.get("BOT_TOKEN", "8022651374:AAGpeoK6a7nLs-ecBTIjGEoLZMHD3MQAGik")
bot = Bot(token=TOKEN)

app = Flask(__name__)

application = Application.builder().token(TOKEN).build()

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return "ok"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a TeraBox link and I’ll send the file!")

def progress_bar(done, total):
    percent = int((done / total) * 100)
    bar = "#" * (percent // 10) + "-" * (10 - percent // 10)
    return f"Progress: [{bar}] {percent}%"

async def download_file_with_progress(url, filepath, update: Update):
    r = requests.get(url, stream=True)
    total = int(r.headers.get('content-length', 0))
    done = 0
    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                done += len(chunk)
                if done % (20 * 1024 * 1024) == 0:
                    await update.message.reply_text(progress_bar(done, total))
    return filepath

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "terabox" not in text:
        await update.message.reply_text("Please send a valid TeraBox link.")
        return

    await update.message.reply_text("Fetching download link...")
    try:
        res = requests.get(f"https://terabox-pro-api.vercel.app/api?link={text}").json()
        if not res.get("success"):
            await update.message.reply_text("Failed to get the download link.")
            return

        url = res["download_url"]
        filename = res.get("filename", "terabox_file")
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, filename)

        await update.message.reply_text(f"Downloading `{filename}`...")

        await download_file_with_progress(url, filepath, update)

        file_size = os.path.getsize(filepath)
        if file_size > 2 * 1024 * 1024 * 1024:
            await update.message.reply_text("File > 2GB. Splitting...")
            parts = split_file(filepath)
            for part in parts:
                await bot.send_document(chat_id=update.effective_chat.id, document=open(part, 'rb'), filename=os.path.basename(part))
                os.remove(part)
        else:
            await bot.send_document(chat_id=update.effective_chat.id, document=open(filepath, 'rb'), filename=filename)

        os.remove(filepath)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Something went wrong!")
        await update.message.reply_text("Internal error occurred.")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))