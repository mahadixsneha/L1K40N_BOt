import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes, Application, filters
from telegram.constants import ParseMode
import database as db

logger = logging.getLogger(__name__)

# Helper
async def is_user_admin(chat_id, user_id, context: ContextTypes.DEFAULT_TYPE):
    admins = await context.bot.get_chat_administrators(chat_id)
    return any(admin.user.id == user_id for admin in admins)

# নতুন সদস্যকে স্বাগতম
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot: continue
        
        await context.bot.restrict_chat_member(
            update.message.chat_id, member.id, permissions=ChatPermissions(can_send_messages=False)
        )
        keyboard = [[InlineKeyboardButton("✅ আমি মানুষ, ভেরিফাই করুন", callback_data=f"verify_{member.id}")]]
        welcome_msg = db.get_setting(update.message.chat_id, "welcome_message") or "স্বাগতম {firstname}!"
        
        await update.message.reply_text(
            welcome_msg.format(firstname=member.first_name, groupname=update.message.chat.title),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ভেরিফিকেশন বাটন
async def button_verifier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id_to_verify = int(query.data.split("_")[1])
    if query.from_user.id == user_id_to_verify:
        await context.bot.restrict_chat_member(
            query.message.chat_id, user_id_to_verify,
            permissions=ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        )
        await query.edit_message_text(f"✅ {query.from_user.first_name} সফলভাবে ভেরিফায়েড!")
    else:
        await query.answer("দুঃখিত, এই বাটনটি আপনার জন্য নয়।", show_alert=True)

# অ্যাডমিন কমান্ড: warn
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_user_admin(update.message.chat.id, update.message.from_user.id, context):
        await update.message.reply_text("এই কমান্ডটি শুধুমাত্র অ্যাডমিনদের জন্য।")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("কোনো ব্যবহারকারীকে ওয়ার্ন করতে তার মেসেজে রিপ্লাই করুন।")
        return

    user_to_warn = update.message.reply_to_message.from_user
    warnings = db.add_warning(update.message.chat_id, user_to_warn.id)
    
    await update.message.reply_text(f"{user_to_warn.mention_html()} কে সতর্ক করা হয়েছে। মোট সতর্কতা: {warnings}/3", parse_mode=ParseMode.HTML)

    if warnings >= 3:
        try:
            await context.bot.ban_chat_member(update.message.chat_id, user_to_warn.id)
            await update.message.reply_text(f"{user_to_warn.mention_html()} ৩টি সতর্কতা পাওয়ায় তাকে ব্যান করা হয়েছে।", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"ব্যান করতে সমস্যা হয়েছে: {e}")

def register_handlers(application: Application):
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, greet_new_member))
    application.add_handler(CallbackQueryHandler(button_verifier, pattern=r"^verify_"))
    application.add_handler(CommandHandler("warn", warn_user))
