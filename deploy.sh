#!/usr/bin/env bash
# ==============================================================================
# Orion Telegram Bot - Production Deployment Script
# Fast, automated setup for VPS & Servers
# Repo: https://github.com/wymthw1n/orionbot
# ==============================================================================

set -euo pipefail

# Color palette (256-color support with fallback)
C_CYAN="\033[38;5;45m"
C_BLUE="\033[38;5;39m"
C_PURPLE="\033[38;5;141m"
C_GREEN="\033[38;5;82m"
C_YELLOW="\033[38;5;220m"
C_RED="\033[38;5;196m"
C_WHITE="\033[1;37m"
C_DIM="\033[38;5;244m"
C_GRAY="\033[38;5;245m"
C_LINE="\033[38;5;31m"
BOLD="\033[1m"
NC="\033[0m"

# Compatibility aliases
RED="$C_RED"
GREEN="$C_GREEN"
YELLOW="$C_YELLOW"
BLUE="$C_BLUE"
CYAN="$C_CYAN"

SERVICE_NAME="orionbot"
REPO_URL="https://github.com/wymthw1n/orionbot.git"

# Sleek ASCII Art Header & Info Panel
echo ""
echo -e "${C_BLUE}   ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗${NC}"
echo -e "${C_BLUE}  ██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║${NC}"
echo -e "${C_BLUE}  ██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║${NC}"
echo -e "${C_CYAN}  ██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║${NC}"
echo -e "${C_CYAN}  ╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║${NC}"
echo -e "${C_CYAN}   ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝${NC}"
echo ""
echo -e "${C_LINE}  ───────────────────────────────────────────────────────────${NC}"
echo -e "  ${C_PURPLE}✦${NC}  ${BOLD}Platform:${NC}    ${C_WHITE}Secure Telegram ⇄ VPS File Bridge${NC}"
echo -e "  ${C_BLUE}✦${NC}  ${BOLD}Features:${NC}    ${C_CYAN}Auto-Save${NC} ${C_GRAY}•${NC} ${C_CYAN}Send & Browse${NC} ${C_GRAY}•${NC} ${C_GREEN}Up to 2GB Transfer${NC}"
echo -e "  ${C_GRAY}✦${NC}  ${BOLD}Repository:${NC}  ${C_GRAY}https://github.com/wymthw1n/orionbot${NC}"
echo -e "${C_LINE}  ───────────────────────────────────────────────────────────${NC}"
echo ""

# 1. Root / Sudo check
if [ "$EUID" -ne 0 ]; then
  echo -e "${C_RED}❌ Error: Please run this script as root or using sudo:${NC}"
  echo "   sudo bash deploy.sh"
  exit 1
fi

# Helper for interactive or fallback input
prompt_input() {
  local prompt_text="$1"
  local default_val="$2"
  local var_name="$3"
  local val=""

  # 1. Use variable from environment if already exported
  eval "val=\"\${$var_name:-}\""
  if [ -n "$val" ]; then
    return 0
  fi

  while true; do
    if [ -n "$default_val" ]; then
      read -r -p "$prompt_text [$default_val]: " val || val=""
      val="${val:-$default_val}"
    else
      read -r -p "$prompt_text: " val || val=""
    fi

    if [ -n "$val" ]; then
      eval "$var_name=\"\$val\""
      break
    else
      echo -e "${RED}This value cannot be empty. Please enter a valid value.${NC}"
    fi
  done
}

# Helper for yes/no prompts
prompt_yes_no() {
  local prompt_text="$1"
  local default_val="$2"
  local var_name="$3"
  local val=""

  read -r -p "$prompt_text: " val || val=""
  val="${val:-$default_val}"
  eval "$var_name=\"\$val\""
}

# 2. Determine Target Installation Directory
DEFAULT_APP_DIR="/opt/orionbot"
CURRENT_REPO_DIR=""
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
  CURRENT_REPO_DIR="$(pwd)"
fi

APP_DIR="${INSTALL_DIR:-}"

if [ -z "$APP_DIR" ]; then
  if [ -n "$CURRENT_REPO_DIR" ] && [ "$CURRENT_REPO_DIR" != "$DEFAULT_APP_DIR" ]; then
    echo -e "\n${BOLD}${CYAN}📁 Step 1/5: Target Installation Location${NC}"
    echo "Where would you like to install Orion?"
    echo -e "  ${BOLD}1)${NC} ${C_GREEN}/opt/orionbot${NC}  ${C_GRAY}(Standard Production - Recommended)${NC}"
    echo -e "  ${BOLD}2)${NC} ${C_WHITE}$CURRENT_REPO_DIR${NC}  ${C_GRAY}(Current Directory)${NC}"
    prompt_input "Select option [1/2]" "1" DIR_CHOICE
    if [ "$DIR_CHOICE" = "2" ]; then
      APP_DIR="$CURRENT_REPO_DIR"
    else
      APP_DIR="$DEFAULT_APP_DIR"
    fi
  else
    APP_DIR="$DEFAULT_APP_DIR"
  fi
fi

# Ensure files exist in target APP_DIR
if [ -n "$CURRENT_REPO_DIR" ] && [ "$CURRENT_REPO_DIR" != "$APP_DIR" ]; then
  echo -e "${CYAN}→ Installing Orion project files into $APP_DIR...${NC}"
  mkdir -p "$APP_DIR"
  cp -a "$CURRENT_REPO_DIR/." "$APP_DIR/"
  cd "$APP_DIR"
elif [ ! -d "$APP_DIR/.git" ] && [ ! -f "$APP_DIR/main.py" ]; then
  echo -e "${CYAN}→ Cloning repository into $APP_DIR...${NC}"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
else
  cd "$APP_DIR"
  echo -e "${GREEN}✓ Using installation directory:${NC} $APP_DIR"
fi

# 3. Install System Prerequisites
echo -e "\n${BOLD}${CYAN}📦 Step 2/5: Installing System Packages (Python, venv, git, curl)...${NC}"
if command -v apt-get &>/dev/null; then
  apt-get update -qq
  apt-get install -y -qq python3 python3-venv python3-pip git curl > /dev/null
elif command -v dnf &>/dev/null; then
  dnf install -y -q python3 python3-pip git curl
elif command -v yum &>/dev/null; then
  yum install -y -q python3 python3-pip git curl
elif command -v pacman &>/dev/null; then
  pacman -Sy --noconfirm python python-pip git curl
else
  echo -e "${YELLOW}⚠️ Unknown package manager. Please ensure python3 and venv are installed.${NC}"
fi

# 4. Interactive Configuration for .env
ENV_FILE="$APP_DIR/.env"
RECONFIGURE=true
IS_LOCAL="false"
CURRENT_DIR="downloads"

if [ -f "$ENV_FILE" ]; then
  # Detect existing local bot api setting
  if grep -qi '^BOT_API_IS_LOCAL=true' "$ENV_FILE" 2>/dev/null; then
    IS_LOCAL="true"
  fi
  # Detect existing download directory (migrate downloads/orion to downloads)
  EXISTING_DIR="$(grep '^DOWNLOAD_DIR=' "$ENV_FILE" 2>/dev/null | cut -d '=' -f2- | tr -d ' ' || true)"
  if [ "$EXISTING_DIR" = "downloads/orion" ]; then
    CURRENT_DIR="downloads"
    sed -i 's|^DOWNLOAD_DIR=downloads/orion|DOWNLOAD_DIR=downloads|' "$ENV_FILE"
  elif [ -n "$EXISTING_DIR" ]; then
    CURRENT_DIR="$EXISTING_DIR"
  fi

  echo -e "\n${YELLOW}ℹ️  An existing .env file was found at:${NC} $ENV_FILE"
  prompt_yes_no "Do you want to keep existing settings? [Y/n]" "y" KEEP_EXISTING
  if [[ "$KEEP_EXISTING" =~ ^[Yy]$ ]]; then
    RECONFIGURE=false
    echo -e "${GREEN}✓ Keeping existing .env configuration.${NC}"
  else
    RECONFIGURE=true
  fi
fi

if [ "$RECONFIGURE" = true ]; then
  echo -e "\n${BOLD}${CYAN}⚙️  Step 3/5: Configuring Environment Variables (.env)${NC}"
  echo "----------------------------------------------------------"

  # 4a. BOT_TOKEN
  CURRENT_TOKEN="${BOT_TOKEN:-}"
  if [ -z "$CURRENT_TOKEN" ]; then
    echo -e "${YELLOW}Get your Bot Token from Telegram by messaging @BotFather.${NC}"
    prompt_input "🔑 Enter Telegram BOT_TOKEN" "" CURRENT_TOKEN
  fi

  # 4b. ALLOWED_USERS
  CURRENT_USERS="${ALLOWED_USERS:-}"
  if [ -z "$CURRENT_USERS" ]; then
    echo -e "${YELLOW}Get your Telegram User ID by messaging @userinfobot on Telegram.${NC}"
    echo -e "${YELLOW}For multiple users, separate with commas (e.g. 12345678,87654321).${NC}"
    prompt_input "👤 Enter ALLOWED_USERS (Telegram User IDs)" "" CURRENT_USERS
  fi

  # 4c. Custom Download Directory
  CURRENT_DIR="${DOWNLOAD_DIR:-}"
  if [ -z "$CURRENT_DIR" ]; then
    echo -e "\n${BOLD}${CYAN}📁 Storage Directory:${NC}"
    echo "Default storage directory: downloads (inside project: ${APP_DIR}/downloads)"
    prompt_yes_no "Do you want to set a custom download directory? [y/N]" "n" SET_CUSTOM_DIR
    if [[ "$SET_CUSTOM_DIR" =~ ^[Yy]$ ]]; then
      prompt_input "📁 Enter custom download path" "downloads" CURRENT_DIR
    else
      CURRENT_DIR="downloads"
      echo -e "${GREEN}✓ Using default storage directory: downloads${NC}"
    fi
  fi

  # 4d. Large File Transfer Option (Up to 2GB via local Telegram Bot API Server)
  ENABLE_LARGE_FILES="${ENABLE_LARGE_FILES:-}"
  CURRENT_API_ID="${TELEGRAM_API_ID:-}"
  CURRENT_API_HASH="${TELEGRAM_API_HASH:-}"
  CURRENT_SERVER="${BOT_API_SERVER:-}"
  IS_LOCAL="false"
  CURRENT_MAX="50"

  if [ -z "$ENABLE_LARGE_FILES" ]; then
    echo -e "\n${BOLD}${CYAN}📦 Large File Transfer Option (Up to 2GB):${NC}"
    echo "• Official Telegram Bot API limits: 50MB upload, 20MB download."
    echo "• Local Telegram Bot API Server unlocks transfers up to 2000MB (2GB)!"
    echo "  (Requires free API ID & API HASH from https://my.telegram.org)"

    prompt_yes_no "Enable Large File Support (up to 2GB)?" "n" ENABLE_LARGE_FILES
  fi

  ENABLE_LARGE_FILES="${ENABLE_LARGE_FILES:-n}"
  if [[ "$ENABLE_LARGE_FILES" =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}✓ Enabling Large File Mode (up to 2000MB / 2GB).${NC}"
    prompt_input "🔑 Enter TELEGRAM_API_ID (numeric)" "" CURRENT_API_ID
    prompt_input "🔑 Enter TELEGRAM_API_HASH" "" CURRENT_API_HASH

    # Install Docker if not present
    if ! command -v docker &>/dev/null; then
      echo -e "${CYAN}🐳 Installing Docker for Local Telegram Bot API Server...${NC}"
      if command -v apt-get &>/dev/null; then
        apt-get install -y -qq docker.io > /dev/null
      elif command -v dnf &>/dev/null; then
        dnf install -y -q docker
      elif command -v yum &>/dev/null; then
        yum install -y -q docker
      elif command -v pacman &>/dev/null; then
        pacman -Sy --noconfirm docker
      fi
    fi

    # Enable and start Docker service
    systemctl enable --now docker > /dev/null 2>&1 || true

    echo -e "${CYAN}🚀 Starting Local Telegram Bot API Server container (port 8081)...${NC}"
    mkdir -p /var/lib/telegram-bot-api
    docker pull aiogram/telegram-bot-api:latest -q || true
    docker stop telegram-bot-api 2>/dev/null || true
    docker rm telegram-bot-api 2>/dev/null || true
    docker run -d \
      --name telegram-bot-api \
      --restart always \
      -p 8081:8081 \
      -v /var/lib/telegram-bot-api:/var/lib/telegram-bot-api \
      -e TELEGRAM_API_ID="${CURRENT_API_ID}" \
      -e TELEGRAM_API_HASH="${CURRENT_API_HASH}" \
      -e TELEGRAM_LOCAL="true" \
      aiogram/telegram-bot-api:latest > /dev/null

    CURRENT_SERVER="http://127.0.0.1:8081"
    CURRENT_MAX="2000"
    IS_LOCAL="true"
    echo -e "${GREEN}✓ Local Telegram Bot API Server is running on http://127.0.0.1:8081${NC}"
  else
    echo -e "${GREEN}✓ Using Official Telegram Bot API (50MB send / 20MB receive limit).${NC}"
    CURRENT_MAX="50"
    CURRENT_SERVER=""
    IS_LOCAL="false"
  fi

  # Write .env file
  cat > "$ENV_FILE" << EOF
# ==============================================================
# Orion Bot - Configuration File (.env)
# Generated by deploy.sh on $(date -u +"%Y-%m-%d %H:%M:%SZ")
# ==============================================================

BOT_TOKEN=${CURRENT_TOKEN}
ALLOWED_USERS=${CURRENT_USERS}
DOWNLOAD_DIR=${CURRENT_DIR}
MAX_FILE_SIZE_MB=${CURRENT_MAX}
BOT_API_SERVER=${CURRENT_SERVER}
BOT_API_IS_LOCAL=${IS_LOCAL}
TELEGRAM_API_ID=${CURRENT_API_ID}
TELEGRAM_API_HASH=${CURRENT_API_HASH}
EOF

  chmod 600 "$ENV_FILE"
  echo -e "${GREEN}✓ Saved configuration to $ENV_FILE (permissions: 600)${NC}"
fi

# 5. Set up Python Virtual Environment & Install Dependencies
echo -e "\n${BOLD}${CYAN}🐍 Step 4/5: Setting up Python Virtual Environment (.venv)...${NC}"
if [ ! -d "$APP_DIR/.venv" ]; then
  python3 -m venv "$APP_DIR/.venv"
fi

"$APP_DIR/.venv/bin/pip" install --upgrade pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q
echo -e "${GREEN}✓ Python dependencies successfully installed.${NC}"

# 6. Ensure Download Storage Directory Exists
TARGET_DOWNLOAD_DIR="${CURRENT_DIR:-downloads}"
if [[ "$TARGET_DOWNLOAD_DIR" != /* ]]; then
  TARGET_DOWNLOAD_DIR="$APP_DIR/$TARGET_DOWNLOAD_DIR"
fi
mkdir -p "$TARGET_DOWNLOAD_DIR"
echo -e "${GREEN}✓ Download storage prepared:${NC} $TARGET_DOWNLOAD_DIR"

# 7. Configure and Install Systemd Service
echo -e "\n${BOLD}${CYAN}⚙️  Step 5/5: Configuring Systemd Service (${SERVICE_NAME}.service)...${NC}"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

UNIT_AFTER="network.target"
UNIT_WANTS=""
if [ -n "$CURRENT_SERVER" ] && [[ "$CURRENT_SERVER" =~ (localhost|127\.0\.0\.1) ]]; then
  UNIT_AFTER="network.target docker.service"
  UNIT_WANTS="Wants=docker.service"
fi

cat > "$SERVICE_DEST" << EOF
[Unit]
Description=Orion Telegram Bot - VPS File Transfer Service
After=${UNIT_AFTER}
${UNIT_WANTS}

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/python ${APP_DIR}/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service" > /dev/null 2>&1 || true
systemctl restart "${SERVICE_NAME}.service"

# 8. Check Status
sleep 2
if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
  echo ""
  echo -e "${C_LINE}  ═══════════════════════════════════════════════════════════${NC}"
  echo -e "  ${C_GREEN}🚀  ${BOLD}ORION BOT SUCCESSFULLY DEPLOYED & ACTIVE${NC}"
  echo -e "${C_LINE}  ───────────────────────────────────────────────────────────${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}Directory:${NC}    ${C_WHITE}${APP_DIR}${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}Downloads:${NC}    ${C_CYAN}${TARGET_DOWNLOAD_DIR}${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}Service:${NC}      ${C_GREEN}${SERVICE_NAME}.service${NC} ${C_GRAY}(running)${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}View Logs:${NC}    ${C_YELLOW}journalctl -u ${SERVICE_NAME} -f${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}Restart:${NC}      ${C_CYAN}systemctl restart ${SERVICE_NAME}${NC}"
  echo -e "  ${C_GRAY}•${NC} ${BOLD}Stop:${NC}         ${C_GRAY}systemctl stop ${SERVICE_NAME}${NC}"
  echo -e "${C_LINE}  ───────────────────────────────────────────────────────────${NC}"
  echo -e "  ${C_YELLOW}💡${NC} ${C_WHITE}Open your Telegram bot and send ${C_CYAN}${BOLD}/start${NC}${C_WHITE} to begin!${NC}"
  echo -e "${C_LINE}  ═══════════════════════════════════════════════════════════${NC}"
  echo ""
else
  echo -e "\n${C_YELLOW}⚠️  Service started, but is not currently active.${NC}"
  echo "Checking recent logs:"
  journalctl -u "${SERVICE_NAME}" -n 15 --no-pager
fi
