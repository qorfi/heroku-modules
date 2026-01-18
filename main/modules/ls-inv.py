# meta developer: Lolix_God
# scope: hikka_only
# scope: hikka_min 1.3.0
# meta version: 1.1.0
import asyncio
import logging
import random
from telethon import errors
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class FinfineMod(loader.Module):
    """
    🚀 Finfine — Ультимативный инструмент рассылки.
    Юзай .binfo для просмотра гайда.
    """
    
    strings = {
        "name": "Finfine",
        "cfg_exclude": "Игнор-лист (ID/Юзернеймы через запятую)",
        "cfg_delay": "Задержка (сек)",
        "cfg_jitter": "Разброс (сек)",
        "cfg_obfuscate": "Обфускация (True/False)",
        
        "no_args": "<b>❌ Ошибка:</b> Введи текст или используй <code>.bc -p пресет</code>",
        "busy": "<b>⚠️ Занято.</b> Используй <code>.bstop</code> для сброса.",
        "start": "<b>🚀 ЗАПУСК</b>\n🎯 Целей: <code>{}</code>\n⏱ Задержка: <code>{}s</code>",
        "stop": "<b>🛑 ПРЕРВАНО.</b>",
        "finish": "<b>🏁 ЗАВЕРШЕНО</b>\n✅ Успешно: <code>{}</code>\n❌ Ошибки: <code>{}</code>\n\n<i>Для отката:</i> <code>.bc -d</code>",
        "test": "🧪 <b>ТЕСТ</b>\n👥 Охват: <code>{}</code>\n📝 Текст: <i>{}</i>\n🖼 Медиа: <code>{}</code>",
        "undoing": "<b>🗑 ОТКАТ...</b>\nУдаляю <code>{}</code> сообщений.",
        
        "info_msg": (
            "<b>📖 ГАЙД ПО Finfine</b>\n\n"
            "<b>основные команды:</b>\n"
            "• <code>.bc <текст> </code> — жахнуть по всем личкам.\n"
            "• <code>.bc -d</code> — <b>ОТКАТ</b> (удалить всё отправленное).\n"
            "• <code>.bc -t <текст> </code> — <b>ТЕСТ</b> (проверка целей без отправки).\n"
            "• <code>.bc -s <текст> </code> — <b>ТИХО</b> (без уведомлений).\n"
            "• <code>.bstop</code> — экстренная остановка.\n\n"
            "<b>пресеты:</b>\n"
            "• <code>.bset <имя> <текст> </code> — сохранить шаблон.\n"
            "• <code>.bc -p <имя> </code> — запуск по шаблону.\n"
            "• <code>.blist</code> — список шаблонов.\n\n"
            "<b>исключения:</b>\n"
            "• Зайди в <code>.cfg Finfine</code> и впиши в <code>exclude_list</code> ID или юзернеймы через запятую."
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "exclude_list", "", self.strings["cfg_exclude"],
            "base_delay", 3.0, self.strings["cfg_delay"],
            "jitter", 1.0, self.strings["cfg_jitter"],
            "obfuscate", True, self.strings["cfg_obfuscate"]
        )
        self.is_running = False

    async def client_ready(self, client, db):
        self.client, self.db = client, db
        if self.db.get("Finfine", "undo_stack") is None:
            self.db.set("Finfine", "undo_stack", [])
        if self.db.get("Finfine", "presets") is None:
            self.db.set("Finfine", "presets", {})

    def _get_excludes(self):
        return [x.strip().replace("@", "").lower() for x in str(self.config["exclude_list"]).split(",") if x.strip()]

    def _draw_progress(self, current, total):
        perc = int(current / total * 100) if total > 0 else 0
        bar_len = 10
        filled = int(bar_len * current / total) if total > 0 else 0
        bar = "■" * filled + "□" * (bar_len - filled)
        return f"<code>[{bar}]</code> {perc}% ({current}/{total})"

    @loader.command(ru_doc="Справка по модулю")
    async def binfo(self, message):
        """Показать гайд по Finfine"""
        await utils.answer(message, self.strings["info_msg"])

    @loader.command(ru_doc="Стоп рассылки")
    async def bstop(self, message):
        self.is_running = False
        await utils.answer(message, self.strings["stop"])

    @loader.command(ru_doc="Сохранить пресет")
    async def bset(self, message):
        args = utils.get_args_raw(message)
        if not args: return await utils.answer(message, "Дай имя и текст.")
        parts = args.split(maxsplit=1)
        name, text = parts[0], parts[1] if len(parts) > 1 else ""
        presets = self.db.get("Finfine", "presets", {})
        presets[name] = {"text": text}
        self.db.set("Finfine", "presets", presets)
        await utils.answer(message, f"<b>✅ Пресет '{name}' сохранен.</b>")

    @loader.command(ru_doc="Список пресетов")
    async def blist(self, message):
        presets = self.db.get("Finfine", "presets", {})
        if not presets: return await utils.answer(message, "Пресеты не найдены.")
        txt = "\n".join([f"🔹 <code>{k}</code>" for k in presets.keys()])
        await utils.answer(message, f"<b>📂 ПРЕСЕТЫ:</b>\n{txt}")

    @loader.command(ru_doc="Рассылка", alias="bc")
    async def broadcast(self, message):
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if "-d" in args:
            stack = self.db.get("Finfine", "undo_stack", [])
            if not stack: return await utils.answer(message, "Нечего удалять.")
            await utils.answer(message, self.strings["undoing"].format(len(stack)))
            for i, (chat, mid) in enumerate(reversed(stack)):
                try: await self.client.delete_messages(chat, mid)
                except: pass
                if i % 20 == 0: await asyncio.sleep(0.3)
            self.db.set("Finfine", "undo_stack", [])
            return await utils.answer(message, "<b>✅ Откат завершен.</b>")

        if self.is_running: return await utils.answer(message, self.strings["busy"])

        is_test, is_silent = "-t" in args, "-s" in args
        clean_text = args.replace("-s", "").replace("-t", "").strip()
        
        if "-p" in clean_text:
            try:
                p_name = clean_text.split("-p")[1].strip().split()[0]
                presets = self.db.get("Finfine", "presets", {})
                clean_text = presets.get(p_name, {}).get("text", "")
                if not clean_text: return await utils.answer(message, "Пресет пуст.")
            except: pass

        if not clean_text and not reply: return await utils.answer(message, self.strings["no_args"])

        excludes = self._get_excludes()
        targets = []
        async for d in self.client.iter_dialogs():
            if d.is_user and not d.entity.bot and not d.entity.is_self:
                uid, un = str(d.entity.id), (str(d.entity.username).lower() if d.entity.username else "")
                if uid not in excludes and un not in excludes:
                    targets.append(d.entity.id)

        if is_test:
            media = "Да" if reply and reply.media else "Нет"
            return await utils.answer(message, self.strings["test"].format(len(targets), clean_text[:50]+"...", media))

        self.is_running = True
        self.db.set("Finfine", "undo_stack", [])
        await utils.answer(message, self.strings["start"].format(len(targets), self.config["base_delay"]))

        sent, err, stack = 0, 0, []
        for i, user_id in enumerate(targets):
            if not self.is_running: break
            try:
                final_txt = clean_text + ("\u200b" * random.randint(1, 3)) if self.config["obfuscate"] else clean_text
                if reply:
                    m = await self.client.send_message(user_id, final_txt or reply.message, file=reply.media, silent=is_silent)
                else:
                    m = await self.client.send_message(user_id, final_txt, silent=is_silent)
                stack.append((user_id, m.id))
                sent += 1
            except errors.FloodWaitError as e: await asyncio.sleep(e.seconds)
            except: err += 1

            if i % 5 == 0 or i == len(targets) - 1:
                progress = self._draw_progress(i + 1, len(targets))
                await utils.answer(message, f"<b>📊 ПРОГРЕСС Finfine:</b>\n{progress}\n✅: <code>{sent}</code> | ❌: <code>{err}</code>")
                self.db.set("Finfine", "undo_stack", stack)

            await asyncio.sleep(max(0.2, self.config["base_delay"] + random.uniform(-self.config["jitter"], self.config["jitter"])))

        self.is_running = False
        await utils.answer(message, self.strings["finish"].format(sent, err))