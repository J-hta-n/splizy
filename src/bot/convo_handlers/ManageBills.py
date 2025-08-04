import json
from decimal import Decimal

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_utils.parsers import parse_amount, parse_multiplier, parse_username
from src.bot.convo_utils.renderers import (
    get_bill_summary,
    send_all_expenses,
    send_confirmation_form,
    send_custom_multiselect_users,
    send_multiselect_users,
)
from src.bot.convo_utils.wrappers import group_only
from src.utils.database import supabase
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ManageBills(BaseConversation):
    (
        EXPENSE_NAME,
        EXPENSE_AMOUNT,
        EXPENSE_PAID_BY,
        EXPENSE_SPLIT_TYPE,
        EXPENSE_PARTICIPANTS,
        EXPENSE_CUSTOM_SPLIT,
        EXPENSE_CONFIRM,
        EXPENSE_CUSTOM_AMOUNT,
        EXPENSE_MULTIPLIER,
        VIEW_EXPENSE,
        EDIT_OR_GO_BACK,
        DELETE_EXPENSE,
    ) = range(3, 15)

    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("add", add_command)),
            CommandHandler("view", view_all_command),
        ]
        self.states = {
            self.EXPENSE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_name)
            ],
            self.EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)
            ],
            self.EXPENSE_PAID_BY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_paid_by)
            ],
            self.EXPENSE_SPLIT_TYPE: [CallbackQueryHandler(expense_split_type)],
            self.EXPENSE_PARTICIPANTS: [CallbackQueryHandler(expense_participants)],
            self.EXPENSE_CUSTOM_SPLIT: [CallbackQueryHandler(expense_custom_split)],
            self.EXPENSE_CUSTOM_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_custom_amount)
            ],
            self.EXPENSE_MULTIPLIER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, expense_multiplier)
            ],
            self.EXPENSE_CONFIRM: [CallbackQueryHandler(expense_confirm)],
            self.VIEW_EXPENSE: [CallbackQueryHandler(view_expense)],
            self.EDIT_OR_GO_BACK: [CallbackQueryHandler(edit_or_go_back)],
            self.DELETE_EXPENSE: [CallbackQueryHandler(delete_expense)],
        }


@group_only
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Let's add a new expense! Tell me what this is for? Eg 'Hotpot dinner'"
    )

    return ManageBills.EXPENSE_NAME


async def expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.text:
        await update.message.reply_text("Name cannot be empty, please try again.")
        return ManageBills.EXPENSE_NAME
    context.user_data["expense_name"] = update.message.text

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return ManageBills.EXPENSE_CONFIRM

    expense_currency = (
        supabase.table("groups")
        .select("expense_currency")
        .eq("id", update.message.chat.id)
        .execute()
        .data[0]["expense_currency"]
    )
    context.user_data["expense_currency"] = expense_currency
    context.user_data["currency"] = expense_currency
    await update.message.reply_text(
        "How much is it? Enter just the numeric value, eg '50.10'\n\n"
        f"(Expense currency is in {expense_currency}, override by adding currency code in front, eg 'KRW 100 or MYR 100')"
    )
    return ManageBills.EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    is_valid, result = parse_amount(update.message.text)
    if not is_valid:
        await update.message.reply_text(result)  # result is error msg if invalid
        return ManageBills.EXPENSE_AMOUNT
    currency, amount = result
    if currency:
        context.user_data["currency"] = currency
    context.user_data["amount"] = amount

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return ManageBills.EXPENSE_CONFIRM

    await update.message.reply_text(
        f"Who paid for this expense of {context.user_data['currency']} {context.user_data['amount']}? "
        "Please enter the telegram handle, eg `@user1`"
    )
    return ManageBills.EXPENSE_PAID_BY


async def expense_paid_by(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = (
        supabase.table("splizy_users")
        .select("username")
        .eq("group_id", update.message.chat.id)
        .execute()
        .data
    )
    usernames = [user["username"] for user in users]
    context.user_data["all_participants"] = usernames
    is_valid, result = parse_username(update.message.text, usernames)
    if not is_valid:
        await update.message.reply_text(result)
        return ManageBills.EXPENSE_PAID_BY
    context.user_data["paid_by"] = result

    if "edit_field" in context.user_data:
        await send_confirmation_form(update, context)
        return ManageBills.EXPENSE_CONFIRM

    keyboard = [
        [
            InlineKeyboardButton(
                "Split equally among all", callback_data="split_equal_all"
            )
        ],
        [
            InlineKeyboardButton(
                "Split equally only among some", callback_data="split_equal_some"
            )
        ],
        [InlineKeyboardButton("Split by custom amounts", callback_data="split_custom")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👥 How do you want to split this expense?", reply_markup=reply_markup
    )
    return ManageBills.EXPENSE_SPLIT_TYPE


async def expense_split_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    split_type = query.data
    data = context.user_data

    if split_type == "split_equal_all":
        data["is_equal_split"] = True
        data["split_type"] = "equal_all"

        await send_confirmation_form(update, context, False)
        return ManageBills.EXPENSE_CONFIRM
    elif split_type == "split_equal_some":
        data["is_equal_split"] = True
        data["split_type"] = "equal_some"

        # Since entire keyboard has to be rebuilt on every callback, state is managed with a bool array to minimise latency
        # and to preserve ordering of the inline buttons, as opposed to using a adding/removing strings in a string array
        if "participant_selections" not in data:
            data["participant_selections"] = [True] * len(data["all_participants"])
        await send_multiselect_users(update, context)
        return ManageBills.EXPENSE_PARTICIPANTS
    elif split_type == "split_custom":
        data["is_equal_split"] = False
        data["split_type"] = "custom"

        # Similarly, use the bool array implementation
        if "has_mult" not in data:
            data["has_mult"] = False
        if "mult_val" not in data:
            data["mult_val"] = 1.19
        total_participants = len(data["all_participants"])
        if "participant_selections" not in data:
            data["participant_selections"] = [True] * total_participants
        if "custom_amounts" not in data:
            data["custom_amounts"] = [
                data["amount"] / total_participants
            ] * total_participants
        await send_custom_multiselect_users(update, context)
        return ManageBills.EXPENSE_CUSTOM_SPLIT


async def expense_participants(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle the selection of participants."""
    query = update.callback_query
    await query.answer()

    action = query.data
    if action != "participants_done":
        # Toggle participant selection
        index = int(action)
        context.user_data["participant_selections"][index] = not context.user_data[
            "participant_selections"
        ][index]

        # Recreate keyboard with updated selection
        await send_multiselect_users(update, context)
        return ManageBills.EXPENSE_PARTICIPANTS

    if not any(context.user_data["participant_selections"]):
        # Recreate keyboard with validation error
        await send_multiselect_users(
            update, context, "Please select at least one participant."
        )
        return ManageBills.EXPENSE_PARTICIPANTS

    # Check if all participants were selected anyway
    selected_participants = [
        username
        for idx, username in enumerate(context.user_data["all_participants"])
        if context.user_data["participant_selections"][idx]
    ]
    if len(selected_participants) == len(context.user_data["all_participants"]):
        context.user_data["split_type"] = "equal_all"
    else:
        context.user_data["selected_participants"] = selected_participants
    await send_confirmation_form(update, context, False)
    return ManageBills.EXPENSE_CONFIRM


async def expense_custom_split(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    action = query.data

    data = context.user_data
    if action != "custom_done":
        entity, field = action.split("_")
        if entity.isdigit():
            index = int(entity)
            if field == "toggle":
                data["participant_selections"][index] = not data[
                    "participant_selections"
                ][index]
                await send_custom_multiselect_users(update, context)
                return ManageBills.EXPENSE_CUSTOM_SPLIT
            elif field == "amount":
                data["index"] = index
                await query.edit_message_text(
                    f"Please enter the amount spent by @{data['all_participants'][index]}:"
                )
                return ManageBills.EXPENSE_CUSTOM_AMOUNT
        else:
            if field == "toggle":
                data["has_mult"] = not data["has_mult"]
                await send_custom_multiselect_users(update, context)
                return ManageBills.EXPENSE_CUSTOM_SPLIT
            elif field == "amount":
                await query.edit_message_text(
                    "Please enter a multiplier between 1 and 2, eg 1.19"
                )
                return ManageBills.EXPENSE_MULTIPLIER

    # Custom split done, validate first
    logger.info("Validating custom split selections...")
    if not any(context.user_data["participant_selections"]):
        await send_custom_multiselect_users(
            update, context, False, "Please select at least one participant."
        )
        return ManageBills.EXPENSE_CUSTOM_SPLIT

    logger.info("Custom selection validated. Preparing confirmation form...")
    has_mult, mult_val = data["has_mult"], data["mult_val"]
    data["selected_participants"] = [
        username
        for idx, username in enumerate(data["all_participants"])
        if data["participant_selections"][idx]
    ]
    data["amount"] = sum(
        [
            (amount * Decimal(mult_val) if has_mult else amount)
            for idx, amount in enumerate(data["custom_amounts"])
            if data["participant_selections"][idx]
        ]
    )
    logger.info("Confirmation form prepared, sending...")
    print(json.dumps(dict(context.user_data), indent=2, default=str))
    await send_confirmation_form(update, context, False)
    logger.info("Confirmation form sent")

    return ManageBills.EXPENSE_CONFIRM


async def expense_custom_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    is_valid, result = parse_amount(update.message.text)
    if not is_valid:
        await update.message.reply_text(result)  # result is error msg if invalid
        return ManageBills.EXPENSE_CUSTOM_AMOUNT
    _, amount = result

    index = context.user_data["index"]
    context.user_data["custom_amounts"][index] = amount

    await send_custom_multiselect_users(update, context, True)
    return ManageBills.EXPENSE_CUSTOM_SPLIT


async def expense_multiplier(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    is_valid, result = parse_multiplier(update.message.text)
    if not is_valid:
        await update.message.reply_text(result)
        return ManageBills.EXPENSE_MULTIPLIER
    context.user_data["mult_val"] = result

    await send_custom_multiselect_users(update, context, True)
    return ManageBills.EXPENSE_CUSTOM_SPLIT


async def expense_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action != "submit_form" and action != "cancel_form":
        context.user_data["edit_field"] = action

    if action == "edit_expense_name":
        await query.edit_message_text("What is the new name for this expense?")
        return ManageBills.EXPENSE_NAME
    elif action == "edit_amount":
        if context.user_data["split_type"] == "custom":
            await send_custom_multiselect_users(update, context)
            return ManageBills.EXPENSE_CUSTOM_SPLIT
        else:
            await query.edit_message_text(
                "Please send the new amount in raw numeric form.\n(add currency code in front to override current currency)"
            )
            return ManageBills.EXPENSE_AMOUNT
    elif action == "edit_payer":
        await query.edit_message_text(
            "Please enter the telegram handle of the new payer, eg `@user1`"
        )
        return ManageBills.EXPENSE_PAID_BY
    elif action == "edit_split":
        # Ask how to split the expense
        keyboard = [
            [
                InlineKeyboardButton(
                    "Split equally among all", callback_data="split_equal_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "Split equally only among some", callback_data="split_equal_some"
                )
            ],
            [
                InlineKeyboardButton(
                    "Split by custom amounts", callback_data="split_custom"
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"👥 How do you want to split this expense?", reply_markup=reply_markup
        )
        return ManageBills.EXPENSE_SPLIT_TYPE
    elif action == "cancel_form":
        if "expenses" not in context.user_data:
            await query.edit_message_text("Operation cancelled.")
            return ConversationHandler.END
        await send_all_expenses(update, context, False)
        return ManageBills.VIEW_EXPENSE

    elif action == "submit_form":
        data = context.user_data
        entry = {
            "group_id": query.message.chat.id,
            "title": data["expense_name"],
            "amount": str(data["amount"]),  # Decimal is not JSON serializable
            "paid_by": data["paid_by"],
            "currency": data["currency"],
            "is_equal_split": data["is_equal_split"],
            "multiplier": str(data["mult_val"])
            if ("has_mult" in data and data["has_mult"])
            else None,
        }
        # NOTE: look into implementing transactions with supabase.table().rpc() in future if needed; for now
        # things are simple enough that failures are unlikely / manual rollbacks are manageable, so no need
        # to overengineer at the moment
        try:
            if "expense_id" in data:
                # If editing existing expense, delete all outdated user_expenses first and update expense
                supabase.table("user_expenses").delete().eq(
                    "expense_id", data["expense_id"]
                ).execute()
                supabase.table("expenses").update(entry).eq(
                    "id", data["expense_id"]
                ).execute()
            else:
                # Else create new expense and record its expense_id
                new_expense_id = (
                    supabase.table("expenses").insert(entry).execute().data[0]["id"]
                )
                data["expense_id"] = new_expense_id
            # Then create new user_expenses
            if data["split_type"] == "equal_all" or data["split_type"] == "equal_some":
                participants = (
                    data["all_participants"]
                    if data["split_type"] == "equal_all"
                    else data["selected_participants"]
                )
                amount_per_pax = str(data["amount"] / len(participants))
                supabase.table("user_expenses").insert(
                    [
                        {
                            "username": username,
                            "group_id": query.message.chat.id,
                            "expense_id": data["expense_id"],
                            "amount": amount_per_pax,
                        }
                        for username in participants
                    ]
                ).execute()
            else:
                # Custom split
                supabase.table("user_expenses").insert(
                    [
                        {
                            "username": username,
                            "group_id": query.message.chat.id,
                            "expense_id": data["expense_id"],
                            "amount": str(amount * Decimal(data["mult_val"]))
                            if data["has_mult"]
                            else str(amount),
                        }
                        for idx, (username, amount) in enumerate(
                            zip(data["selected_participants"], data["custom_amounts"])
                        )
                        if data["participant_selections"][idx]
                    ]
                ).execute()
            await query.edit_message_text(
                f"Expense for {data['expense_name']} saved successfully!"
            )
            context.user_data.clear()
            return ConversationHandler.END

        except Exception as e:
            logger.error(f"Failed to add / edit expense: {e}")
            await query.edit_message_text(
                "Failed to add / edit expense, please check logs."
            )
            context.user_data.clear()
            return ConversationHandler.END

    return ManageBills.EXPENSE_CONFIRM


@group_only
async def view_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    group_id = update.message.chat.id
    expenses = (
        supabase.table("expenses")
        .select("*")
        .eq("group_id", group_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )
    if not expenses:
        await update.message.reply_text("No expenses logged yet.")
        return ConversationHandler.END
    context.user_data["expenses"] = expenses

    await send_all_expenses(update, context)
    return ManageBills.VIEW_EXPENSE


async def view_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    index = int(query.data)
    expense = context.user_data["expenses"][index]
    group_id = query.message.chat.id

    users = (
        supabase.table("splizy_users")
        .select("username")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    user_expenses = (
        supabase.table("user_expenses")
        .select("*")
        .eq("expense_id", expense["id"])
        .execute()
        .data
    )
    context.user_data["all_participants"] = [user["username"] for user in users]
    context.user_data["has_mult"] = expense.get("multiplier") is not None
    context.user_data["mult_val"] = expense.get("multiplier")

    if expense["is_equal_split"]:
        context.user_data["split_type"] = (
            "equal_some" if len(user_expenses) < len(users) else "equal_all"
        )
    else:
        context.user_data["split_type"] = "custom"
    context.user_data["selected_participants"] = [
        ue["username"] for ue in user_expenses
    ]
    context.user_data["participant_selections"] = [
        username in context.user_data["selected_participants"]
        for username in context.user_data["all_participants"]
    ]
    context.user_data["custom_amounts"] = [ue["amount"] for ue in user_expenses]

    context.user_data["expense_id"] = expense[
        "id"
    ]  # Signals an edit flow in expense_confirm
    context.user_data["expense_name"] = expense["title"]
    context.user_data["amount"] = Decimal(expense["amount"])
    context.user_data["paid_by"] = expense["paid_by"]
    context.user_data["currency"] = expense["currency"]
    context.user_data["is_equal_split"] = expense["is_equal_split"]

    summary = get_bill_summary(context.user_data)
    keyboard = [
        [
            InlineKeyboardButton("Edit", callback_data="edit_expense"),
            InlineKeyboardButton("Delete", callback_data="delete_expense"),
        ],
        [InlineKeyboardButton("Go back", callback_data="go_back")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(summary, reply_markup=reply_markup)
    return ManageBills.EDIT_OR_GO_BACK


async def edit_or_go_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "edit_expense":
        await send_confirmation_form(update, context, False)
        return ManageBills.EXPENSE_CONFIRM
    elif action == "delete_expense":
        data = context.user_data
        keyboard = [
            [
                InlineKeyboardButton("❌ No", callback_data="cancel_delete"),
                InlineKeyboardButton("✅ Yes", callback_data="confirm_delete"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=(
                f"Are you sure you want to delete this expense?\n({data['expense_name']} | {data['paid_by']} | {data['currency']} {data['amount']})\n"
                "This action cannot be undone."
            ),
            reply_markup=reply_markup,
        )
        return ManageBills.DELETE_EXPENSE
    else:
        await send_all_expenses(update, context, False)
        return ManageBills.VIEW_EXPENSE


async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "confirm_delete":
        expense_id = context.user_data["expense_id"]
        supabase.table("expenses").delete().eq(
            "id", expense_id
        ).execute()  # Cascade deletes user_expenses
        await query.edit_message_text("Expense deleted successfully.")
        context.user_data.clear()
        return ConversationHandler.END
    elif action == "cancel_delete":
        await send_all_expenses(update, context, False)
        return ManageBills.VIEW_EXPENSE

    return ConversationHandler.END
