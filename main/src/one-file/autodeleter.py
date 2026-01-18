# meta developer: @znxiw
# scope: hikka_only
# красивых выводов не будет. разраб в запое
# лицензия чисто по феншую
# ебите эти сурсы как хотите. мне вообще похую

from telethon import events
from telethon.tl.types import User
from .. import loader, utils
import logging

__version__ = (2, 5, 2)

logger = logging.getLogger(__name__)

@loader.tds
class DjamboMod(loader.Module):
    """Автоудаление входящих сообщений в ЛС."""
    
    strings = {
        "name": "Djambo",
        "error_pm": "<blockquote><emoji document_id=5116156972751651938>🖕</emoji> <b>Работает только в ЛС.</b></blockquote>",
        "searching": "<blockquote><emoji document_id=5355051922862653659>🤖</emoji> <b>Чищу историю (только сообщения собеседника)...</b></blockquote>",
        "done": "<blockquote><emoji document_id=5116414868357907335>🔥</emoji> <b>ЧИСТКА ЗАВЕРШЕНА!</b>\n\n<b>Удалено {count} сообщений от собеседника. Твои сообщения целы.</b></blockquote>"
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.active_chats = self.db.get("Djambo", "active_chats", {})

    async def dhcmd(self, message):
        """ - удалить всю историю от собеседника"""
        chat = await message.get_chat()
        
        if not isinstance(chat, User) or chat.bot:
            return await utils.answer(message, self.strings["error_pm"])
            
        target_id = chat.id
        await utils.answer(message, self.strings["searching"])
        
        msgs_to_delete = []
        async for msg in self.client.iter_messages(chat, from_user=target_id):
            msgs_to_delete.append(msg.id)
            
            if len(msgs_to_delete) >= 100:
                await self.client.delete_messages(chat, msgs_to_delete)
                msgs_to_delete = []

        if msgs_to_delete:
            await self.client.delete_messages(chat, msgs_to_delete)

        await message.delete()
        await self.client.send_message(chat, self.strings["done"].format(count="все"))

    async def adhcmd(self, message):
        """ - включить/выключить приём входящих от собеседника"""
        chat = await message.get_chat()
        
        if not isinstance(chat, User) or chat.bot:
            return await utils.answer(message, self.strings["error_pm"])

        chat_id_str = str(chat.id)
        is_active = self.active_chats.get(chat_id_str, False)
        
        if is_active:
            self.active_chats[chat_id_str] = False
            status = "выключено"
        else:
            self.active_chats[chat_id_str] = True
            status = "включено"

        self.db.set("Djambo", "active_chats", self.active_chats)
        
        await utils.answer(message, f"<blockquote><emoji document_id=5193212401188615252>✅</emoji> <b>Автоудаление входящих <u>{status}</u>!</b></blockquote>")

    @loader.watcher(only_messages=True, incoming=True)
    async def watcher(self, message):
        """Воркер: удаляет только входящие в реальном времени"""
        # 1. Проверка на личку
        if not message.is_private or not message.sender_id:
            return

        chat_id_str = str(message.chat_id)
        
        # 2. Проверяем, включен ли режим для этого чата
        if not self.active_chats.get(chat_id_str, False):
            return

        if message.sender_id == message.chat_id:
            try:
                await message.delete()
            except Exception as e:
                logger.error(f"Ошибка удаления: {e}")