import os
import logging
import random
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application
import yt_dlp
import openai

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

# ইউটিউব গান
async def song_downloader(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ব্যবহার: /song <গানের নাম বা ইউটিউব লিঙ্ক>")
        return

    query = " ".join(context.args)
    message = await update.message.reply_text(f"🔎 '{query}' খোঁজা হচ্ছে...")

    ydl_opts = {
        'format': 'bestaudio/best', 'outtmpl': '%(title)s.%(ext)s', 'noplaylist': True,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'default_search': 'ytsearch',
    }

    filename = ""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info: info = info['entries'][0]
            
            file_size = info.get('filesize') or info.get('filesize_approx', 0)
            if file_size > 50 * 1024 * 1024: # 50 MB limit
                await message.edit_text("দুঃখিত, ফাইলটি 50MB এর চেয়ে বড় হওয়ায় পাঠানো সম্ভব নয়।")
                return

            await message.edit_text(f"📥 '{info['title']}' ডাউনলোড করা হচ্ছে...")
            ydl.download([info['webpage_url']])
            filename = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.mp3'

            await message.edit_text("📤 গানটি আপলোড করা হচ্ছে...")
            await context.bot.send_audio(
                chat_id=update.effective_chat.id, audio=open(filename, 'rb'),
                title=info.get('title'), duration=info.get('duration')
            )
            await message.delete()
    except Exception as e:
        logger.error(f"YouTube ডাউনলোড ব্যর্থ: {e}")
        await message.edit_text(f"দুঃখিত, গানটি ডাউনলোড করতে সমস্যা হয়েছে।")
    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

# AI চ্যাট
async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not openai.api_key:
        await update.message.reply_text("AI ফিচারটি কনফিগার করা হয়নি।")
        return
    if not context.args:
        await update.message.reply_text("ব্যবহার: /ask <আপনার প্রশ্ন>")
        return
    
    question = " ".join(context.args)
    await update.message.reply_chat_action('typing')
    
    try:
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are L1K40N, a friendly and helpful Telegram bot from Bangladesh."},
                {"role": "user", "content": question}
            ]
        )
        answer = response.choices[0].message.content
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        await update.message.reply_text("দুঃখিত, AI এর সাথে সংযোগ করতে সমস্যা হচ্ছে।")

# ফান কমান্ডস
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jokes = ["শিক্ষক: তোমরা সবাই এমন একটা কাজ এর নাম বল যা তোমরা ঘুমিয়েও করতে পারো। ছাত্র: স্বপ্ন দেখা স্যার।", "রোগী: ডাক্তার সাহেব, আমার সবকিছু দুটো করে দেখার রোগ হয়েছে। ডাক্তার: আচ্ছা, ঐ চেয়ারটায় আপনারা দুজন বসুন।"]
    await update.message.reply_text(random.choice(jokes))

def register_handlers(application: Application):
    application.add_handler(CommandHandler("song", song_downloader))
    application.add_handler(CommandHandler("ask", ask_ai))
    application.add_handler(CommandHandler("joke", joke))
