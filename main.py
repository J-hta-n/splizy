from config import PORT, SECRET_TOKEN, WEBHOOK_URL
from src.bot.telebot import initialise_telebot
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    telebot = initialise_telebot()
    # Set the webhook
    if WEBHOOK_URL:
        logger.info(f"Running as a webhook on port {PORT}")
        telebot.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=WEBHOOK_URL,
            secret_token=SECRET_TOKEN,
        )
    else:
        # Fallback to polling
        logger.info(f"Polling on port {PORT}")
        telebot.run_polling()


if __name__ == "__main__":
    main()
