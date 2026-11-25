import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
USERS_FILE = "users.txt"


# ---------- User storage helpers ----------
def load_users():
    try:
        with open(USERS_FILE) as f:
            return set(int(line.strip()) for line in f if line.strip())
    except FileNotFoundError:
        return set()


def save_user(user_id: int):
    users = load_users()
    if user_id not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")


# ---------- /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)

    # Your existing promotional message
    await update.message.reply_text(
        "🎁 Welcome to Bonus Specialist! Here is your promotional message..."
    )

    # Notify every admin with inline action buttons
    username_text = f"@{user.username}" if user.username else "No username"
    keyboard = [
        [
            InlineKeyboardButton("💬 Message user directly", callback_data=f"msg_{user.id}"),
            InlineKeyboardButton("🔔 Send notification", callback_data=f"notify_{user.id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🆕 New user started the bot!\n"
                    f"Name: {user.full_name}\n"
                    f"Username: {username_text}\n"
                    f"ID: {user.id}\n\n"
                    f"Tap a button below to reach out to them."
                ),
                reply_markup=reply_markup,
            )
        except Exception as e:
            logger.warning("Could not notify admin %s: %s", admin_id, e)


# ---------- Inline button handler ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text("⛔ You are not an admin.")
        return

    data = query.data

    if data.startswith("msg_"):
        target_id = int(data[4:])
        context.user_data["target_id"] = target_id
        context.user_data["action"] = "message"
        await query.edit_message_text(
            f"💬 Type the message you want to send **directly** to user `{target_id}`.\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown",
        )

    elif data.startswith("notify_"):
        target_id = int(data[7:])
        context.user_data["target_id"] = target_id
        context.user_data["action"] = "notify"
        await query.edit_message_text(
            f"🔔 Type the notification you want to send to user `{target_id}`.\n"
            f"Send /cancel to abort.",
            parse_mode="Markdown",
        )

    elif data == "broadcast_start":
        context.user_data["action"] = "broadcast"
        await query.edit_message_text(
            "📢 Type the message you want to broadcast to all users.\n"
            "Send /cancel to abort."
        )


# ---------- Admin text handler (captures the message after clicking a button) ----------
async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return

    action = context.user_data.get("action")
    target_id = context.user_data.get("target_id")
    text = update.message.text
    if not action or not text:
        return

    if action == "message" and target_id:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"📨 Message from admin:\n{text}",
            )
            await update.message.reply_text("✅ Message delivered.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed: {e}")

    elif action == "notify" and target_id:
        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"🔔 Notification from admin:\n{text}",
            )
            await update.message.reply_text("✅ Notification delivered.")
        except Exception as e:
            await update.message.reply_text(f"❌ Failed: {e}")

    elif action == "broadcast":
        await do_broadcast(update, context, text)

    context.user_data.pop("action", None)
    context.user_data.pop("target_id", None)


# ---------- Broadcast ----------
async def do_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    users = load_users()
    success, failed = 0, 0
    for user_id in users:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 Announcement:\n{message_text}",
            )
            success += 1
        except Exception as e:
            logger.warning("Broadcast failed for %s: %s", user_id, e)
            failed += 1

    await update.effective_chat.send_message(
        f"✅ Broadcast complete.\nSent: {success}\nFailed: {failed}\nTotal: {len(users)}"
    )


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not an admin.")
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) == 1:
        users = load_users()
        await update.message.reply_text(
            f"📢 You can send a message to all {len(users)} users who started the bot.\n\n"
            f"Tap the button below, or use `/broadcast <message>`.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Start broadcast", callback_data="broadcast_start"),
            ]]),
        )
        return

    await do_broadcast(update, context, parts[1])


# ---------- /cancel ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    had_state = bool(context.user_data.get("action"))
    context.user_data.pop("action", None)
    context.user_data.pop("target_id", None)
    await update.message.reply_text(
        "❌ Cancelled." if had_state else "Nothing to cancel."
    )


# ---------- /adminhelp ----------
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not an admin.")
        return
    await update.message.reply_text(
        "🛠 Admin commands:\n\n"
        "/broadcast – Send a message to all users who started the bot\n"
        "/broadcast <message> – Broadcast immediately\n"
        "/cancel – Abort a pending action\n\n"
        "When a new user starts the bot, you receive inline buttons to message them directly or send a notification."
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("adminhelp", admin_help))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text)
    )

    logger.info("Bonus Specialist Bot is starting…")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
