# 🌌 Orion Telegram Bot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![aiogram 3.x](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg?logo=telegram&logoColor=white)](https://github.com/aiogram/aiogram)

**Orion** is a lightweight, secure, and bidirectional file transfer bridge between your Linux VPS / server and Telegram.

Easily transfer files back and forth:
- **Auto-save incoming files:** Send any file, document, video, or picture to your bot on Telegram — it automatically saves it to `downloads/` on your VPS.
- **Fetch & Send files:** Request files from your VPS by command (`/send <path>`, `/get <filename>`, or `/list` with 1-tap download buttons).
- **Strict Authorization:** Only user IDs explicitly configured in `ALLOWED_USERS` are granted access.
- **Production Ready:** Includes a single interactive `deploy.sh` script that automatically sets up the environment and registers a systemd service.

---

## ⚡ Quick Deployment (Single Command)

Clone the repository and run the interactive deploy script:

```bash
git clone https://github.com/wymthw1n/orionbot.git
cd orionbot
sudo bash deploy.sh
```

The script will interactively ask for your configuration:
1. **`Target Directory`**: Production `/opt/orionbot` or current directory.
2. **`BOT_TOKEN`**: Your bot token from [@BotFather](https://t.me/BotFather).
3. **`ALLOWED_USERS`**: Your Telegram numeric user ID(s) (find yours via [@userinfobot](https://t.me/userinfobot)).
4. **`DOWNLOAD_DIR`**: Path to save received files (default: `downloads`).
5. **`Large File Support`**: Optional 2GB mode via local Telegram API server.

`deploy.sh` automatically creates the Python virtual environment, installs dependencies, sets up `/etc/systemd/system/orionbot.service`, and starts the service.

---

## 📖 Telegram Bot Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| `/start` | Welcome message and bot overview | `/start` |
| `/help` | Detailed command manual | `/help` |
| `/list` or `/ls` | Browse files in storage with 1-tap download buttons | `/list` |
| `/get <filename>` | Quickly download a file from `downloads/` | `/get backup.tar.gz` |
| `/send <filepath>` | Send any file from the VPS to Telegram | `/send /var/log/syslog` |
| `/status` or `/disk` | VPS disk space and storage directory statistics | `/status` |
| `/id` | Show your Telegram User ID and Chat ID | `/id` |

### 📥 Uploading Files to VPS
Simply attach or forward any file (documents, archives, videos, photos, audio, voice messages) to the bot. Orion will:
1. Validate authorization.
2. Sanitize filename and prevent name collisions (e.g. `report (1).pdf`).
3. Save the file to `downloads/`.
4. Reply with a confirmation receipt showing the file size, exact path, and transfer time.

---

## ⚙️ Configuration (.env)

Configuration is managed via the `.env` file in the project root:

```env
# Telegram Bot Token from @BotFather (Required)
BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Authorized Telegram User IDs, comma-separated (Required)
ALLOWED_USERS=123456789,987654321

# Storage directory for incoming files (Default: downloads)
DOWNLOAD_DIR=downloads

# Maximum file size to handle in MB (50 for official API, up to 2000 for local server)
MAX_FILE_SIZE_MB=50

# Optional custom Telegram Bot API Server (leave empty for official API)
BOT_API_SERVER=
BOT_API_IS_LOCAL=false

# Telegram API credentials from https://my.telegram.org (only if running local API server)
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
```

---

## 🛠️ Service Management

Orion runs in the background as a `systemd` daemon:

```bash
# Check service status
sudo systemctl status orionbot

# View live real-time logs
sudo journalctl -u orionbot -f

# Restart the bot
sudo systemctl restart orionbot

# Stop the bot
sudo systemctl stop orionbot
```

---

## 🚀 2GB Large File Support (Local Bot API Server)

- **Standard Telegram Bot API:**
  - Max upload from VPS: **50 MB**
  - Max download from Telegram: **20 MB**
- **Orion Large File Mode (Up to 2 GB):**
  When running `deploy.sh`, you will be asked:
  ```text
  Enable Large File Support (up to 2GB)? [y/N]:
  ```
  Selecting **Y** will prompt for your Telegram `API_ID` & `API_HASH` (free from [my.telegram.org](https://my.telegram.org)), automatically install Docker, deploy a local Telegram Bot API Server on port 8081, and configure Orion to handle files up to **2000 MB (2 GB)**!

---

## 🧪 Running Tests

Orion includes comprehensive unit tests for configuration, path sanitization, and authorization:

```bash
source .venv/bin/activate
pytest tests/ -v
```

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).
