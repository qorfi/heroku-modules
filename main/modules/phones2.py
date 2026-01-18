#---------------------!!------------!!---------------------#
#                     source by @znxiw                     #
#---------------------!!------------!!---------------------#
#                         АНЕКДОТ                          #
#---------------------!!------------!!---------------------#
#     - Моя девушка в постели представляет, что ей 14      #
#                       - Зачем?..                         #
#        - Не знаю. Может, хочет казаться старше           #
#---------------------!!------------!!---------------------#
# meta developer: @znxiw
# Requires: hikkatl
# meta version: 1.4.9
import random
import re
import aiohttp
from hikkatl.types import Message
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact, PeerUser, User
from telethon.errors import FloodWaitError, RPCError
from .. import loader, utils

class NullLogger:
    def exception(self, *args, **kwargs):
        """заглушка .exception()."""
        pass
    def warning(self, *args, **kwargs):
        """заглушка .warning()."""
        pass
    def error(self, *args, **kwargs):
        """заглушка .error()."""
        pass


@loader.tds
class FlexixMod(loader.Module):
    """
    Выдает случайный российский номер, проверяет его регистрацию в Telegram,с.
    """

    strings = {
        "name": "Flexix",
        "phone_doc": "Выдает случайный российский номер и проверяет его регистрацию в Telegram.",

        "phone_result": "<blockquote><emoji document_id=5341479130422603611>😼</emoji> <b>Случайный номер:</b> {0}\n<emoji document_id=5258332798409783582>🚀</emoji> <b>Status:</b> <code>{1}</code>{2}</blockquote>",

        "region_info": "<blockquote><emoji document_id=5125286720308249351>💀</emoji> <b>Регион:</b> <code>{region}</code>\n<emoji document_id=5303400229549135579>🌅</emoji> <b>Оператор:</b> <code>{operator}</code></blockquote>",
        "region_error": "<blockquote><emoji document_id=5933764569469031506>👎</emoji> <code>Ошибка при запросе к внешнему API.</code></blockquote>",

        "flood_wait": "<blockquote><emoji document_id=5116156972751651938>🖕</emoji> <b>Внимание:</b>\n<code>Превышен лимит запросов к Telegram API. Повторите попытку позже.</code></blockquote>",
        "import_error": "<blockquote><emoji document_id=5933764569469031506>👎</emoji> <b>Ошибка:</b>\n<code>Не удалось импортировать контакт.</code></blockquote>",
        
        # Строки для управления кодами
        "rpe_doc": "Управляет списком кодов операторов РФ (DEF-кодов).\nИспользование:\n <code>{prefix}rpe &lt;+|-&gt; &lt;код&gt;</code>\n <code>{prefix}rpe &lt;+|-&gt; all</code> (вернуть дефолт/очистить)",
        "invalid_args": "<blockquote><b>Неверный формат. Используйте:</b> <code>{prefix}rpe &lt;+ / -&gt; &lt;код | all&gt;</code>.</blockquote>",
        "invalid_code": "<blockquote>Код <code>{code}</code> должен содержать ровно 3 цифры.</blockquote>",
        "code_added": "<blockquote><emoji document_id=5192963112696822273>✅</emoji> <b>Код</b> <code>{code}</code> <b>добавлен в список.</b></blockquote>",
        "code_removed": "<blockquote><emoji document_id=5192963112696822273>✅</emoji> <b>Код</b> <code>{code}</code> <b>удален из списка.</b></blockquote>",
        "code_exists": "<blockquote><emoji document_id=5933764569469031506>👎</emoji> <b>Код</b> <code>{code}</code> <b>уже есть в списке.</b></blockquote>",
        "code_not_exists": "<blockquote><emoji document_id=5933764569469031506>👎</emoji> <b>Кода</b> <code>{code}</code> <b>нет в списке.</b></blockquote>",
        
        "current_codes_header": "<blockquote><emoji document_id=5217890643321300022>✈️</emoji> <b>Текущие DEF-коды ({count}):</b></blockquote>",
        "current_codes_list": "<blockquote><code>{codes}</code></blockquote>",

        "all_restored": "<blockquote><emoji document_id=5192963112696822273>✅</emoji> <b>Список DEF-кодов</b> <b>восстановлен</b> до значений по умолчанию.</blockquote>",
        "all_cleared": "<blockquote><emoji document_id=5192963112696822273>✅</emoji> <b>Список DEF-кодов</b> <b>полностью очищен.</b></blockquote>",
        "already_empty": "<blockquote><emoji document_id=5933764569469031506>👎</emoji> <b>Список DEF-кодов</b> уже пуст.</blockquote>",
        # T-ID для вывода, если найден.
        "user_id_output": "\n<emoji document_id=5416064102260811352>🦾</emoji> <b>ID:</b> <code>{user_id}</code>",
        
        # Желания с разметкой ебаться нет.
        "rpi_info_1": "<blockquote><emoji document_id=5352629969329610635>✝️</emoji> <b>Flexix создан в <u>развлекательных</u> целях.</b></blockquote>",
        "rpi_info_2": "<blockquote><emoji document_id=4904936030232117798>⚙️</emoji> <b>{prefix}rp</b> - генерирует случайный номер.</blockquote>",
        "rpi_info_3": "<blockquote><emoji document_id=4904936030232117798>⚙️</emoji> <b>{prefix}rpe</b> - управление списком DEF-кодов (первые 3 цифры номера после +7), которые используются для генерации номеров.\n\n</b>Примеры:</b>\n<code>{prefix}rpe + 903</code>\n<code>{prefix}rpe - 903</code>\n<code>{prefix}rpe + all</code> (восстановить список)\n<code>{prefix}rpe - all</code> (очистить список)</blockquote>",
        "rpi_info_4": "<blockquote><emoji document_id=5472009448610353211>💗</emoji> <b>Developer:</b> <code>@znxiw</code></blockquote>",
    }

    DEFAULT_DEF_CODES = [
        "910", "911", "912", "913", "914", "915", "916", "917", "918", "919", 
        "980", "981", "982", "983", "984", "985", "986", "987", "988", "989",
        "903", "905", "906", "909", 
        "960", "961", "962", "963", "964", "965", "966", "967", "968", "969",
        "920", "921", "922", "923", "924", "925", "926", "927", "928", "929", 
        "930", "931", "932", "933", "934", "936", "937", "938", "939",
        "900", "901", "902", "904", "908", 
        "950", "951", "952", "953", "954", "955", "956", "958", "959",
        "977", 
        "991", "992", "993", "994", "995", "996", "997", "999",
        "941", "942", "949", "970", "971", "978", "979"
    ]
    
    def __init__(self):
        super().__init__()
        self._db = None
        self._client = None
        self.def_codes = [] 

        if not hasattr(self, 'logger'):
            self.logger = NullLogger()

    def _save_codes(self):
        """Сохраняет текущий список кодов в DB."""
        self._db.set(self.strings["name"], "def_codes", self.def_codes)

    def _load_codes(self):
        """Загружает список кодов из DB, или использует список по умолчанию."""
        self.def_codes = self._db.get(self.strings["name"], "def_codes", self.DEFAULT_DEF_CODES)
        
    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._load_codes() 

    @loader.command(ru_doc=lambda self: "Информация по командам модуля")
    async def rpi(self, message: Message):
        """- вывод информации по модулю"""
        
        prefix = self.get_prefix()
        separator = "&#8203;" 
        
        first_quote = self.strings["rpi_info_1"]
        second_quote = self.strings["rpi_info_2"].format(prefix=prefix)
        third_quote = self.strings["rpi_info_3"].format(prefix=prefix)
        fourth_quote = self.strings["rpi_info_4"]
        
        final_output = first_quote + separator + second_quote + separator + third_quote + separator + fourth_quote

        await utils.answer(
            message, 
            final_output,
            parse_mode="HTML"
        )

    @loader.command(ru_doc=lambda self: self.strings("phone_doc"))
    async def rpcmd(self, message: Message):
        """- выдает случайный номер"""
        
        if not self.def_codes:
            prefix = self.get_prefix()
            return await utils.answer(message, f"<blockquote><b>Ошибка:</b> Список DEF-кодов пуст. Используйте <code>{prefix}rpe + all</code>, чтобы вернуть коды по умолчанию.</blockquote>", parse_mode="HTML")

        # 1. Генерация номера
        operator_code = random.choice(self.def_codes)
        remaining_digits = str(random.randint(0, 9999999)).zfill(7)
        phone_number_raw = f"+7{operator_code}{remaining_digits}"
        
        status_text = "Not Telegram user"
        user_entity_id = None 
        id_output_text = ""
        region_output_text = ""

        # 2. API 
        api_url = "http://num.voxlink.ru/get/"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, params={'num': phone_number_raw}, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        region_name = data.get('region', 'Неизвестно')
                        operator_name = data.get('operator', 'Неизвестно')
                        
                        if operator_name == 'ВЫМПЕЛКОМ': # new
                            operator_name = 'Билайн' # new
                        if operator_name == 'МЕГАФОН': # new
                            operator_name = 'Мегафон' # new
                        
                        region_output_text = self.strings["region_info"].format(
                            region=region_name, 
                            operator=operator_name
                        )
                    else:
                        self.logger.warning(f"Внешний API вернул статус: {resp.status}")
                        region_output_text = self.strings["region_error"]
        except Exception:
            self.logger.exception("Ошибка при запросе к внешнему API (voxlink.ru).")
            region_output_text = self.strings["region_error"]


        # 3. Проверка регистрации в Telegram 
        contact = InputPhoneContact(
            client_id=random.randrange(2**63),
            phone=phone_number_raw,
            first_name="Check",
            last_name="User"
        )
        
        try:
            result = await self._client(ImportContactsRequest(contacts=[contact]))
            
            if result.users:
                user: User = result.users[0]
                status_text = "Telegram user"
                user_entity_id = user.id
                id_output_text = self.strings["user_id_output"].format(user_id=user_entity_id)
            else:
                status_text = "Not Telegram user"
                
        except FloodWaitError:
            return await utils.answer(message, self.strings("flood_wait"), parse_mode="HTML")

        except RPCError as e:
            self.logger.error(f"RPC Error при импорте контакта: <code>{e}</code>")
            status_text = f"API Error: <code>{type(e).__name__}</code>"
            return await utils.answer(message, self.strings("import_error"), parse_mode="HTML")
            
        except Exception:
            self.logger.exception("Неизвестная ошибка при проверке номера через импорт.")
            status_text = "Unknown Error"
            
        finally:
            # 4. ОБЯЗАТЕЛЬНЫЙ ШАГ: Удаление контакта
            if user_entity_id:
                try:
                    delete_peer = PeerUser(user_entity_id)
                    await self._client(DeleteContactsRequest(id=[delete_peer]))
                except Exception:
                    self.logger.exception(f"Не удалось удалить контакт ID {user_entity_id}.")

        # 5. Вывод результата
        
        first_quote = self.strings["phone_result"].format(
            phone_number_raw, status_text, id_output_text
        )
        
        separator = "&#8203;" 
        
        second_quote = region_output_text
        
        final_output = first_quote + separator + second_quote

        await utils.answer(
            message, 
            final_output,
            parse_mode="HTML"
        )
        
    @loader.command(ru_doc=lambda self: self.strings("rpe_doc"))
    async def rpe(self, message: Message):
        """- управляет списком кодов операторов РФ (DEF-кодов)"""
        args = utils.get_args_raw(message).strip().lower()
        prefix = self.get_prefix()
        
        if not args:
            codes_list = ", ".join(sorted(self.def_codes))
            
            header_quote = self.strings["current_codes_header"].format(count=len(self.def_codes))
            
            separator = "&#8203;"
            
            codes_quote = self.strings["current_codes_list"].format(codes=codes_list)
            
            final_output = header_quote + separator + codes_quote
            
            return await utils.answer(
                message, 
                final_output,
                parse_mode="HTML"
            )

        # 2. Обработка обычного добавления/удаления кода
        
        # 1. Проверка на полное управление списком: + all или - all
        if args == "+ all":
            self.def_codes = list(self.DEFAULT_DEF_CODES)
            self.def_codes.sort()
            self._save_codes()
            return await utils.answer(message, self.strings("all_restored"), parse_mode="HTML")

        elif args == "- all":
            # Полная очистка списка
            if not self.def_codes:
                return await utils.answer(message, self.strings("already_empty"), parse_mode="HTML")
                
            self.def_codes = []
            self._save_codes()
            return await utils.answer(message, self.strings("all_cleared"), parse_mode="HTML")

        # 2. Обработка обычного добавления/удаления кода
        match = re.match(r"^\s*([+-])\s*(\d{3})\s*$", args)

        if not match:
            return await utils.answer(message, self.strings("invalid_args").format(prefix=prefix), parse_mode="HTML")

        action, code = match.groups()

        # чек-ин
        if len(code) != 3 or not code.isdigit():
            return await utils.answer(message, self.strings("invalid_code").format(code=code), parse_mode="HTML")

        if action == "+":
            if code not in self.def_codes:
                self.def_codes.append(code)
                self.def_codes.sort()
                self._save_codes()
                return await utils.answer(message, self.strings("code_added").format(code=code), parse_mode="HTML")
            else:
                return await utils.answer(message, self.strings("code_exists").format(code=code), parse_mode="HTML")
        
        elif action == "-":
            if code in self.def_codes:
                self.def_codes.remove(code)
                self._save_codes()
                return await utils.answer(message, self.strings("code_removed").format(code=code), parse_mode="HTML")
            else:
                return await utils.answer(message, self.strings("code_not_exists").format(code=code), parse_mode="HTML")