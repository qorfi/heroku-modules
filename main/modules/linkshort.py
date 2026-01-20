# meta developer: @znxiw
# meta version: 1.2.0
# красивых выводов не будет. разраб в запое
# лицензия чисто по феншую
# ебите эти сурсы как хотите. мне вообще похую

import aiohttp
from .. import loader, utils

@loader.tds
class DolisMod(loader.Module):
    """
    Комбайн для ссылок: сокращатель, дешифратор, QR-коды и Webshot (скриншоты сайтов).
    """

    strings = {
        "name": "Dolis",
        "clck_doc": "Сократить ссылку через clck.ru.\nИспользование: <code>.ls <ссылка></code>",
        "unclck_doc": "Расшифровать (развернуть) сокращенную ссылку.\nИспользование: <code>.unls <ссылка></code>",
        "qr_doc": "Создать QR-код из ссылки или текста.\nИспользование: <code>.qr <текст/ссылка></code>",
        "webshot_doc": "Сделать скриншот сайта.\nИспользование: <code>.webshot <ссылка></code>",
        
        "no_args": "<blockquote><b>Ошибка:</b> Не указана ссылка или текст.</blockquote>",
        "invalid_url": "<blockquote><b>Ошибка:</b> Ссылка должна начинаться с <code>http://</code> или <code>https://</code>.</blockquote>",
        "processing": "<blockquote><b>Обработка...</b></blockquote>",
        "uploading": "<blockquote><b>Генерирую QR-код...</b></blockquote>",
        "shooting": "<blockquote><emoji document_id=5818865084271365343>📸</emoji> <b>Делаю снимок сайта...</b>\n<i>Это может занять пару секунд.</i></blockquote>",
        
        "success_ls": "<blockquote><b>Сокращено:</b> <code>{short_url}</code></blockquote>",
        "success_unls": "<blockquote><b>Расшифровано:</b>\nКороткая: <code>{short}</code></blockquote>",
        
        "api_error": "<blockquote><b>Ошибка API ({status}):</b> Не удалось выполнить запрос.</blockquote>",
        "network_error": "<blockquote><emoji document_id=5116156972751651938>🖕</emoji> <b>Сетевая ошибка:</b> <code>{error}</code></blockquote>"
    }

    CLCK_API_URL = "https://clck.ru/--?url={}"
    QR_API_URL = "https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={}"
    WEBSHOT_API_URL = "https://mini.s-shot.ru/1280x720/JPEG/1280/Z100/?{}"

    async def client_ready(self, client, db):
        self._client = client
        
    @loader.command(ru_doc=lambda self: self.strings("clck_doc"))
    async def lscmd(self, message):
        """<ссылка> - сократить ссылку"""
        args = utils.get_args_raw(message).strip()
        
        if not args:
            return await utils.answer(message, self.strings("no_args"), parse_mode="HTML")

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
            return await utils.answer(message, self.strings("network_error").format(error=str(e)), parse_mode="HTML")

        if shortened_url:
            await utils.answer(message, self.strings("success_ls").format(short_url=shortened_url), parse_mode="HTML")
        else:
            await utils.answer(message, self.strings("api_error").format(status="Empty Response"), parse_mode="HTML")

    @loader.command(ru_doc=lambda self: self.strings("unclck_doc"))
    async def unlscmd(self, message):
        """<ссылка> - расшифровать ссылку"""
        args = utils.get_args_raw(message).strip()

        if not args:
            return await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
        
        if not args.startswith(("http://", "https://")):
            args = "https://" + args

        await utils.answer(message, self.strings("processing"), parse_mode="HTML")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(args, allow_redirects=True) as response:
                    real_url = str(response.url)
            
            await utils.answer(
                message, 
                self.strings("success_unls").format(short=args, original=real_url), 
                parse_mode="HTML"
            )

        except Exception as e:
            return await utils.answer(message, self.strings("network_error").format(error=str(e)), parse_mode="HTML")

    @loader.command(ru_doc=lambda self: self.strings("qr_doc"))
    async def qrcmd(self, message):
        """<текст/ссылка> - создать QR-код"""
        args = utils.get_args_raw(message).strip()
        
        if not args:
            return await utils.answer(message, self.strings("no_args"), parse_mode="HTML")

        await utils.answer(message, self.strings("uploading"), parse_mode="HTML")
        
        qr_url = self.QR_API_URL.format(utils.escape_html(args))
        
        try:
            await utils.answer(message, qr_url, parse_mode="HTML")
        except Exception:
            try:
                await message.delete()
                await message.client.send_file(message.chat_id, qr_url, caption=f"<code>{args}</code>")
            except Exception as e:
                await utils.answer(message, self.strings("network_error").format(error=str(e)), parse_mode="HTML")

    @loader.command(ru_doc=lambda self: self.strings("webshot_doc"))
    async def webshotcmd(self, message):
        """<ссылка> - скриншот сайта"""
        args = utils.get_args_raw(message).strip()
        
        if not args:
            return await utils.answer(message, self.strings("no_args"), parse_mode="HTML")
            
        if not args.startswith(("http://", "https://")):
            args = "http://" + args

        await utils.answer(message, self.strings("shooting"), parse_mode="HTML")
        
        shot_url = self.WEBSHOT_API_URL.format(args)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(shot_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        await message.delete()
                        await message.client.send_file(
                            message.chat_id, 
                            content, 
                            caption=f"<b>Webshot:</b> <code>{args}</code>", 
                            parse_mode="HTML"
                        )
                    else:
                        await utils.answer(
                             message, 
                             self.strings("api_error").format(status=response.status), 
                             parse_mode="HTML"
                        )
        except Exception as e:
            await utils.answer(message, self.strings("network_error").format(error=str(e)), parse_mode="HTML")