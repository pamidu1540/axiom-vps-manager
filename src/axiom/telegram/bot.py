"""
Axiom Async Telegram Bot Module
Built on python-telegram-bot v22.8 (Bot API 9.6) with non-blocking async architecture.
"""

import logging

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


class AxiomTelegramBot:
    def __init__(self, token: str, admin_id: int | None = None):
        self.token = token
        self.admin_id = admin_id
        self.user_manager = UserManager()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processes inline keyboard interactions."""
        query = update.callback_query
        await query.answer()

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
            user_data = self.user_manager.create_user(f"trial_{update.effective_user.id % 10000}", days=1, limit=1)
            text = (
                f"✅ <b>Trial Account Created</b>\n\n"
                f"• <b>Username:</b> <code>{user_data['username']}</code>\n"
                f"• <b>Password:</b> <code>{user_data['password']}</code>\n"
                f"• <b>Expires:</b> {user_data['expiry_date']}\n"
                f"• <b>Connection Limit:</b> {user_data['limit']}"
            )
            await query.edit_message_text(text, parse_mode="HTML")

        elif query.data == "list_users":
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
