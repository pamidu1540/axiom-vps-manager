"""
Axiom Async Telegram Bot Module
Built on python-telegram-bot v22.8 (Bot API 9.6) with non-blocking async architecture.
"""

import logging
import os
import sys

from axiom.config import load_config
from axiom.monitor.stats import SystemMonitor
from axiom.users.manager import UserManager

logger = logging.getLogger("AxiomTelegramBot")

try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
    from telegram.ext import (
        Application,
        CallbackQueryHandler,
        CommandHandler,
        ContextTypes,
    )

    PTB_AVAILABLE = True
except ImportError:
    PTB_AVAILABLE = False
    Update = None
    ContextTypes = None

    class InlineKeyboardButton:  # type: ignore[no-redef]
        """Stub for environments without python-telegram-bot installed."""

        def __init__(self, text: str, callback_data: str = ""):
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:  # type: ignore[no-redef]
        """Stub for environments without python-telegram-bot installed."""

        def __init__(self, keyboard):
            self.keyboard = keyboard


class AxiomTelegramBot:
    def __init__(self, token: str, admin_id: int | None = None):
        self.token = token
        self.admin_id = admin_id
        self.user_manager = UserManager()

    def is_authorized(self, user_id: int | None) -> bool:
        """Checks if the given user ID has administrator privileges."""
        if self.admin_id is None:
            return True
        return user_id is not None and user_id == self.admin_id

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE if ContextTypes else None):
        """Handles /start command with interactive inline menu."""
        keyboard = [
            [InlineKeyboardButton("📊 System Status", callback_data="status")],
            [InlineKeyboardButton("⚡ Create Trial User", callback_data="create_trial")],
            [InlineKeyboardButton("👥 List Users", callback_data="list_users")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "<b>⚡ Welcome to Axiom VPS Manager ⚡</b>\nSelect an option below:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE if ContextTypes else None):
        """Processes inline keyboard interactions with authorization checks."""
        query = update.callback_query
        if not query:
            return
        await query.answer()

        user_id = update.effective_user.id if update.effective_user else None

        if query.data == "status":
            metrics = SystemMonitor.get_system_metrics()
            text = (
                f"<b>📊 Server Status</b>\n"
                f"• <b>RAM:</b> {metrics['mem_used_mb']}MB / {metrics['mem_total_mb']}MB ({metrics['mem_percent']}%)\n"
                f"• <b>Disk:</b> {metrics['disk_used_gb']}GB / {metrics['disk_total_gb']}GB ({metrics['disk_percent']}%)\n"
                f"• <b>Online Users:</b> {metrics['online_users']}"
            )
            await query.edit_message_text(text, parse_mode="HTML")

        elif query.data == "create_trial":
            user_suffix = user_id % 10000 if user_id else 1
            user_data = self.user_manager.create_user(f"trial_{user_suffix}", days=1, limit=1)
            text = (
                f"✅ <b>Trial Account Created</b>\n\n"
                f"• <b>Username:</b> <code>{user_data['username']}</code>\n"
                f"• <b>Password:</b> <code>{user_data['password']}</code>\n"
                f"• <b>Expires:</b> {user_data['expiry_date']}\n"
                f"• <b>Connection Limit:</b> {user_data['limit']}"
            )
            await query.edit_message_text(text, parse_mode="HTML")

        elif query.data == "list_users":
            if not self.is_authorized(user_id):
                await query.edit_message_text(
                    "🚫 <b>Access Denied: Admin authorization required.</b>",
                    parse_mode="HTML",
                )
                return

            users = self.user_manager.list_users()
            user_text = "\n".join([f"• <code>{u['username']}</code> (Limit: {u['limit']})" for u in users[:20]])
            await query.edit_message_text(
                f"<b>👥 Active Accounts ({len(users)})</b>\n\n{user_text or 'No accounts found.'}", parse_mode="HTML"
            )

    def run(self):
        """Starts the async polling bot daemon."""
        if not PTB_AVAILABLE:
            logger.error("python-telegram-bot is not installed. Install via pip install python-telegram-bot")
            return

        app = Application.builder().token(self.token).build()
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("status", self.start_command))
        app.add_handler(CallbackQueryHandler(self.button_handler))

        logger.info("Axiom Telegram Bot starting polling...")
        app.run_polling()


def main():
    """CLI and systemd entrypoint for the Axiom Telegram Bot daemon."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser(description="Axiom Telegram Automation Bot")
    parser.add_argument("--token", help="Telegram Bot API Token", default=None)
    parser.add_argument("--admin-id", help="Admin Telegram User ID", type=int, default=None)
    args = parser.parse_args()

    config = load_config()
    telegram_cfg = config.get("telegram", {})

    token = (
        args.token
        or os.environ.get("AXIOM_BOT_TOKEN")
        or os.environ.get("TELEGRAM_BOT_TOKEN")
        or os.environ.get("BOT_TOKEN")
        or telegram_cfg.get("bot_token")
    )

    admin_id = args.admin_id
    if admin_id is None:
        env_admin = (
            os.environ.get("AXIOM_BOT_ADMIN_ID")
            or os.environ.get("ADMIN_CHAT_ID")
            or os.environ.get("ADMIN_ID")
            or telegram_cfg.get("admin_chat_id")
        )
        if env_admin and str(env_admin).strip().isdigit():
            admin_id = int(str(env_admin).strip())

    if not token:
        logger.error("No Telegram Bot Token provided. Set AXIOM_BOT_TOKEN or configure axiom.toml.")
        sys.exit(1)

    bot = AxiomTelegramBot(token=token, admin_id=admin_id)
    bot.run()


if __name__ == "__main__":
    main()
