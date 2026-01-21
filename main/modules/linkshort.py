# meta developer: @znxiw
# # scope: hikka_only
# scope: hikka_min 3.0.0
# meta version: 1.3.1

import logging
import requests
from io import BytesIO
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class AdvancedLinkMod(loader.Module):
    """
    Модуль для работы со ссылками, QR-кодами и скриншотами сайтов.
    """
    strings = {
        "name": "AdvancedLinkMod",
        "processing": "<b>🔄 Обрабатываю...</b>",
        "error": "<b>❌ Ошибка:</b> {}",
        "no_args": "<b>❌ Нет аргументов. Укажи ссылку или текст.</b>",
        "shot_caption": "📸 <b>Снимок страницы:</b> {}",
        "unshorten_result": "🔗 <b>Расшифрованная ссылка:</b>\n<code>{}</code>"
    }

    async def client_ready(self, client, db):
        self.client = client

    async def mkqrcmd(self, message):
        """<текст/ссылка> - Создать QR-код (отправляет как фото, без текста)"""
        args = utils.get_args_raw(message)
        if not args:
            reply = await message.get_reply_message()
            if reply and reply.text:
                args = reply.text
            else:
                await utils.answer(message, self.strings("no_args"))
                return

        try:
            url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={requests.utils.quote(args)}"
            response = await utils.run_sync(requests.get, url)
            
            if response.status_code != 200:
                await utils.answer(message, self.strings("error").format("API Error"))
                return

            file = BytesIO(response.content)
            file.name = "qr.jpg"

            await message.client.send_file(
                message.to_id,
                file,
                force_document=False,
                reply_to=message.reply_to_msg_id
            )
            
            await message.delete()

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))

    async def unshortcmd(self, message):
        """<ссылка> - Расшифровать сокращенную ссылку (работает с clck.ru и др.)"""
        args = utils.get_args_raw(message)
        if not args:
            reply = await message.get_reply_message()
            if reply and reply.text:
                args = reply.text
            else:
                await utils.answer(message, self.strings("no_args"))
                return

        if not args.startswith("http"):
            args = "https://" + args.strip()

        message = await utils.answer(message, self.strings("processing"))

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = await utils.run_sync(requests.get, args, headers=headers, allow_redirects=True, timeout=10)
            
            final_url = response.url
            
            await utils.answer(message, self.strings("unshorten_result").format(final_url))

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))

    async def webshotcmd(self, message):
        """<ссылка> - Сделать скриншот веб-сайта"""
        args = utils.get_args_raw(message)
        if not args:
            reply = await message.get_reply_message()
            if reply and reply.text:
                args = reply.text
            else:
                await utils.answer(message, self.strings("no_args"))
                return

        if not args.startswith("http"):
            target_url = "https://" + args.strip()
        else:
            target_url = args.strip()

        message = await utils.answer(message, self.strings("processing"))

        try:
            api_url = f"https://image.thum.io/get/width/1200/crop/800/noanimate/{target_url}"
            
            response = await utils.run_sync(requests.get, api_url)
            
            if response.status_code != 200:
                await utils.answer(message, self.strings("error").format("Не удалось получить изображение"))
                return

            file = BytesIO(response.content)
            file.name = "webshot.jpg"

            await message.client.send_file(
                message.to_id,
                file,
                caption=self.strings("shot_caption").format(target_url),
                force_document=False, # Сжатие включено (отправка как фото)
                reply_to=message.reply_to_msg_id
            )
            
            await message.delete()

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))