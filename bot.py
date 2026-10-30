import os
import logging
import random
from datetime import time, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Educational AI Tips
AI_TIPS = [
    "💡 AI Tip: 'Zero-shot learning' means an AI can perform a task it was never explicitly trained on. Try asking ChatGPT to write in a completely new style!",
    "🧠 Did you know? Neural networks are inspired by the human brain, but they don't 'think'—they just find complex patterns in data.",
    "🚀 Free Tool: Use 'Hugging Face' to experiment with thousands of open-source AI models for free.",
    "🤖 AI Tip: When prompting an AI, always give it a 'role' (e.g., 'Act as a senior Python developer') to get much better answers.",
    "📊 AI is great at analyzing data, but it can 'hallucinate' (make up facts). Always double-check critical information!",
    "🛠️ AI Tip: AI isn't just text. You can use tools like Midjourney or DALL-E to generate images from simple text descriptions."
]

# --- UI BUILDERS ---

def get_main_menu_keyboard():
    """Creates the main inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("📚 Subscribe to Daily Tips", callback_data="subscribe")],
        [InlineKeyboardButton("🔒 Privacy Policy", callback_data="privacy")],
        [InlineKeyboardButton("🛑 Stop Tips", callback_data="stop")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_stop_keyboard():
    """Keyboard to show inside daily tips so users can easily unsubscribe."""
    keyboard = [[InlineKeyboardButton("🛑 Stop Receiving Tips", callback_data="stop")]]
    return InlineKeyboardMarkup(keyboard)

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the initial /start (mandatory for Telegram)."""
    welcome_text = (
        "👋 Welcome to **Bonus Specialist**!\n\n"
        "🤖 **Transparency Note:** I am an AI-powered educational bot. I share free daily tips about Artificial Intelligence to help you learn.\n\n"
        "Click a button below to get started:"
    )
    # If it's a callback query (e.g., clicking a "Back" button)
    if update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all inline button clicks."""
    query = update.callback_query
    await query.answer() # Acknowledge the click

    chat_id = query.message.chat_id
    data = query.data

    if data == "subscribe":
        # Check if already subscribed
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        if current_jobs:
            await query.edit_text(
                "✅ You are already subscribed! You will receive a tip every day at 09:00 UTC.",
                reply_markup=get_main_menu_keyboard()
            )
            return

        # Schedule daily job
        context.job_queue.run_daily(
            send_daily_tip,
            time=time(hour=9, minute=0, tzinfo=timezone.utc),
            chat_id=chat_id,
            name=str(chat_id),
            data={"chat_id": chat_id}
        )
        await query.edit_text(
            "🎉 **Subscribed!**\n\nYou will receive a new AI tip every day at 09:00 UTC.\nYou can click 'Stop Tips' at any time to unsubscribe.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "stop":
        current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
        if not current_jobs:
            await query.edit_text(
                "You are not currently subscribed to daily tips.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        for job in current_jobs:
            job.schedule_removal()
            
        await query.edit_text(
            "🔕 **Unsubscribed.**\n\nYou will no longer receive daily tips. You can resubscribe anytime.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )

    elif data == "privacy":
        policy = (
            "🔒 **Privacy Policy for Bonus Specialist**\n\n"
            "1. **Data Collected:** We store your Telegram Chat ID solely to deliver the daily tips you requested.\n"
            "2. **Usage:** We do not sell your data or use it for third-party advertising.\n"
            "3. **Opt-out:** You can delete your data by clicking 'Stop Tips' or blocking the bot.\n"
            "4. **AI Disclosure:** This bot uses automated scripts to provide educational content."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
        await query.edit_text(policy, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "back":
        await start(update, context)

# --- DAILY JOB ---

async def send_daily_tip(context: ContextTypes.DEFAULT_TYPE):
    """Sends the scheduled daily tip."""
    job = context.job
    chat_id = job.data["chat_id"]
    
    tip = random.choice(AI_TIPS)
    
    try:
        await context.bot.send_message(
            chat_id=chat_id, 
            text=tip, 
            reply_markup=get_stop_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        # If the user blocked the bot, remove their job
        logger.error(f"Failed to send tip to {chat_id}: {e}")
        job.schedule_removal()

# --- MAIN ---

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found. Set it in Render Environment Variables.")

    application = Application.builder().token(token).build()

    # We still need to catch /start because Telegram forces it when clicking "Start"
    application.add_handler(CommandHandler("start", start))
    
    # All other interactions are handled by buttons
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bonus Specialist Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
