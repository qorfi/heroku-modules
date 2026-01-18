# meta developer: GXDEE.t.me
# scope: hikka_only

from .. import loader, utils
from datetime import datetime, timezone, timedelta

__version__ = (1, 2)

@loader.tds
class Midex(loader.Module):
    """
    Отсёт времени до нового года.
    """
    strings = {
        "name": "Midex",
        "help": (
            "<emoji document_id=5215241189665571769>☃️</emoji><b> Команды модуля New Year:</b>\n"
            "<blockquote expandable><b>.new year</b> - показать время до Нового года\n"
            "<b>.new set [часовой пояс]</b> - установить часовой пояс (от -12 до +12)\n"
            "<b>.new add [прямая ссылка/реплай на медиа]</b> - добавить медиафайл\n"
            "<b>.new remove</b> - удалить медиафайл\n\n"
            "<b>Примеры:</b>\n<code>.new set 3</code> - UTC+3 (Москва)\n"
            "<code>.new set -5</code> - UTC-5 (Нью-Йорк)\n"
            "<code>.new add https://example.com/ny.gif</code> - добавить гифку</blockquote>"
        ),
        "template": (
            "<emoji document_id=5212986052662297552>🎩</emoji><b> До Нового {year} года осталось:</b>\n\n"
            "<emoji document_id=5217611071015125647>🎆</emoji><b> Дней: </b><code>{days}</code>\n"
            "<emoji document_id=5217496236474531914>🕯</emoji><b> Часов: </b><code>{hours}</code>\n"
            "<emoji document_id=5215645221534075191>🫐</emoji><b> Минут: </b><code>{minutes}</code>\n"
            "<emoji document_id=5213026914981153242>🎄</emoji><b> Секунд: </b><code>{seconds}</code>\n\n"
            "<blockquote><emoji document_id=5213038163500499521>🍪</emoji><b> Часовой пояс: </b>UTC{tz}\n"
            "<emoji document_id=5213024307936005301>☕️</emoji><b> Текущее время: </b>{time}</blockquote>"
        ),
        "tz_set": "<emoji document_id=5213276280782356417>👌</emoji><b> Часовой пояс установлен: </b>UTC{tz}",
        "media_added": (
            "<emoji document_id=5213276280782356417>👌</emoji><b> Медиафайл добавлен!</b>\n"
            "<blockquote>Теперь он будет отправляться с командой .new year</blockquote>"
        ),
        "invalid_tz": (
            "<emoji document_id=5213225329585325406>😵</emoji><b> Неверный часовой пояс!</b>\n"
            "<blockquote>Используйте число от -12 до +12</blockquote>"
        ),
        "invalid_media": (
            "<emoji document_id=5213225329585325406>😵</emoji><b> Укажите ссылку или реплай!</b>\n"
            "<blockquote>Пример: .new add https://example.com/image.gif</blockquote>"
        ),
        "no_reply": "<emoji document_id=5213225329585325406>😵</emoji><b> В реплае нет медиа!</b>",
        "load_err": "<emoji document_id=5213225329585325406>😵</emoji><b> Не удалось загрузить медиа!</b>",
        "removed": "<emoji document_id=5213478908749449426>❌</emoji><b> Медиафайл удален!</b>",
        "saved_cap": "<emoji document_id=5217839043584230575>🪟</emoji><b> Не удалять - медиа для модуля New Year</b>",
        "gone": (
            "<emoji document_id=5213225329585325406>😵</emoji><b> Медиафайл больше не доступен!</b>\n"
            "<blockquote>Значение в cfg было сброшено.</blockquote>"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "timezone", 3, "часовой пояс (число)",
            "media_url", "", "ссылка на медиа или saved:id",
            "saved_msg_id", 0, "служебная переменная: хранит id сохраненного сообщения"
        )

    def _get_tz_str(self, offset):
        return f"+{offset}" if offset >= 0 else str(offset)

    async def get_saved_media(self, msg_id):
        try:
            msg = await self.client.get_messages("me", ids=msg_id)
            return msg.media if msg and msg.media else None
        except:
            return None

    @loader.command(ru_doc="Инструкция к модулю Midex")
    async def new(self, message):
        """[ year | set | add | remove ] - Управление модулем"""
        args = utils.get_args_raw(message).split()
        cmd = args[0].lower() if args else ""

        if not cmd:
            return await utils.answer(message, self.strings["help"])

        if cmd == "year":
            offset = self.config["timezone"]
            tz = timezone(timedelta(hours=offset))
            now = datetime.now(tz)
            
            target_year = now.year + 1
            ny = datetime(target_year, 1, 1, 0, 0, 0, tzinfo=tz)
            diff = ny - now
            
            text = self.strings["template"].format(
                year=target_year,
                days=diff.days,
                hours=diff.seconds // 3600,
                minutes=(diff.seconds % 3600) // 60,
                seconds=diff.seconds % 60,
                tz=self._get_tz_str(offset),
                time=now.strftime("%d.%m.%Y %H:%M:%S")
            )

            media_src = self.config["media_url"]
            if media_src:
                to_send = media_src
                if media_src.startswith("saved:"):
                    try:
                        saved_id = int(media_src.split(":")[1])
                        to_send = await self.get_saved_media(saved_id)
                    except:
                        to_send = None

                if to_send:
                    try:
                        return await utils.answer(message, text, file=to_send)
                    except:
                        self.config["media_url"] = "" 
                        await utils.answer(message, self.strings["gone"])
                else:
                    self.config["media_url"] = ""
                    await utils.answer(message, self.strings["gone"])
            
            return await utils.answer(message, text)

        elif cmd == "set":
            try:
                val = int(args[1].replace('+', ''))
                if not -12 <= val <= 12: raise ValueError
                self.config["timezone"] = val
                await utils.answer(message, self.strings["tz_set"].format(tz=self._get_tz_str(val)))
            except:
                await utils.answer(message, self.strings["invalid_tz"])

        elif cmd == "add":
            reply = await message.get_reply_message()
            
            if reply and reply.media:
                if self.config["saved_msg_id"]:
                    await self.client.delete_messages("me", self.config["saved_msg_id"])
                
                try:
                    saved = await self.client.send_file("me", reply.media, caption=self.strings["saved_cap"])
                    self.config["saved_msg_id"] = saved.id
                    self.config["media_url"] = f"saved:{saved.id}"
                    await utils.answer(message, self.strings["media_added"], file=reply.media)
                except Exception as e:
                    await utils.answer(message, f"Error: {e}")
            
            elif len(args) > 1:
                url = args[1]
                if self.config["saved_msg_id"]:
                    await self.client.delete_messages("me", self.config["saved_msg_id"])
                    self.config["saved_msg_id"] = 0
                
                try:
                    await utils.answer(message, self.strings["media_added"], file=url)
                    self.config["media_url"] = url
                except:
                    await utils.answer(message, self.strings["load_err"])
            else:
                await utils.answer(message, self.strings["invalid_media"])

        elif cmd == "remove":
            if self.config["saved_msg_id"]:
                await self.client.delete_messages("me", self.config["saved_msg_id"])
            self.config["media_url"] = ""
            self.config["saved_msg_id"] = 0
            await utils.answer(message, self.strings["removed"])

        else:
            await utils.answer(message, self.strings["help"])