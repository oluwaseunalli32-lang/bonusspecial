import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---- Load admin IDs from environment variable ----
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start, sends the promotional message, and notifies admins."""
    # Your existing promotional message – replace the text below with your actual message
    await update.message.reply_text(
        "🎁 Welcome to Bonus Specialist! Here is your promotional message..."
    )

    # ---- Notify every admin about the new user ----
    user = update.effective_user
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🆕 New user started the bot!\n"
                    f"Name: {user.full_name}\n"
                    f"Username: @{user.username}" if user.username else "No username\n"
                    f"ID: {user.id}\n\n"
                    f"Use /reply {user.id} <message> to contact them, "
                    f"or /notify {user.id} <message> to send a notification."
                )
            )
        except Exception as e:
            logger.warning("Could not notify admin %s: %s", admin_id, e)


async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /reply <user_id> <message>"""
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not an admin.")
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /reply <user_id> <message>")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    reply_text = parts[2]
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📨 Message from admin:\n{reply_text}"
        )
        await update.message.reply_text("✅ Reply sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def admin_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /notify <user_id> <message>"""
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not an admin.")
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /notify <user_id> <message>")
        return

    try:
        target_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    note = parts[2]
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🔔 Notification from the admin:\n{note}"
        )
        await update.message.reply_text("✅ Notification sent.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed: {e}")


async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only: /add_admin <user_id>"""
    admin_id = update.effective_user.id
    if admin_id not in ADMIN_IDS:
        await update.message.reply_text("⛔ You are not an admin.")
        return

    parts = update.message.text.split()
    if len(parts) != 2:
        await update.message.reply_text("Usage: /add_admin <user_id>")
        return

    try:
        new_admin_id = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid user ID.")
        return

    if new_admin_id in ADMIN_IDS:
        await update.message.reply_text("That user is already an admin.")
        return

    ADMIN_IDS.append(new_admin_id)
    await update.message.reply_text(f"✅ User {new_admin_id} added as admin.")
    try:
        await context.bot.send_message(
            chat_id=new_admin_id,
            text="🎉 You have been promoted to admin of this bot."
        )
    except Exception:
        pass  # New admin may not have started the bot yet


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found.")

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reply", admin_reply))
    application.add_handler(CommandHandler("notify", admin_notify))
    application.add_handler(CommandHandler("add_admin", add_admin))

    logger.info("Bonus Specialist Bot is starting…")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
