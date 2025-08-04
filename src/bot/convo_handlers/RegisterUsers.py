from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.bot.convo_handlers.Base import BaseConversation
from src.bot.convo_utils.wrappers import group_only
from src.utils.database import supabase


class RegisterUsers(BaseConversation):
    REGISTER_USERS = 0

    def setup_handlers(self):
        self.entry_points = [
            (CommandHandler("register", register_command)),
        ]
        self.states = {
            self.REGISTER_USERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, register_users)
            ],
        }


@group_only
async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Register group chat id if not already registered
    group_id = update.message.chat.id
    supabase.table("groups").upsert({"id": group_id}).execute()

    msg = "Please enter a list of user telegram handles separated by a space, eg `@user1 @user2 @user3`"
    cur_users = (
        supabase.table("splizy_users")
        .select("*")
        .eq("group_id", group_id)
        .execute()
        .data
    )
    if cur_users:
        usernames = [f"@{user['username']}" for user in cur_users]
        msg += f"\n\nNote: the following users ({', '.join(usernames)}) are already registered and will not be overwritten."
    await update.message.reply_text(msg)
    return RegisterUsers.REGISTER_USERS


async def register_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        response = update.message.text
        usernames = [username.split("@")[1] for username in response.split(" ")]
        if not usernames:
            await update.message.reply_text(
                "List cannot be empty, please try again, eg `@user1 @user2 @user3`"
            )
            return
        usernames.append(update.effective_user.username)  # Add sender too
        usernames = list(set(usernames))  # Remove duplicates
    except IndexError as e:
        await update.message.reply_text(
            f"Invalid format; please remember to include '@' for each handle, eg `@user1 @user2 @user3`"
        )
        return RegisterUsers.REGISTER_USERS

    # Only add users that are not already registered
    existing_users = (
        supabase.table("splizy_users")
        .select("*")
        .eq("group_id", update.message.chat.id)
        .execute()
        .data
    )
    existing_usernames = [user["username"] for user in existing_users]
    new_usernames = [
        username for username in usernames if username not in existing_usernames
    ]
    if new_usernames:
        supabase.table("splizy_users").insert(
            [
                {"group_id": update.message.chat.id, "username": username}
                for username in new_usernames
            ]
        ).execute()
        msg = f"Registered the new users: @{', @'.join(new_usernames)}"
    else:
        msg = f"All users are already registered: @{', @'.join(usernames)}"
    await update.message.reply_text(msg)
    return ConversationHandler.END
