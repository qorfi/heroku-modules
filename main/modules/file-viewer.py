# meta developer: @znxiw
# scope: hikka_only
# requires: python-docx pypdf openpyxl

import io
import html
import os
import re
import logging
from telethon.tl.types import MessageMediaDocument
from .. import loader, utils

__version__ = (2, 1, 1)

try:
    import docx
except ImportError:
    docx = None

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import openpyxl
except ImportError:
    openpyxl = None

logger = logging.getLogger(__name__)

@loader.tds
class MonfoMod(loader.Module):
    """
    Ultimate File Reader v2.1 (Fixed by Lolix).
    Supports: DOCX, XLSX, PDF, RTF, JSON, XML, YAML, INI, CSV, SUBTITLES, CODE.
    Features: Smart LRU Cache, Fixed Pagination, Clean UI.
    """
    
    strings = {"name": "Monfo"}
    
    # Максимальное количество файлов в памяти одновременно
    MAX_CACHE_SIZE = 5 

    def __init__(self):
        self._content_cache = {}

    async def client_ready(self, client, db):
        self.client = client

    async def fviewcmd(self, message):
        """<реплай на файл> - Читает форматы: docx, xlsx, pdf, rtf, txt, code..."""
        reply = await message.get_reply_message()
        
        if not reply or not reply.media:
            await utils.answer(message, "<blockquote><b>❌ Мне нужен реплай на файл.</b></blockquote>")
            return

        file_name = "unknown"
        file_ext = ""
        if hasattr(reply.media, 'document'):
            for attr in reply.media.document.attributes:
                if hasattr(attr, 'file_name'):
                    file_name = attr.file_name
                    _, file_ext = os.path.splitext(file_name)
                    file_ext = file_ext.lower()

        status_msg = await utils.answer(message, f"<blockquote><b>📥 Читаю {file_ext}...</b></blockquote>")
        
        if reply.file.size > 15 * 1024 * 1024:
            await utils.answer(status_msg, "<blockquote><b>❌ Файл слишком большой (>15MB).</b></blockquote>")
            return

        file_bytes = await reply.download_media(file=io.BytesIO())
        file_bytes.seek(0)
        content = ""

        # === ПАРСИНГ ===
        try:
            if file_ext == ".docx" and docx:
                doc = docx.Document(file_bytes)
                content = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                if not content: content = "[DOCX пуст]"

            elif file_ext in [".xlsx", ".xlsm"] and openpyxl:
                wb = openpyxl.load_workbook(file_bytes, data_only=True)
                sheet = wb.active
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    rows.append(" | ".join([str(c) if c is not None else "" for c in row]))
                content = "\n".join(rows)

            elif file_ext == ".pdf" and pypdf:
                try:
                    pdf_reader = pypdf.PdfReader(file_bytes)
                    content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                except Exception:
                    content = "[PDF Error: Невозможно извлечь текст]"

            elif file_ext == ".rtf":
                raw_rtf = file_bytes.read().decode('utf-8', errors='ignore')
                content = re.sub(r"{\*?\\[^{}]+}|[{}]|\\\n?[A-Za-z]+\n?(?:-?\d+)?[ ]?", "", raw_rtf)
                content = "\n".join([l for l in content.splitlines() if l.strip()])

            else:
                raw_data = file_bytes.read()
                for enc in ['utf-8', 'windows-1251', 'cp866', 'latin-1']:
                    try:
                        content = raw_data.decode(enc)
                        break
                    except UnicodeDecodeError:
                        continue
            
            if not content or not content.strip():
                content = "[Файл пуст или формат не поддерживается]"

        except Exception as e:
            await utils.answer(status_msg, f"<blockquote><b>❌ Ошибка парсинга:</b> {e}</blockquote>")
            return

        max_chars = 3000
        safe_content = html.escape(content)
        pages = [safe_content[i:i + max_chars] for i in range(0, len(safe_content), max_chars)]
        
        # LRUСС
        if len(self._content_cache) >= self.MAX_CACHE_SIZE:
            first_key = next(iter(self._content_cache))
            del self._content_cache[first_key]

        msg_id = status_msg.id
        self._content_cache[msg_id] = {
            "pages": pages,
            "name": file_name,
            "total": len(pages)
        }
        
        await self._render_page(status_msg, 1, msg_id)

    async def _render_page(self, message, page_num, msg_id):
        """
        Рендерит страницу.
        :param message: Объект сообщения (или call) для редактирования.
        :param page_num: Номер страницы.
        :param msg_id: ID сообщения в кэше (ключ).
        """
        if msg_id not in self._content_cache:
            await utils.answer(message, "<blockquote><b>❌ Кэш очищен или устарел. Откройте файл заново.</b></blockquote>")
            return

        data = self._content_cache[msg_id]
        pages = data["pages"]
        total = data["total"]
        
        page_num = max(1, min(page_num, total))
        chunk = pages[page_num - 1]
        
        text = (
            f"<blockquote><b>📂 Файл:</b> <code>{data['name']}</code>\n</blockquote>"
            f"<blockquote><b>📄 Страница:</b> <code>{page_num} / {total}</code>\n</blockquote>"
            f"{'—'*20}\n"
            f"<blockquote><code>{chunk}</code></blockquote>"
        )

        buttons = []
        row_nav = []

        if total > 1:
            # Логика кнопок: [Первая] [Пред] [След] [Последняя]

            # 1. Первая (показываем, если мы дальше 2-й страницы)
            if page_num > 2:
                row_nav.append({"text": "« 1", "callback": self._cb_page, "args": (msg_id, 1)})

            # 2. Предыдущая (показываем, если мы не на 1-й)
            if page_num > 1:
                row_nav.append({"text": f"‹ {page_num - 1}", "callback": self._cb_page, "args": (msg_id, page_num - 1)})

            # 3. Следующая (показываем, если мы не на последней)
            if page_num < total:
                row_nav.append({"text": f"{page_num + 1} ›", "callback": self._cb_page, "args": (msg_id, page_num + 1)})

            # 4. Последняя (показываем, если мы не на пред-последней и не на последней)
            if page_num < total - 1:
                row_nav.append({"text": f"{total} »", "callback": self._cb_page, "args": (msg_id, total)})
            
            if row_nav:
                buttons.append(row_nav)

        buttons.append([{"text": "❌ Закрыть", "callback": self._cb_close, "args": (msg_id,)}])

        await utils.answer(message, text, reply_markup=buttons)

    async def _cb_page(self, call, msg_id, page_num):
        await self._render_page(call, page_num, msg_id)

    async def _cb_close(self, call, msg_id):
        if msg_id in self._content_cache:
            del self._content_cache[msg_id]
        await call.delete()