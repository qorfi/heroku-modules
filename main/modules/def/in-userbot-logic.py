# meta developer: @znxiw
# meta name: VSCodeBackup
# meta description: Автоматически скачивает бэкап VSCode из репозитория GitHub.
# meta version: 1.0.0

import io
import requests
from .. import loader, utils

@loader.tds
class VSCodeBackupMod(loader.Module):
    
    strings = {
        "name": "VSCodeBackup",
        "cfg_repo": "Ссылка на репозиторий (формат: username/repository)",
        "cfg_token": "Твой GitHub Personal Access Token",
        "cfg_chat_id": "ID чата для отправки бэкапа (0 = текущий/избранное)",
        "cfg_filename": "Имя файла в репозитории (по умолчанию vscode_backup.zip)",
        "no_config": "🚫 <b>Конфиг не настроен!</b> Укажите репозиторий и токен в .config.",
        "downloading": "🔄 <b>Скачиваю бэкап из GitHub...</b>",
        "uploading": "📤 <b>Отправляю в чат...</b>",
        "error": "❌ <b>Ошибка:</b> {}",
        "success": "✅ <b>Бэкап VS Code успешно получен!</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "repo",
                None,
                lambda: self.strings("cfg_repo"),
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "github_token",
                None,
                lambda: self.strings("cfg_token"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "backup_chat_id",
                0,
                lambda: self.strings("cfg_chat_id"),
                validator=loader.validators.Integer()
            ),
            loader.ConfigValue(
                "filename",
                "vscode_backup.zip",
                lambda: self.strings("cfg_filename"),
                validator=loader.validators.String()
            )
        )

    async def client_ready(self, client, db):
        self.client = client

    @loader.command(ru_doc="Принудительно скачать и отправить бэкап")
    async def getbackup(self, message):
        """Скачивает бэкап из репозитория и отправляет в чат."""
        repo = self.config["repo"]
        token = self.config["github_token"]
        filename = self.config["filename"]
        target_chat = self.config["backup_chat_id"]

        if not repo or not token:
            await utils.answer(message, self.strings("no_config"))
            return

        if target_chat == 0:
            target_chat = message.chat_id

        await utils.answer(message, self.strings("downloading"))

        api_url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw"
        }

        try:
            response = requests.get(api_url, headers=headers, stream=True)
            
            if response.status_code != 200:
                await utils.answer(message, self.strings("error").format(f"GitHub API Error: {response.status_code} - {response.reason}"))
                return

            file_bytes = io.BytesIO(response.content)
            file_bytes.name = filename

            await utils.answer(message, self.strings("uploading"))
            
            # Отправка файла
            await self.client.send_file(
                target_chat,
                file_bytes,
                caption=self.strings("success")
            )
            
            await message.delete()

        except Exception as e:
            await utils.answer(message, self.strings("error").format(str(e)))