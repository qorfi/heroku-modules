import os
import zipfile
import subprocess
import datetime
import sys
import shutil

# --- КОНФИГУРАЦИЯ ---
# Путь к папке настроек VS Code (зависит от ОС, пример для Windows)
# Для Linux: os.path.expanduser("~/.config/Code/User")
# Для macOS: os.path.expanduser("~/Library/Application Support/Code/User")
VSCODE_USER_PATH = os.path.join(os.getenv('APPDATA'), 'Code', 'User')

# Путь к локальному клону твоего приватного репозитория
REPO_PATH = r"C:\Path\To\Your\BackupRepo"
BACKUP_FILENAME = "vscode_backup.zip"

def create_zip(source_dir, output_filename): 
    """Архивирует папку в zip файл"""
    zip_path = os.path.join(REPO_PATH, output_filename)
    
    print(f"[*] Архивирование {source_dir} в {zip_path}...")
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:          # Q
            for root, dirs, files in os.walk(source_dir):                           # O
                for file in files:                                                  # R
                    file_path = os.path.join(root, file)                            # F
                    arcname = os.path.relpath(file_path, start=source_dir)          # i
                    zipf.write(file_path, arcname)
        print("[+] Архив создан.")          # q
        return True                         # o
    except Exception as e:                  # r
        print(f"[-] Ошибка архивации: {e}") # f
        return False                        # i

def git_push():
    """Отправляет изменения в GitHub"""
    os.chdir(REPO_PATH)
    
    print("[*] Выполнение git add/commit/push...")
    try:
        status = subprocess.check_output(["git", "status", "--porcelain"])
        if not status:
            print("[!] Изменений нет.")
            return

        subprocess.check_call(["git", "add", BACKUP_FILENAME])
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Backup: {timestamp}"
        
        subprocess.check_call(["git", "commit", "-m", commit_message])
        subprocess.check_call(["git", "push"])
        print("[+] Бэкап успешно отправлен на GitHub.")
        
    except subprocess.CalledProcessError as e:
        print(f"[-] Ошибка Git: {e}")

if __name__ == "__main__":
    if not os.path.exists(VSCODE_USER_PATH):
        print(f"[-] Папка VS Code не найдена: {VSCODE_USER_PATH}")
        sys.exit(1)

    if not os.path.exists(REPO_PATH):
        print(f"[-] Папка репозитория не найдена: {REPO_PATH}")
        sys.exit(1)

    if create_zip(VSCODE_USER_PATH, BACKUP_FILENAME):
        git_push()