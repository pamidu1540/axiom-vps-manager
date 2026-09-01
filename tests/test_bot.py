"""
Unit tests for Axiom Telegram Bot module
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from axiom.telegram.bot import AxiomTelegramBot


def test_bot_init():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=12345)
    assert bot.token == "123456:FAKE_TOKEN"
    assert bot.admin_id == 12345
    assert bot.user_manager is not None


def test_is_authorized():
    bot_with_admin = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    assert bot_with_admin.is_authorized(999) is True
    assert bot_with_admin.is_authorized(111) is False
    assert bot_with_admin.is_authorized(None) is False

    bot_open = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=None)
    assert bot_open.is_authorized(999) is True
    assert bot_open.is_authorized(None) is True


@pytest.mark.asyncio
async def test_start_command():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()

    await bot.start_command(update, None)
    update.message.reply_text.assert_called_once()
    args, kwargs = update.message.reply_text.call_args
    assert "Welcome to Axiom" in args[0]
    assert kwargs.get("reply_markup") is not None


@pytest.mark.asyncio
async def test_button_status():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = "status"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    with patch("axiom.monitor.stats.SystemMonitor.get_system_metrics") as mock_metrics:
        mock_metrics.return_value = {
            "mem_used_mb": 512,
            "mem_total_mb": 2048,
            "mem_percent": 25.0,
            "disk_used_gb": 10.0,
            "disk_total_gb": 50.0,
            "disk_percent": 20.0,
            "online_users": 3,
        }
        await bot.button_handler(update, None)

        update.callback_query.answer.assert_called_once()
        update.callback_query.edit_message_text.assert_called_once()
        args, _ = update.callback_query.edit_message_text.call_args
        assert "Server Status" in args[0]
        assert "512MB" in args[0]


@pytest.mark.asyncio
async def test_button_create_trial():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 5555
    update.callback_query = MagicMock()
    update.callback_query.data = "create_trial"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    with patch.object(bot.user_manager, "create_user") as mock_create:
        mock_create.return_value = {
            "username": "trial_5555",
            "password": "sample_password",
            "expiry_date": "2026-09-02",
            "limit": 1,
        }
        await bot.button_handler(update, None)

        update.callback_query.edit_message_text.assert_called_once()
        args, _ = update.callback_query.edit_message_text.call_args
        assert "Trial Account Created" in args[0]
        assert "trial_5555" in args[0]


@pytest.mark.asyncio
async def test_button_list_users_authorized():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 999
    update.callback_query = MagicMock()
    update.callback_query.data = "list_users"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    with patch.object(bot.user_manager, "list_users") as mock_list:
        mock_list.return_value = [
            {"username": "user1", "limit": 2},
            {"username": "user2", "limit": 1},
        ]
        await bot.button_handler(update, None)

        update.callback_query.edit_message_text.assert_called_once()
        args, _ = update.callback_query.edit_message_text.call_args
        assert "Active Accounts (2)" in args[0]
        assert "user1" in args[0]


@pytest.mark.asyncio
async def test_button_list_users_denied():
    bot = AxiomTelegramBot(token="123456:FAKE_TOKEN", admin_id=999)
    update = MagicMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 111  # Not admin!
    update.callback_query = MagicMock()
    update.callback_query.data = "list_users"
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()

    await bot.button_handler(update, None)

    update.callback_query.edit_message_text.assert_called_once()
    args, _ = update.callback_query.edit_message_text.call_args
    assert "Access Denied" in args[0]
