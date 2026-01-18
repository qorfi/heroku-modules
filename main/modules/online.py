# meta developer: @znxiw
# scope: hikka_only
# name: ConstantOnline
# meta version: 1.1.0

import asyncio
import random
import logging
import json
import os
import time
from datetime import datetime
from telethon import functions, types
from .. import loader, utils

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
        "log_cleared": "<b>🗑 Log file has been purged.</b>",
        "stats": (
            "<blockquote><b>📊 Online Statistics</b>\n\n"
            "Running since: <b>{}</b>\n"
            "Uptime: <b>{}</b>\n"
            "Messages Logged (Session): <b>{}</b></blockquote>"
        ),
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "interval", 20, "Интервал (сек). Рекомендуется 20-30.",
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
        self._start_time = None
        self._session_logs = 0

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
                try:
                    with open(fname, "w", encoding="utf-8") as f:
                        json.dump({"about": "ConstantOnline Dump", "messages": []}, f, indent=4)
                except OSError as e:
                    logger.error(f"Failed to init log file: {e}")

    async def _start_loop(self):
        if self._task:
            self._task.cancel()
        self._start_time = time.time()
        self._session_logs = 0
        self._task = asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            try:
                # убрал ебаный "ъ" / добавил обработку ошибок запросов
                await self._client(functions.account.GetPrivacyRequest(
                    key=types.InputPrivacyKeyStatusTimestamp()
                ))
                await self._client(functions.account.UpdateStatusRequest(offline=False))
                
                sleep_time = self.config["interval"] + random.randint(5, 15)
                await asyncio.sleep(sleep_time)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Online worker error: {e}")
                await asyncio.sleep(15)

    async def _log_message(self, message, sender):
        if not self.config["enable_logging"]:
            return

        fname = self.config["log_filename"]
        
        sender_name = "Unknown"
        if sender:
            first = getattr(sender, 'first_name', '') or ""
            last = getattr(sender, 'last_name', '') or ""
            sender_name = f"{first} {last}".strip()

        msg_obj = {
            "id": message.id,
            "type": "message",
            "date": message.date.isoformat(),
            "date_unixtime": str(int(message.date.timestamp())),
            "from": sender_name,
            "from_id": f"user{sender.id}" if sender else "unknown",
            "text": message.text or "",
            "text_entities": [] 
        }

        async with self._log_lock:
            try:
                # читаем -> обновляем -> перезаписываем
                if os.path.exists(fname):
                    with open(fname, "r", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            data = {"about": "ConstantOnline Dump", "messages": []}
                else:
                    data = {"about": "ConstantOnline Dump", "messages": []}

                data["messages"].append(msg_obj)
                
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                
                self._session_logs += 1
            except Exception as e:
                logger.error(f"Log Error: {e}")

    def _is_exempt(self, user_id, username):
        exempt = str(self.config["exempt_users"]).split()
        uid_str = str(user_id)
        if uid_str in exempt:
            return True
        if username:
            u_clean = username.lstrip("@").lower()
            exempt_clean = [u.lstrip("@").lower() for u in exempt]
            if u_clean in exempt_clean:
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

        # 2. Имитация активности
        try:
            if self.config["auto_typing"] or self.config["enable_game"]:
                content_len = len(message.text or "")
                delay = min(max(content_len // 10, 2), 6)
                
                if self.config["enable_game"]:
                    await self._client(functions.messages.SetTypingRequest(
                        peer=message.chat_id,
                        action=types.SendMessageGamePlayAction()
                    ))
                else:
                    await self._client(functions.messages.SetTypingRequest(
                        peer=message.chat_id,
                        action=types.SendMessageTypingAction()
                    ))
                
                await asyncio.sleep(delay)
        except Exception:
            pass

        # 3. Авточтение (Исправлено)
        if self.config["auto_read"]:
            try:
                # Использование max_id гарантирует, что диалог пометится прочитанным
                await self._client.send_read_acknowledge(
                    message.chat_id,
                    max_id=message.id,
                    clear_mentions=True
                )
            except Exception as e:
                logger.debug(f"Auto-read failed: {e}")

    @loader.command()
    async def online(self, message):
        """- Включить/выключить режим"""
        state = not self._db.get(self.strings["name"], "status", False)
        self._db.set(self.strings["name"], "status", state)
        if state:
            await self._start_loop()
            log_status = "ON" if self.config["enable_logging"] else "OFF"
            game_status = self.config["game_title"] if self.config["enable_game"] else "OFF"
            await utils.answer(message, self.strings["on"].format(log_status, game_status))
        else:
            if self._task:
                self._task.cancel()
            self._start_time = None
            await self._client(functions.account.UpdateStatusRequest(offline=True))
            await utils.answer(message, self.strings["off"])

    @loader.command()
    async def dumplog(self, message):
        """- Выгрузить лог (JSON)"""
        fname = self.config["log_filename"]
        if not os.path.exists(fname):
            return await utils.answer(message, self.strings["no_logs"])
        
        count = 0
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
                count = len(data.get("messages", []))
        except Exception:
            pass

        await utils.answer(message, self.strings["dump_caption"].format(count))
        await self._client.send_file(
            message.chat_id,
            fname,
            caption=f"Dump generated at {datetime.now().strftime('%H:%M:%S')}"
        )

    @loader.command()
    async def clearlog(self, message):
        """- Очистить лог"""
        fname = self.config["log_filename"]
        async with self._log_lock:
            with open(fname, "w", encoding="utf-8") as f:
                json.dump({"about": "ConstantOnline Dump", "messages": []}, f, indent=4)
        self._session_logs = 0
        await utils.answer(message, self.strings["log_cleared"])

    @loader.command()
    async def onlinestats(self, message):
        """- Показать статистику текущей сессии"""
        if not self._start_time or not self._db.get(self.strings["name"], "status", False):
            return await utils.answer(message, "<b>Система сейчас выключена.</b>")
            
        uptime_seconds = int(time.time() - self._start_time)
        uptime_str = str(datetime.utcfromtimestamp(uptime_seconds).strftime('%H:%M:%S'))
        start_date = datetime.fromtimestamp(self._start_time).strftime('%Y-%m-%d %H:%M:%S')
        
        await utils.answer(message, self.strings["stats"].format(
            start_date,
            uptime_str,
            self._session_logs
        ))