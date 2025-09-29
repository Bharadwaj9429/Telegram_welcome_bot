import logging
import asyncio
import os
from telegram import Update, InputMediaPhoto, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from telegram.constants import ParseMode

# ---------------- CONFIG ----------------
# --- IMPORTANT: REPLACE WITH YOUR ACTUAL BOT TOKEN AND CHAT ID ---
BOT_TOKEN = "8481829632:AAFsm2fFM3WClyAB5cUqUbSN5vpuU_XV8mw"
OWNER_CHAT_ID = 8388091191
BROCHURE_IMAGES = ["broucher1.jpg", "broucher2.jpg"]
WELCOME_FILE = "welcome_message.txt"

# ---------------- LOGGING ----------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ---------------- UTILITY: CLEAR CONFLICTS ----------------
async def clear_conflicts(application: Application):
    """Clears pending updates from Telegram's servers before starting the bot."""
    try:
        await application.bot.delete_webhook()
        updates = await application.bot.get_updates(offset=-1)
        if updates:
            last_update_id = updates[-1].update_id
            await application.bot.get_updates(offset=last_update_id + 1)
        logger.info("Cleared previous bot updates to avoid conflicts.")
    except TelegramError as e:
        logger.error(f"Error clearing conflicts: {e}")


# ---------------- HANDLER: SEND WELCOME ----------------
async def send_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command and new user messages.
    Sends a welcome message with inline buttons, notifies the owner, and then sends an image carousel.
    """
    if not update.message:
        return

    user = update.effective_user
    user_name = user.first_name or "User"
    chat_id = update.message.chat_id

    # --- 1. Notify Owner ---
    try:
        owner_text = (
            f"🔔 New user started the bot:\n"
            f"Name: {user.full_name}\n"
            f"Username: @{user.username or 'No username'}\n"
            f"User ID: {user.id}"
        )
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=owner_text)
    except TelegramError as e:
        logger.error(f"Failed to send owner notification: {e}")

    # --- 2. Send Welcome Text with Clickable Buttons ---
    try:
        if not os.path.exists(WELCOME_FILE):
            logger.error(f"CRITICAL: '{WELCOME_FILE}' not found. Cannot send welcome message.")
            await context.bot.send_message(chat_id=chat_id, text="Welcome! The bot is under maintenance.")
            return

        with open(WELCOME_FILE, "r", encoding="utf-8") as f:
            welcome_text = f.read().replace("{name}", user_name)

        # --- Create Inline Buttons pointing to the correct personal account ---
        keyboard = [
            [InlineKeyboardButton("✅ Visit Our Secure Company Site", url="https://arthatech.net/")],
            # This now points to the correct personal username
            [InlineKeyboardButton("✅ Chat Securely with Our Team", url="https://t.me/Artha_Fintech")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
        logger.info(f"Sent welcome text with buttons to {user.full_name} ({user.id})")

    except Exception as e:
        logger.error(f"Error sending welcome text: {e}")
        return

    # --- 3. Send Brochure Images as a separate message ---
    media_group = []
    for img_path in BROCHURE_IMAGES:
        if os.path.exists(img_path):
            try:
                media_group.append(InputMediaPhoto(media=open(img_path, "rb")))
            except Exception as e:
                 logger.error(f"Error processing image {img_path}: {e}")
        else:
            logger.warning(f"Brochure image not found: '{img_path}'. Skipping it.")

    if media_group:
        try:
            await context.bot.send_media_group(chat_id=chat_id, media=media_group)
            logger.info(f"Successfully sent {len(media_group)} brochure(s) to {user.full_name}.")
        except TelegramError as e:
            logger.error(f"Telegram API error sending media group: {e}")

# ---------------- MAIN ----------------
def main() -> None:
    """Main function to set up and run the bot."""
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(clear_conflicts)
        .build()
    )

    application.add_handler(CommandHandler("start", send_welcome))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_welcome))

    logger.info("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.critical(f"Bot crashed with an unhandled exception: {e}")


