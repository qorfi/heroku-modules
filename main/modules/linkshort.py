# meta developer: @znxiw
# meta version: 1.0.4
# красивых выводов не будет. разраб в запое
# лицензия чисто по феншую
# ебите эти сурсы как хотите. мне вообще похую

import aiohttp
from .. import loader, utils

@loader.tds
class DolisMod(loader.Module):
    """
    Простой и быстрый сократитель ссылок, использующий сервис clck.ru.
    """

    strings = {
        "name": "Dolis",
        "clck_doc": "Сократить ссылку через clck.ru.\nИспользование: <code>.ls <ссылка></code>",
        
        "no_url": "<blockquote><b>Ошибка:</b> Не указана ссылка для сокращения.</blockquote>",
        "invalid_url": "<blockquote><b>Ошибка:</b> Ссылка должна начинаться с <code>http://</code> или <code>https://</code>.</blockquote>",
        "processing": "<blockquote><b>Сокращаю ссылку...</b></blockquote>",
        
        "success": "<blockquote><b>Сокращено:</b> <code>{short_url}</code></blockquote>",
        "api_error": "<blockquote><b>Ошибка API ({status}):</b> Не удалось сократить ссылку.</blockquote>",
        "network_error": "<blockquote><emoji document_id=5116156972751651938>🖕</emoji> <b>Сетевая ошибка:</b> <code>{error}</code></blockquote>"
    }

    CLCK_API_URL = "https://clck.ru/--?url={}"

    async def client_ready(self, client, db):
        self._client = client
        
    @loader.command(ru_doc=lambda self: self.strings("clck_doc"))
    async def lscmd(self, message):
        """- сократить ссылку"""
        
        args = utils.get_args_raw(message).strip()
        
        if not args:
            return await utils.answer(message, self.strings("no_url"), parse_mode="HTML")

        if not args.startswith(("http://", "https://")):
            return await utils.answer(message, self.strings("invalid_url"), parse_mode="HTML")

        await utils.answer(message, self.strings("processing"), parse_mode="HTML")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.CLCK_API_URL.format(args)) as response:
                    
                    if response.status != 200:
                        return await utils.answer(
                            message, 
                            self.strings("api_error").format(status=response.status), 
                            parse_mode="HTML"
                        )
                    
                    shortened_url = (await response.text()).strip()

        except Exception as e:
            return await utils.answer(
                message, 
                self.strings("network_error").format(error=str(e)), 
                parse_mode="HTML"
            )

        if shortened_url:
            await utils.answer(
                message,
                self.strings("success").format(
                    short_url=shortened_url,
                    original_url=args
                ),
                parse_mode="HTML"
            )
        else:
            await utils.answer(
                message,
                self.strings("api_error").format(status="Empty Response"),
                parse_mode="HTML"
            )