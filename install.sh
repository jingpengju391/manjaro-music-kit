#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == "--dry-run" ]]; then
  exec python3 install.py --dry-run
fi
if [[ $EUID == 0 ]]; then echo '请以桌面普通用户运行，不要 sudo 整个脚本。'; exit 1; fi
if [[ "${XDG_SESSION_TYPE:-x11}" != x11 ]]; then echo '此界面需要 X11，请登录 XFCE/X11 会话后安装。'; exit 1; fi
command -v pacman >/dev/null || { echo '此安装器面向 Manjaro / Arch Linux。'; exit 1; }
packages=(mpd ncmpcpp cava python python-gobject python-cairo gtk3 xfce4-terminal xdotool xorg-xprop xorg-xrandr libx11 libxext dbus xfconf)
missing=()
for p in "${packages[@]}"; do pacman -Q "$p" >/dev/null 2>&1 || missing+=("$p"); done
if ((${#missing[@]})); then sudo pacman -S --needed "${missing[@]}"; fi
exec python3 install.py
