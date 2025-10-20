import os
import logging
import threading
from dotenv import load_dotenv
from flask import Flask
from telegram.ext import Application, CommandHandler

# .env ফাইল থেকে এনভায়রনমেন্ট ভেরিয়েবল লোড করা
load_dotenv()

# মডিউল থেকে হ্যান্ডলার ইম্পোর্ট করা
import database as db
from modules.entertainment import register_handlers as register_entertainment_handlers
from modules.moderation import register_handlers as register_moderation_handlers
from modules.utility import register_handlers as register_utility_handlers

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask Keep-Alive
PORT = int(os.environ.get('PORT', 8080))
app = Flask(__name__)
@app.route('/')
def hello(): return "L1K40N is alive!"
def run_flask(): app.run(host='0.0.0.0', port=PORT)

def main() -> None:
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        logger.error("BOT_TOKEN পাওয়া যায়নি! .env ফাইলটি পরীক্ষা করুন।")
        return

    # ডাটাবেস ইনিশিয়ালাইজ করা
    db.init_db()

    # Flask সার্ভার নতুন থ্রেডে চালু করা
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    application = Application.builder().token(TOKEN).build()

    # সাধারণ কমান্ড
    application.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("L1K40N حاضر! আপনার সেবায় নিয়োজিত।")))

    # বিভিন্ন মডিউল থেকে হ্যান্ডলার রেজিস্টার করা
    register_moderation_handlers(application)
    register_entertainment_handlers(application)
    register_utility_handlers(application)

    logger.info("L1K40N is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
