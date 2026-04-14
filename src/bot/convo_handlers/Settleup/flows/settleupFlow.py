from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from src.bot.convo_handlers.Settleup.utils.general import (
    build_sgd_exchange_rate_summary,
    get_suggested_payments,
)
from src.bot.convo_handlers.Settleup.utils.renderers import send_stats_table
from src.bot.convo_handlers.Settleup.utils.reports import send_settleup_reports
from src.bot.convo_utils.wrappers import group_only
from src.lib.currencies.service import refresh_exchange_rates_if_stale
from src.lib.splizy_repo.repo import repo


@group_only
async def settleup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    refresh_exchange_rates_if_stale()
    group_id = update.message.chat.id
    all_expenses = repo.list_expenses(group_id)
    settleup_currency = repo.get_group(group_id).get("settleup_currency", "SGD")
    stats, suggested_payments = get_suggested_payments(all_expenses, settleup_currency)
    exchange_rates_summary = build_sgd_exchange_rate_summary(all_expenses)
    await update.message.reply_text(f"{exchange_rates_summary}\n\n{suggested_payments}")
    await send_stats_table(update, context, stats)
    # await send_settleup_csv(update, context, all_expenses, settleup_currency)

    return ConversationHandler.END


@group_only
async def settleup_report_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    report_generated_at = datetime.now(timezone.utc)
    refresh_exchange_rates_if_stale()
    group_id = update.message.chat.id
    all_expenses = repo.list_expenses(group_id)
    settleup_currency = repo.get_group(group_id).get("settleup_currency", "SGD")

    await send_settleup_reports(
        update,
        context,
        all_expenses,
        settleup_currency,
        report_generated_at=report_generated_at,
    )
    return ConversationHandler.END
