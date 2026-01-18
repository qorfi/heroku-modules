# meta developer: @znxiw
# scope: hikka_only
# поддержки премиум эмодзи не будет. разраб тильтует

import asyncio
import random
import logging
import json
import os
from datetime import datetime
from telethon import functions, types
from .. import loader, utils

__version__ = (1, 0, 0)

logger = logging.getLogger(__name__)

@loader.tds
class ConstantOnlineMod(loader.Module):
    """
    Elite Constant Online System + Surveillance Log + Game Status.
    Includes:
    - Deep State Keep-Alive
    - Human-like Adaptive Typing / Gaming Status
    - JSON Export Logging (Telegram Desktop format)
    """
    
    strings = {
        "name": "ConstantOnline",
        "on": (
            "<blockquote><emoji document_id=5287717156467778509>🟢</emoji> <b>Online System: ACTIVE</b>\n"
            "Mode: <b>Adaptive/Stealth</b>\n"
            "Logging: <b>{}</b>\n"
            "Game Status: <b>{}</b></blockquote>"
        ),
        "off": "<blockquote><emoji document_id=5287534079191819089>🔴</emoji> <b>Online System: OFF</b></blockquote>",
        "dump_caption": "<b>📂 Incoming Traffic Dump</b>\n<i>Format: Telegram JSON Export</i>\n\nEntries: {}",
        "no_logs": "<b>⚠️ Log file is empty or does not exist.</b>",
        "log_cleared": "<b>🗑 Log file has been purged.</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "interval", 17, "Интервал (сек). Рекомендуется 20-30.",
            "auto_read", True, "Авто-чтение сообщений.",
            "auto_typing", True, "Адаптивная имитация печати.",
            "exempt_users", "", "ID/Username через пробел для игнора.",
            "enable_logging", True, "Логировать входящие в файл (JSON).",
            "log_filename", "incoming_export.json", "Имя файла лога.",
            "enable_game", False, "Показывать статус 'Играет в...' вместо печати.",
            "game_title", "Half-Life 3", "Название игры (виртуальное)."
        )
        self._task = None
        self._log_lock = asyncio.Lock()

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        await self._init_log_file()
        
        if self._db.get(self.strings["name"], "status", False):
            await self._start_loop()

    async def _init_log_file(self):
        fname = self.config["log_filename"]
        if not os.path.exists(fname):
            async with self._log_lock:
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump({"about": "ConstantOnline Dump", "messages": []}, f, indent=4)

    async def _start_loop(self):
        if self._task: self._task.cancel()
        self._task = asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            try:ъ
                await self._client(functions.account.GetPrivacyRequest(
                    key=types.InputPrivacyKeyStatusTimestamp()
                ))
                await self._client(functions.account.UpdateStatusRequest(offline=False))
                
                await asyncio.sleep(self.config["interval"] + random.randint(5, 15))
            except asyncio.CancelledError: break
            except Exception: await asyncio.sleep(15)

    async def _log_message(self, message, sender):
        if not self.config["enable_logging"]: return

        fname = self.config["log_filename"]
        msg_obj = {
            "id": message.id,
            "type": "message",
            "date": message.date.isoformat(),
            "date_unixtime": str(int(message.date.timestamp())),
            "from": getattr(sender, 'first_name', 'Unknown') + " " + (getattr(sender, 'last_name', '') or "").strip(),
            "from_id": f"user{sender.id}",
            "text": message.text or "",
            "text_entities": []
        }

        async with self._log_lock:
            try:
                with open(fname, "r+", encoding="utf-8") as f:
                    try: data = json.load(f)
                    except json.JSONDecodeError: data = {"about": "ConstantOnline Dump", "messages": []}
                    data["messages"].append(msg_obj)
                    f.seek(0)
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    f.truncate()
            except Exception as e: logger.error(f"Log Error: {e}")

    def _is_exempt(self, user_id, username):
        exempt = str(self.config["exempt_users"]).split()
        if str(user_id) in exempt: return True
        if username and username.lstrip("@").lower() in [u.lstrip("@").lower() for u in exempt]:
            return True
        return False

    @loader.watcher(only_messages=True, out=False)
    async def watcher(self, message):
        if not self._db.get(self.strings["name"], "status", False) or not message.is_private:
            return

        sender = await message.get_sender()
        if not sender or getattr(sender, 'bot', False) or self._is_exempt(sender.id, getattr(sender, 'username', None)):
            return

        # 1. Логирование
        await self._log_message(message, sender)

        try:
            # 2. Имитация активности
            if self.config["auto_typing"] or self.config["enable_game"]:
                content_len = len(message.text or "")
                delay = min(max(content_len // 10, 2), 8)
                
                if self.config["enable_game"]:
                    # Играет в...
                    # (Работает нестабильно на UserAPI, но это лучшая реализация без бота)
                    await self._client(functions.messages.SetTypingRequest(
                        peer=message.chat_id,
                        action=types.SendMessageGamePlayAction()
                    ))
                else:
                    # Печатает...
                    await self._client(functions.messages.SetTypingRequest(
                        peer=message.chat_id,
                        action=types.SendMessageTypingAction()
                    ))
                
                await asyncio.sleep(delay)

            # 3. Авточтение
            if self.config["auto_read"]:
                await self._client.send_read_acknowledge(message.chat_id, message)
        except Exception: pass

    @loader.command()
    async def online(self, message):
        """ - включить/выключить режим"""
        state = not self._db.get(self.strings["name"], "status", False)
        self._db.set(self.strings["name"], "status", state)
        if state:
            await self._start_loop()
            log_status = "ON" if self.config["enable_logging"] else "OFF"
            game_status = self.config["game_title"] if self.config["enable_game"] else "OFF"
            await utils.answer(message, self.strings["on"].format(log_status, game_status))
        else:
            if self._task: self._task.cancel()
            await self._client(functions.account.UpdateStatusRequest(offline=True))
            await utils.answer(message, self.strings["off"])

    @loader.command()
    async def dumplog(self, message):
        """ - Выгрузить лог (JSON)"""
        fname = self.config["log_filename"]
        if not os.path.exists(fname):
            return await utils.answer(message, self.strings["no_logs"])
        
        count = 0
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = len(data.get("messages", []))
        except: pass

        await utils.answer(message, self.strings["dump_caption"].format(count))
        await self._client.send_file(
            message.chat_id,
            fname,
            caption=f"Dump generated at {datetime.now().strftime('%H:%M:%S')}"
        )

    @loader.command()
    async def clearlog(self, message):
        """ - Удалить лог"""
        fname = self.config["log_filename"]
        async with self._log_lock:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump({"about": "ConstantOnline Dump", "messages": []}, f, indent=4)
        await utils.answer(message, self.strings["log_cleared"])