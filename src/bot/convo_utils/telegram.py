from telegram import Update


def get_message_thread_id(update: Update) -> int | None:
    return getattr(update.effective_message, "message_thread_id", None)
