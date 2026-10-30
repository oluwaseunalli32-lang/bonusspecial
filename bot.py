import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends the promotional message immediately when the user clicks Start."""
    
    # Using HTML formatting to embed the links into the word "AQUI"
    message = (
        "👇 <b>3 Ofertas disponíveis</b> 👇\n\n"
        "🎁 <b>Ofertas sem depósito</b> 🎁\n\n"
        "<b>1. ColdBet - 50 Free Spins</b>\n"
        "Slot: Le Prechaun\n"
        "Código de registo: <code>SEMDEPOSITO</code>\n"
        "Regista-te 👉 <a href='https://coldb2.com/19r3yq4N'>AQUI</a>\n\n"
        "<b>2. Bettilt - 40€ em Apostas Grátis</b>\n"
        "Código de registo: <code>SEMDEPOSITO</code>\n"
        "Regista-te 👉 <a href='https://btt-pt.rklnk.xyz/pt/sportsbook?partner=p434p34913p003f#registration-bonus'>AQUI</a>\n\n"
        "<b>3. Spinbetter - 100 Free Spins</b>\n"
        "Slot: Book of Wealth III\n"
        "Código de registo: <code>SEMDEPOSITO</code>\n"
        "Regista-te 👉 <a href='https://redirspinner.com/2DVE?p=%2Fregistration%2F'>AQUI</a>"
    )
    
    # Send the message with HTML parsing and no link previews
    await update.message.reply_text(
        text=message, 
        parse_mode='HTML',
        disable_web_page_preview=True
    )

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("No BOT_TOKEN found. Set it in Render Environment Variables.")

    application = Application.builder().token(token).build()

    # Only listening for the mandatory /start command
    application.add_handler(CommandHandler("start", start))

    logger.info("Bonus Specialist Bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
