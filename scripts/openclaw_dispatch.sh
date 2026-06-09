#!/usr/bin/env bash
# OpenClaw /docmind 斜杠命令（macOS / Linux）
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$#" -eq 0 ]; then
  echo "用法: openclaw_dispatch.sh preview --desktop" >&2
  exit 2
fi
exec python3 "${SCRIPT_DIR}/openclaw_dispatch.py" "$@"
