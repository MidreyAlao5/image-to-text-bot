import os
import logging
import pytesseract
from PIL import Image
from io import BytesIO
from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, CallbackContext, ConversationHandler
)
from googletrans import Translator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Replace with your group and channel IDs
CHANNEL_ID = -1002682987275
GROUP_ID = -1002375756524
CHANNEL_LINK = "https://t.me/latest_animes_world"
GROUP_LINK = "https://t.me/All_anime_chat"

# Initialize translator
translator = Translator()

# Store extracted text per user
user_texts = {}

# States for conversation handler
TRANSLATE_TEXT = 1

# Language selection keyboard
def get_language_menu():
    keyboard = [
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton("🇪🇸 Spanish", callback_data="lang_es")],
        [InlineKeyboardButton("🇫🇷 French", callback_data="lang_fr"),
         InlineKeyboardButton("🇩🇪 German", callback_data="lang_de")],
        [InlineKeyboardButton("🇮🇹 Italian", callback_data="lang_it"),
         InlineKeyboardButton("🇷🇺 Russian", callback_data="lang_ru")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Function to check user membership
async def is_user_member(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    try:
        chat_member_channel = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        chat_member_group = await context.bot.get_chat_member(GROUP_ID, user_id)
        
        if chat_member_channel.status in ["member", "administrator", "creator"] and \
           chat_member_group.status in ["member", "administrator", "creator"]:
            return True
        else:
            return False
    except:
        return False

# Start command with verification
async def start(update: Update, context: CallbackContext):
    if not await is_user_member(update, context):
        keyboard = [[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                    [InlineKeyboardButton("💬 Join Group", url=GROUP_LINK)],
                    [InlineKeyboardButton("✅ I Have Joined", callback_data="verify")]]
        await update.message.reply_text(
            "🚀 *To use this bot, you must join our official groups:*\n\n"
            f"📢 [Join Channel]({CHANNEL_LINK})\n"
            f"💬 [Join Group]({GROUP_LINK})\n\n"
            "✅ *Click 'I Have Joined' after joining.*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "🤖 Welcome to the Image-to-Text & Translator Bot!\n\n"
        "📌 *How to Use:*\n"
        "1️⃣ Send me an *image* with text, and I will extract it for you.\n"
        "2️⃣ Use /translate to translate extracted or manually typed text.\n"
        "3️⃣ Use /tts to convert extracted text to speech.\n"
        "4️⃣ Use /help for more information.\n\n"
        "🌟 *Try sending me an image now!*"
    )

# Verify button callback
async def verify(update: Update, context: CallbackContext):
    query = update.callback_query
    if await is_user_member(query, context):
        await query.message.reply_text("✅ *Verification successful! You can now use the bot.*", parse_mode="Markdown")
    else:
        await query.message.reply_text(
            "⚠️ *You have not joined yet!*\n\n"
            f"📢 [Join Channel]({CHANNEL_LINK})\n"
            f"💬 [Join Group]({GROUP_LINK})\n\n"
            "✅ *Click 'I Have Joined' after joining.*",
            parse_mode="Markdown"
        )

# Help command
async def help_command(update: Update, context: CallbackContext):
    if not await is_user_member(update, context):
        await start(update, context)
        return

    await update.message.reply_text(
        "ℹ️ *Bot Usage Guide:*\n\n"
        "🖼️ *Extract Text:*\nSend an image with text, and I will extract it.\n\n"
        "🌎 *Translate Text:*\nUse /translate to select a method:\n"
        "- Translate extracted text from an image.\n"
        "- Manually type text to translate.\n\n"
        "🔊 *Text-to-Speech:*\nUse /tts to convert extracted text to speech.\n\n"
        "📌 *Additional Features Coming Soon:* Voice input, batch processing, and more!"
    )

# Extract text from images
async def extract_text(update: Update, context: CallbackContext):
    if not await is_user_member(update, context):
        await start(update, context)
        return

    user_id = update.message.from_user.id
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a valid image.")
        return

    await update.message.reply_text("⏳ Please wait while I'm extracting text...")

    # Get highest-resolution image
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = BytesIO(await photo_file.download_as_bytearray())

    # Convert image to text
    image = Image.open(photo_bytes)
    extracted_text = pytesseract.image_to_string(image)

    if extracted_text.strip():
        user_texts[user_id] = extracted_text  # Store for translation
        await update.message.reply_text(f"📝 *Extracted Text:*\n\n```{extracted_text}```", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No text detected. Try another image.")

# Convert text to speech
async def text_to_speech(update: Update, context: CallbackContext):
    if not await is_user_member(update, context):
        await start(update, context)
        return

    user_id = update.message.from_user.id
    if user_id not in user_texts:
        await update.message.reply_text("⚠️ No extracted text found. Please send an image first.")
        return

    text = user_texts[user_id]
    await update.message.reply_text("🔊 Converting text to speech, please wait...")

    tts = gTTS(text=text, lang="en")
    tts.save("speech.mp3")

    with open("speech.mp3", "rb") as audio:
        await update.message.reply_audio(audio)

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tts", text_to_speech))
    app.add_handler(MessageHandler(filters.PHOTO, extract_text))
    app.add_handler(CallbackQueryHandler(verify, pattern="^verify$"))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
