# идея принадлежит @кодермазохист ( реально мазохист )( вроде... нашёл на просторах фхеты ) ,
# его говно-модуль был переработан нижеуказанным девом ( мною ).
# че сделано:
# новое название, выкинул к хуям все костыли, запараллелил запросы к апи, добавил кеширование,
# что в разы уменьшило нагрузку на стороннее апи и работу модуля в целом,
# сделал вывод более приятным глазу, и по мелочи там хуйня какая-то.
#                                                       by @znxiw aka $ынок aka Qorfi Kowalds


# meta developer: @znxiw
# meta banner: https://x0.at/ep0r.jpg
# requires: telegram-stars-rates
# meta version: 2.0.0
import asyncio
import aiohttp
import time
from datetime import datetime
from .. import loader, utils
from telegram_stars_rates import get_stars_rate

@loader.tds
class Pingo(loader.Module):
    """
    Отображение курса telegram stars в TON/USDT/RUB и наоборот.
    """
    
    strings = {
        "name": "Pingo",
        "error": "<blockquote><emoji document_id=6050773179557745617>🫡</emoji> <b><i>Ошибка получения данных. API недоступен.</i></b></blockquote>",
        
        "result": (
            "<blockquote>"
            "<emoji document_id=5951762148886582569>⭐️</emoji> <code>{stars}</code> <b>Stars</b>\n"
            "<emoji document_id=5897692655273383739>⭐</emoji> <code>{ton:.6f}</code> <b>TON</b>\n"
            "<emoji document_id=5402104393396931859>⭐️</emoji> <code>{usdt:.2f}</code> <b>USDT</b>\n"
            "<emoji document_id=5814556334829343625>🪙</emoji> <code>{rub:.2f}</code> <b>RUB</b>"
            "</blockquote>"
            "&#8203;" 
            "<blockquote><emoji document_id=5258113901106580375>⌛️</emoji> <b>Курс актуален на: {time}</b></blockquote>"
        ),
        
        "result_ton": (
            "<blockquote>"
            "<emoji document_id=5424912684078348533>❤️</emoji> <code>{ton}</code> <b>TON</b>\n"
            "<emoji document_id=5402104393396931859>⭐️</emoji> <code>{stars:.2f}</code> <b>Stars</b>\n"
            "<emoji document_id=5897692655273383739>⭐</emoji> <code>{usdt:.2f}</code> <b>USDT</b>\n"
            "<emoji document_id=5814556334829343625>🪙</emoji> <code>{rub:.2f}</code> <b>RUB</b>"
            "</blockquote>"
            "&#8203;"
            "<blockquote><emoji document_id=5258113901106580375>⌛️</emoji> <b>Курс актуален на: {time}</b></blockquote>"
        ),
        
        "invalid": "<blockquote><emoji document_id=6037514847443227774>⭐️</emoji> <b><i>Укажите корректное число звёзд.</i></b></blockquote>",
        "invalid_ton": "<blockquote><emoji document_id=6037514847443227774>💎</emoji> <b><i>Укажите корректное число TON.</i></b></blockquote>",
        "loading": "<blockquote><emoji document_id=6014655953457123498>💱</emoji><b> <i>Считаю курсы...</i></b></blockquote>",
    }

    def __init__(self):
        self._rates_cache = None
        self._rates_ts = 0
        self._cache_ttl = 300  # Кеш живет 5 минут

    async def _get_rates_data(self):
        # Если кеш свежий — используем его
        if self._rates_cache and (time.time() - self._rates_ts < self._cache_ttl):
            return self._rates_cache

        url = "https://tonapi.io/v2/rates?tokens=ton,usdt&currencies=usdt,rub"
        
        async def fetch_api():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            return None
                        return await resp.json()
            except:
                return None

        # Параллельный запрос данных
        api_data, stars_data = await asyncio.gather(
            fetch_api(),
            utils.run_sync(get_stars_rate),
            return_exceptions=True
        )

        # Обработка ошибок: если API упал, пытаемся отдать старый кеш
        if not api_data or isinstance(api_data, Exception) or isinstance(stars_data, Exception):
            if self._rates_cache:
                return self._rates_cache
            return None

        try:
            ton_to_usdt = api_data["rates"]["TON"]["prices"]["USDT"]
            usdt_to_rub = api_data["rates"]["USDT"]["prices"]["RUB"]
            ton_per_star = stars_data["ton_per_star"]
            
            # Обновляем кеш и время
            self._rates_cache = (ton_to_usdt, usdt_to_rub, ton_per_star)
            self._rates_ts = time.time()
            
            return self._rates_cache
        except (KeyError, TypeError):
            if self._rates_cache:
                return self._rates_cache
            return None

    async def _process_conversion(self, message, amount, mode="stars"):
        loading_msg = await utils.answer(message, self.strings["loading"])
        
        rates = await self._get_rates_data()
        if not rates:
            await utils.answer(loading_msg, self.strings["error"])
            return

        ton_to_usdt, usdt_to_rub, ton_per_star = rates
        
        formatted_time = datetime.fromtimestamp(self._rates_ts).strftime('%H:%M:%S')

        if mode == "stars":
            res_stars = amount
            res_ton = ton_per_star * amount
            res_usdt = res_ton * ton_to_usdt
            res_rub = res_usdt * usdt_to_rub
            
            await utils.answer(
                loading_msg, 
                self.strings["result"].format(
                    stars=res_stars, 
                    ton=res_ton, 
                    usdt=res_usdt, 
                    rub=res_rub,
                    time=formatted_time
                )
            )
        
        elif mode == "ton":
            res_ton = amount
            res_stars = amount / ton_per_star
            res_usdt = amount * ton_to_usdt
            res_rub = res_usdt * usdt_to_rub

            await utils.answer(
                loading_msg, 
                self.strings["result_ton"].format(
                    ton=res_ton, 
                    stars=res_stars, 
                    usdt=res_usdt, 
                    rub=res_rub,
                    time=formatted_time
                )
            )

    async def srcmd(self, m):
        """<количество> - конвертация звёзд в TON и другие валюты."""
        args = utils.get_args_raw(m)
        try:
            amount = float(args) if args else None
        except ValueError:
            amount = None

        if amount is None:
            await utils.answer(m, self.strings("invalid"))
            return

        await self._process_conversion(m, amount, mode="stars")
    
    async def tsrcmd(self, m):
        """<количество> - ковертация TON в звёзды и другие валюты."""
        args = utils.get_args_raw(m)
        try:
            amount = float(args) if args else None
        except ValueError:
            amount = None

        if amount is None:
            await utils.answer(m, self.strings("invalid_ton"))
            return

        await self._process_conversion(m, amount, mode="ton")