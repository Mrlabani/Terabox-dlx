import os
import requests
import tempfile
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, filters, CommandHandler
from telegram.constants import ParseMode
from utils import split_file, human_readable_size

TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = Bot(token=TOKEN)
app = Flask(__name__)

dispatcher = Dispatcher(bot=bot, update_queue=None, workers=4)

@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

def start(update, context):
    update.message.reply_text("Send me a TeraBox link and I’ll fetch + send the file!")

def progress_text(done, total):
    percent = int((done / total) * 100)
    bar = "#" * (percent // 10) + "-" * (10 - percent // 10)
    return f"Progress: [{bar}] {percent}%"

def download_file_with_progress(url, filepath, update):
    r = requests.get(url, stream=True)
    total = int(r.headers.get('content-length', 0))
    done = 0

    with open(filepath, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                done += len(chunk)
                if done % (10 * 1024 * 1024) == 0:
                    update.message.reply_text(progress_text(done, total))
    return filepath

def handle_link(update, context):
    text = update.message.text.strip()
    if "terabox" not in text:
        update.message.reply_text("Please send a valid TeraBox link.")
        return

    update.message.reply_text("Fetching download link...")
    try:
        res = requests.get(f"https://terabox-pro-api.vercel.app/api?link={text}").json()
        if not res.get("success"):
            update.message.reply_text("Failed to get the download link.")
            return

        url = res["download_url"]
        filename = res.get("filename", "terabox_file")
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, filename)

        update.message.reply_text(f"Downloading `{filename}`...")
        download_file_with_progress(url, filepath, update)

        file_size = os.path.getsize(filepath)
        if file_size > 2 * 1024 * 1024 * 1024:
            update.message.reply_text(f"File is larger than 2GB, splitting...")
            parts = split_file(filepath)
            for part in parts:
                bot.send_document(update.effective_chat.id, document=open(part, 'rb'), filename=os.path.basename(part))
                os.remove(part)
        else:
            bot.send_document(update.effective_chat.id, document=open(filepath, 'rb'), filename=filename)

        os.remove(filepath)

    except Exception as e:
        update.message.reply_text(f"Error: {e}")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
