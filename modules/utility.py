import logging
import requests
import wikipediaapi
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, Application

logger = logging.getLogger(__name__)

# উইকিপিডিয়া
wiki = wikipediaapi.Wikipedia('L1K40N Bot (likan@example.com)', 'bn') # বাংলা উইকির জন্য 'bn'

async def wiki_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ব্যবহার: /wiki <অনুসন্ধানের বিষয়>")
        return
    query = " ".join(context.args)
    page = wiki.page(query)
    if not page.exists():
        await update.message.reply_text(f"'{query}' বিষয়ে কোনো তথ্য পাওয়া যায়নি।")
        return
    
    summary = f"<b>{page.title}</b>\n\n{page.summary[:500]}..."
    await update.message.reply_text(summary, parse_mode='HTML')

# URL শর্টনার
async def shorten_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ব্যবহার: /shorten <আপনার বড় লিঙ্ক>")
        return
    long_url = context.args[0]
    try:
        response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}")
        if response.status_code == 200:
            await update.message.reply_text(f"আপনার ছোট লিঙ্ক: {response.text}")
        else:
            await update.message.reply_text("লিঙ্কটি ছোট করতে সমস্যা হয়েছে।")
    except Exception as e:
        logger.error(f"URL Shortener error: {e}")
        await update.message.reply_text("একটি ত্রুটি ঘটেছে।")

def register_handlers(application: Application):
    application.add_handler(CommandHandler("wiki", wiki_search))
    application.add_handler(CommandHandler("shorten", shorten_url))
