from dotenv import load_dotenv
load_dotenv()  # Load .env variables

import logging
import os
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- CONFIG ----------------
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID"))
BROCHURE_IMAGES = ["broucher1.jpg", "broucher2.jpg"]
WELCOME_FILE = "welcome_message.txt"

# ---------------- LOGGING ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- WELCOME HANDLER ----------------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    user_name = user.first_name or "User"
    chat_id = update.message.chat_id

    # 1️⃣ Notify Owner
    try:
        owner_text = (
            f"🔔 New user started the bot:\n"
            f"Name: {user.full_name}\n"
            f"Username: @{user.username or 'No username'}\n"
            f"User ID: {user.id}"
        )
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_text)
    except Exception as e:
        logger.error(f"Failed to send owner notification: {e}")

    # 2️⃣ Send Welcome Text with Buttons
    try:
        if not os.path.exists(WELCOME_FILE):
            await context.bot.send_message(chat_id=chat_id, text="Welcome! The bot is under maintenance.")
            logger.error(f"'{WELCOME_FILE}' not found.")
            return

        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            welcome_text = f.read().replace("{name}", user_name)

        keyboard = [
            [InlineKeyboardButton("✅ Visit Our Company Site", url="https://arthatech.net/")],
            [InlineKeyboardButton("✅ Chat Securely with Our Team", url="https://t.me/Artha_Fintech")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome text with buttons to {user.full_name} ({user.id})")

    except Exception as e:
        logger.error(f"Error sending welcome text: {e}")

    # 3️⃣ Send Brochure Images
    media_group = []
    for img_path in BROCHURE_IMAGES:
        if os.path.exists(img_path):
            try:
                media_group.append(InputMediaPhoto(media=open(img_path, "rb")))
            except Exception as e:
                logger.error(f"Error opening image {img_path}: {e}")
        else:
            logger.warning(f"Brochure image not found: '{img_path}'")

    if media_group:
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=media_group)
            logger.info(f"Sent {len(media_group)} brochure(s) to {user.full_name}")
        except Exception as e:
            logger.error(f"Error sending media group: {e}")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    logger.info("Starting bot with polling...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", send_welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_welcome))

    app.run_polling()
