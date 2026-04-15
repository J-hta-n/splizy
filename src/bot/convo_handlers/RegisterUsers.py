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
from src.bot.convo_utils.wrappers import group_only
from src.lib.splizy_repo.repo import repo


class RegisterUsers(BaseConversation):
    REGISTER_USERS = 0
    CONFIRM_USERS = 1
    DELETE_USERS = 2
    REGISTER_INPUT_PATTERN = r"^\s*-?@\w+(?:\s+-?@\w+)*\s*$"

    DELETE_USERS_ENTRY = "register_manual_delete"
    DELETE_USERS_TOGGLE_PREFIX = "register_manual_delete_toggle:"
    DELETE_USERS_DONE = "register_manual_delete_done"
    DELETE_USERS_BACK = "register_manual_delete_back"

    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("register", register_command)),
            (CommandHandler("register_manual", register_manual_command)),
        ]
        self.states = {
            self.REGISTER_USERS: [
                CallbackQueryHandler(
                    begin_manual_delete_users,
                    pattern=f"^{self.DELETE_USERS_ENTRY}$",
                ),
                MessageHandler(
                    filters.Regex(self.REGISTER_INPUT_PATTERN)
                    & filters.TEXT
                    & ~filters.COMMAND,
                    register_users,
                ),
            ],
            self.CONFIRM_USERS: [
                CallbackQueryHandler(confirm_admin_users, pattern="^confirm_users$"),
                CallbackQueryHandler(retry_admin_users, pattern="^retry_users$"),
            ],
            self.DELETE_USERS: [
                CallbackQueryHandler(
                    toggle_manual_delete_user,
                    pattern=f"^{self.DELETE_USERS_TOGGLE_PREFIX}.*$",
                ),
                CallbackQueryHandler(
                    confirm_manual_delete_users,
                    pattern=f"^{self.DELETE_USERS_DONE}$",
                ),
                CallbackQueryHandler(
                    back_manual_delete_users,
                    pattern=f"^{self.DELETE_USERS_BACK}$",
                ),
            ],
        }


@group_only
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    New registration flow: Admin-based automatic user detection.
    Fetches all group admins, shows them to the user for confirmation.
    Immutable once registered - rejects if group already has registered users.
    """
    group_id = update.message.chat.id
    repo.ensure_group_exists({"id": group_id})

    # Check if group already has registered users
    existing_users = repo.list_group_users(group_id)
    if existing_users:
        usernames = [user["username"] for user in existing_users]
        users_list = ", ".join([f"@{u}" for u in usernames])
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="retry_users")]]
        await update.message.reply_text(
            "The following users are already registered:\n"
            f"{users_list}\n\n"
            "If there are any new members, make sure to assign them as admins and tap on Try Again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        context.user_data["group_id"] = group_id
        return RegisterUsers.CONFIRM_USERS

    # Fetch all group admins
    try:
        admins = await context.bot.get_chat_administrators(group_id)
    except Exception as e:
        await update.message.reply_text(
            "Unable to fetch group members. Please ensure I have admin permissions."
        )
        return ConversationHandler.END

    # Extract usernames from admins
    usernames = []
    for admin in admins:
        if admin.user.username:
            usernames.append(admin.user.username)

    if not usernames:
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="retry_users")]]
        await update.message.reply_text(
            "No user handles detected. Ensure that they have been set as admins, then tap on Try Again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        context.user_data["group_id"] = group_id
        return RegisterUsers.CONFIRM_USERS

    # Store for later confirmation
    context.user_data["pending_usernames"] = sorted(usernames)
    context.user_data["group_id"] = group_id

    # Show confirmation message
    await _show_admin_users_confirmation(update, usernames)
    return RegisterUsers.CONFIRM_USERS


async def _show_admin_users_confirmation(update: Update, usernames: list[str]) -> None:
    """Display detected admin users and ask for confirmation."""
    users_list = ", ".join([f"@{u}" for u in usernames])
    msg = (
        f"Detected {len(usernames)} users with admin permissions:\n\n"
        f"{users_list}\n\n"
        "Are these all your group members? Please ensure everyone is an admin before confirming."
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="confirm_users"),
            InlineKeyboardButton("🔄 Try Again", callback_data="retry_users"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if getattr(update, "message", None) is not None:
        await update.message.reply_text(msg, reply_markup=reply_markup)
        return
    if getattr(update, "callback_query", None) is not None:
        await update.callback_query.edit_message_text(msg, reply_markup=reply_markup)


async def confirm_admin_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Confirm and save the detected admin users."""
    query = update.callback_query
    await query.answer()

    usernames = context.user_data.get("pending_usernames", [])
    group_id = context.user_data.get("group_id")

    if not usernames or not group_id:
        await query.edit_message_text("Session expired. Please run /register again.")
        return ConversationHandler.END

    # Only add users that are not already registered.
    existing_users = repo.list_group_users(group_id)
    existing_usernames = {user["username"] for user in existing_users}
    new_usernames = sorted(
        [username for username in usernames if username not in existing_usernames]
    )

    if new_usernames:
        repo.insert_group_users(
            [{"group_id": group_id, "username": username} for username in new_usernames]
        )

    if new_usernames:
        msg = (
            f"✅ Registered {len(new_usernames)} new users successfully!\n\n"
            f"Users: @{', @'.join(new_usernames)}"
        )
    else:
        msg = (
            "No new users detected.\n\n"
            "If there are any new members, make sure to assign them as admins and tap on Try Again."
        )
    await query.edit_message_text(msg)

    # Clean up user data
    context.user_data.pop("pending_usernames", None)
    context.user_data.pop("group_id", None)

    return ConversationHandler.END


async def retry_admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Retry: refresh and re-fetch admin list."""
    query = update.callback_query
    await query.answer()

    group_id = context.user_data.get("group_id")

    if not group_id:
        await query.edit_message_text("Session expired. Please run /register again.")
        return ConversationHandler.END

    # Re-fetch admins
    try:
        admins = await context.bot.get_chat_administrators(group_id)
    except Exception as e:
        await query.edit_message_text(
            "Unable to refresh admin list. Please try again or use /register_manual."
        )
        return ConversationHandler.END

    usernames = []
    for admin in admins:
        if admin.user.username:
            usernames.append(admin.user.username)

    if not usernames:
        keyboard = [[InlineKeyboardButton("🔄 Try Again", callback_data="retry_users")]]
        await query.edit_message_text(
            "No user handles detected. Ensure that they have been set as admins, then tap on Try Again.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return RegisterUsers.CONFIRM_USERS

    context.user_data["pending_usernames"] = sorted(usernames)
    await _show_admin_users_confirmation(update, usernames)
    return RegisterUsers.CONFIRM_USERS


# ============================================================================
# LEGACY: Manual registration for testing and personal usage
# ============================================================================


@group_only
async def register_manual_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Legacy registration flow: Manual handle entry.
    For testing and personal usage. /register is now the production standard.
    """
    group_id = update.message.chat.id
    repo.ensure_group_exists({"id": group_id})

    msg = (
        "Manual mode (testing): send handles separated by spaces.\n"
        "Add users: @user1 @user2\n"
        "Delete users inline: -@user3 -@user4\n"
        "Or use the Delete users button to pick users interactively."
    )
    cur_users = repo.list_group_users(group_id)
    if cur_users:
        usernames = [f"@{user['username']}" for user in cur_users]
        msg += f"\n\nNote: the following users ({', '.join(usernames)}) are already registered and will not be overwritten."
    keyboard = [
        [
            InlineKeyboardButton(
                "Delete users", callback_data=RegisterUsers.DELETE_USERS_ENTRY
            )
        ]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    return RegisterUsers.REGISTER_USERS


def _render_manual_delete_users_keyboard(
    usernames: list[str], selected_usernames: set[str]
) -> InlineKeyboardMarkup:
    keyboard = []
    for username in usernames:
        prefix = "✅" if username in selected_usernames else "❌"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{prefix} @{username}",
                    callback_data=f"{RegisterUsers.DELETE_USERS_TOGGLE_PREFIX}{username}",
                )
            ]
        )
    keyboard.append(
        [
            InlineKeyboardButton("Done", callback_data=RegisterUsers.DELETE_USERS_DONE),
            InlineKeyboardButton(
                "Go back", callback_data=RegisterUsers.DELETE_USERS_BACK
            ),
        ]
    )
    return InlineKeyboardMarkup(keyboard)


async def begin_manual_delete_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    group_id = update.effective_chat.id
    users = repo.list_group_users(group_id)
    usernames = sorted([user["username"] for user in users], key=str.lower)

    if not usernames:
        await query.edit_message_text(
            "No registered users found to delete.\n\n"
            "Use /register_manual and send @user handles to add users first."
        )
        return ConversationHandler.END

    context.user_data["manual_delete_group_id"] = group_id
    context.user_data["manual_delete_usernames"] = usernames
    context.user_data["manual_delete_selected"] = []

    await query.edit_message_text(
        "Select users to delete, then tap Done to confirm.",
        reply_markup=_render_manual_delete_users_keyboard(usernames, set()),
    )
    return RegisterUsers.DELETE_USERS


async def toggle_manual_delete_user(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    action = query.data or ""
    username = action.replace(RegisterUsers.DELETE_USERS_TOGGLE_PREFIX, "", 1)

    usernames = context.user_data.get("manual_delete_usernames", [])
    selected = set(context.user_data.get("manual_delete_selected", []))

    if username not in usernames:
        await query.edit_message_text(
            "Invalid selection. Please try /register_manual again."
        )
        return ConversationHandler.END

    if username in selected:
        selected.remove(username)
    else:
        selected.add(username)

    context.user_data["manual_delete_selected"] = sorted(selected)
    await query.edit_message_text(
        "Select users to delete, then tap Done to confirm.",
        reply_markup=_render_manual_delete_users_keyboard(usernames, selected),
    )
    return RegisterUsers.DELETE_USERS


async def confirm_manual_delete_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    group_id = context.user_data.get("manual_delete_group_id")
    selected = sorted(context.user_data.get("manual_delete_selected", []))
    usernames = context.user_data.get("manual_delete_usernames", [])

    if group_id is None or not usernames:
        await query.edit_message_text(
            "Session expired. Please run /register_manual again."
        )
        return ConversationHandler.END

    if not selected:
        await query.edit_message_text(
            "Select at least one user to delete, or tap Go back to cancel.",
            reply_markup=_render_manual_delete_users_keyboard(usernames, set()),
        )
        return RegisterUsers.DELETE_USERS

    repo.delete_group_users(group_id, selected)

    context.user_data.pop("manual_delete_group_id", None)
    context.user_data.pop("manual_delete_usernames", None)
    context.user_data.pop("manual_delete_selected", None)

    await query.edit_message_text(f"Deleted: @{', @'.join(selected)}")
    return ConversationHandler.END


async def back_manual_delete_users(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data.pop("manual_delete_group_id", None)
    context.user_data.pop("manual_delete_usernames", None)
    context.user_data.pop("manual_delete_selected", None)

    await query.edit_message_text("Delete users cancelled.")
    return ConversationHandler.END


async def register_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process manual user entry."""
    tokens = [
        token.strip() for token in (update.message.text or "").split() if token.strip()
    ]
    if not tokens:
        await update.message.reply_text(
            "List cannot be empty. Example: @user1 @user2 or -@user3"
        )
        return RegisterUsers.REGISTER_USERS

    to_add: set[str] = set()
    to_delete: set[str] = set()

    for token in tokens:
        is_delete = token.startswith("-")
        handle = token[1:] if is_delete else token

        if not handle.startswith("@") or len(handle) <= 1:
            await update.message.reply_text(
                "Invalid format. Use @user to add, and -@user to delete."
            )
            return RegisterUsers.REGISTER_USERS

        username = handle[1:]
        if is_delete:
            to_delete.add(username)
        else:
            to_add.add(username)

    # Keep old behavior for manual add mode: include sender in additions.
    sender_username = update.effective_user.username
    if sender_username:
        to_add.add(sender_username)

    # If a username appears in both, treat it as delete for explicit testing intent.
    to_add -= to_delete

    group_id = update.message.chat.id
    existing_users = repo.list_group_users(group_id)
    existing_usernames = {user["username"] for user in existing_users}

    new_usernames = sorted(
        [username for username in to_add if username not in existing_usernames]
    )
    delete_usernames = sorted(
        [username for username in to_delete if username in existing_usernames]
    )

    if new_usernames:
        repo.insert_group_users(
            [{"group_id": group_id, "username": username} for username in new_usernames]
        )

    if delete_usernames:
        repo.delete_group_users(group_id, delete_usernames)

    messages: list[str] = []
    if new_usernames:
        messages.append(f"Added: @{', @'.join(new_usernames)}")
    if delete_usernames:
        messages.append(f"Deleted: @{', @'.join(delete_usernames)}")

    if not messages:
        messages.append("No changes made. Users may already be in the requested state.")

    msg = "\n".join(messages)
    await update.message.reply_text(msg)
    return ConversationHandler.END
