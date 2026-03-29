import logging
import yt_dlp
import os
import requests
from flask import Flask, request
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os

# 🔐 TOKEN (safe from environment)
TOKEN = os.getenv("TOKEN")

# 🌐 URL (Replit / Render)
URL = "https://your-app-url.replit.app"

# 🤖 TELEGRAM API
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

# 🌐 Flask App
app = Flask(__name__)

# ================= KEEP ALIVE =================
@app.route('/')
def home():
    return "🚀 Bot is Running"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    Thread(target=run).start()

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

# ================= MUSIC DATA =================
queue = []
history = []
is_playing = False

smart_map = {
    "sad": "sad hindi songs",
    "romantic": "romantic bollywood songs",
    "party": "party songs hindi",
    "bhakti": "bhakti songs",
    "lofi": "lofi chill songs",
    "workout": "gym workout songs"
}

# ================= MOVIE DATA =================
movie_store = {}

API_KEYS = ["3e8227fb","c88010c8","a05a97f","5cda3d54"]
key_index = 0

def get_api_key():
    global key_index
    key = API_KEYS[key_index]
    key_index = (key_index + 1) % len(API_KEYS)
    return key

def search_omdb(name):
    for _ in range(len(API_KEYS)):
        key = get_api_key()
        try:
            res = requests.get(f"https://www.omdbapi.com/?apikey={key}&s={name}")
            data = res.json()

            if data.get("Response") == "True":
                return data["Search"]
        except:
            pass
    return []

# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *ULTIMATE BOT*\n\n"
        "🎵 /play song\n"
        "🎬 /movie name\n"
        "⏭ /skip\n"
        "📜 /history",
        parse_mode="Markdown"
    )

# ================= MUSIC =================
async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_playing

    if not context.args:
        await update.message.reply_text("❌ Song name likh")
        return

    query = " ".join(context.args).lower()

    for key in smart_map:
        if key in query:
            query = smart_map[key]

    queue.append(query)
    await update.message.reply_text(f"➕ Added: {query}")

    if not is_playing:
        await play_next(update, context)

async def play_next(update, context):
    global is_playing

    if not queue:
        is_playing = False
        return

    is_playing = True
    query = queue.pop(0)

    msg = await update.message.reply_text(f"🎶 Searching: {query}")

    try:
        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)
            video = info['entries'][0]

            title = video['title']
            url = video['webpage_url']

        await msg.edit_text(f"⬇️ Downloading: {title[:40]}")

        with yt_dlp.YoutubeDL({'format': 'bestaudio', 'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        history.append(title)

        with open(file_path, 'rb') as f:
            await update.message.reply_audio(audio=f, title=title)

        os.remove(file_path)

    except Exception as e:
        print(e)
        await update.message.reply_text("❌ Error आया")

    await play_next(update, context)

async def skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏭ Skipped")
    await play_next(update, context)

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not history:
        await update.message.reply_text("📭 Empty")
        return

    text = "\n".join(history[-10:])
    await update.message.reply_text(f"📜 History:\n{text}")

# ================= MOVIE =================
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Movie name likh")
        return

    name = " ".join(context.args)
    await update.message.reply_text("🔍 Searching...")

    movies = search_omdb(name)

    if not movies:
        await update.message.reply_text("❌ Not found")
        return

    m = movies[0]

    title = m["Title"]
    poster = m["Poster"]
    imdb = f"https://www.imdb.com/title/{m['imdbID']}"

    await update.message.reply_photo(
        photo=poster,
        caption=f"🎬 {title}\n⭐ {imdb}"
    )

# ================= MAIN =================
def main():
    app_bot = ApplicationBuilder().token(TOKEN).build()

    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CommandHandler("play", play))
    app_bot.add_handler(CommandHandler("skip", skip))
    app_bot.add_handler(CommandHandler("history", show_history))
    app_bot.add_handler(CommandHandler("movie", movie))

    print("🚀 Bot Running...")
    app_bot.run_polling()

# ================= RUN =================
if __name__ == "__main__":
    keep_alive()
    main()
