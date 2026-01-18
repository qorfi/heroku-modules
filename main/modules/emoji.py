# meta developer: @znxiw
# scope: hikka_only
# requires: emoji

import random
import emoji
from .. import loader, utils

__version__ = (1, 1, 1)

@loader.tds
class SinksMod(loader.Module):
    """говно-модуль от $ынка (aka @znxiw aka Qorfi Kowalds aka Б0r aka H3qo₽Ф1l aka Wenis aka 3bb)а|-|A₸ aka kOt-kOkOs aka не помню свой адрес aka забыл своё имя aka потерянный в депрессии aka дохуя ников aka хуесос с 300000000 ликами aka TPAXOДPOM aka казах ест лошадь.) плю-плю-плю-плю"""
    
    strings = {
        "name": "Sinks",
        "usage": "<b>❌ Использование:</b> <code>{}sg [кол-во] [эмодзи]</code>",
        "error_count": "<b>❌ Ошибка:</b> Введи корректное число символов.",
        "error_pool": "<b>❌ Ошибка:</b> Нужно хотя бы 2-3 разных эмодзи для генерации."
    }

    async def sgcmd(self, message):
        """[кол-во] [эмодзи] - генерация хаоса без повторов с динамическим префиксом"""
        prefix = self.get_prefix() 
        args = utils.get_args(message)
        
        if len(args) < 2:
            await utils.answer(message, self.strings("usage").format(prefix))
            return

        try:
            count = int(args[0])
            emoji_pool = emoji.distinct_emoji_list(" ".join(args[1:]))
            
            if len(emoji_pool) < 2:
                await utils.answer(message, self.strings("error_pool"))
                return
        except ValueError:
            await utils.answer(message, self.strings("error_count"))
            return

        result = []
        last_emoji = None
        
        glitch_chars = ["\u200b", "\ufe0f", "\u200d"] 

        for _ in range(count):
            available = [e for e in emoji_pool if e != last_emoji]
            current = random.choice(available)
            
            if random.random() < 0.05:
                current += random.choice(glitch_chars)
                
            result.append(current)
            last_emoji = current

        await utils.answer(message, "".join(result))