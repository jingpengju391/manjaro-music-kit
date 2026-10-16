#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ $EUID == 0 ]]; then echo '请以桌面普通用户运行，不要 sudo 整个脚本。' >&2; exit 1; fi
check=false
for arg in "$@"; do
  case "$arg" in --check|--dry-run|--help|-h|--restore|--restore=*|--list-backups) check=true;; esac
done
if ! command -v python3 >/dev/null; then
  if [[ $check == true ]]; then echo '缺少 Python；请先安装 python。未修改系统。' >&2; exit 1; fi
  command -v pacman >/dev/null || { echo '此安装器面向 Manjaro / Arch Linux。' >&2; exit 1; }
  echo '需要安装 Python；pacman 将完整升级系统并请求确认。'
  sudo pacman -Syu --needed python
fi
if ! python3 -c 'import argparse, datetime, json, math, pathlib, shutil, subprocess'; then
  echo 'Python/系统库无法加载，尚未写入音乐配置。请先完成系统升级：sudo pacman -Syu glibc python，重启后再运行。' >&2
  exit 1
fi
exec python3 install.py "$@"
