#!/usr/bin/env python3
"""OpenClaw /docmind 斜杠命令分发：接收 raw 参数并转调 docmind.py。"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) > 1:
        tokens = sys.argv[1:]
    else:
        raw = (os.getenv("DOCMIND_SLASH_ARGS") or "").strip()
        if not raw:
            print("用法: openclaw_dispatch.py <子命令> [选项…]", file=sys.stderr)
            print("示例: openclaw_dispatch.py preview --desktop", file=sys.stderr)
            return 2
        tokens = shlex.split(raw, posix=os.name != "nt")

    here = Path(__file__).resolve()
    docmind = here.parent / "docmind.py"
    uid = os.getenv("DOCMIND_USER_ID", "default-user")
    cmd = [sys.executable, str(docmind), *tokens]
    if "--user-id" not in tokens:
        cmd.extend(["--user-id", uid])
    return subprocess.run(cmd, env=os.environ.copy()).returncode


if __name__ == "__main__":
    raise SystemExit(main())
