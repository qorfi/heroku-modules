# meta developer: @znxiw
# scope: hikka_only
# meta version: 1.0.0

from .. import loader, utils
import asyncio

@loader.tds
class JengoMod(loader.Module):
    """Мощный сюр логов групп/чатов/сейв-модов и т.п."""
    strings = {"name": "Jengo"}

    async def xddcmd(self, message):
        """<текст> <кол-во> - зафлудить логи"""
        args = utils.get_args(message)
        
        if len(args) < 2:
            await message.edit("<b>❌ Формат: .xdd <текст> <кол-во></b>")
            return

        text = " ".join(args[:-1])
        count_arg = args[-1]

        if not count_arg.isdigit():
            await message.edit("<b>❌ Количество должно быть числом.</b>")
            return

        iterations = int(count_arg)
        delay = 1.5
        zws = "\u200b"

        for i in range(1, iterations + 1):
            try:
                content = zws * i
                await message.edit(f"{text}{content}")
                await asyncio.sleep(delay)
            except Exception as e:
                await message.respond(f"<b>Error:</b> <code>{str(e)}</code>")
                return