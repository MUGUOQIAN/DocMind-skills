#!/usr/bin/env python3
"""WorkBuddy 分发：转调 docmind.py，自动注入 --user-id 与 platform。"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib.constants import resolve_user_id  # noqa: E402


def main() -> int:
    if len(sys.argv) > 1:
        tokens = sys.argv[1:]
    else:
        raw = (os.getenv("DOCMIND_SLASH_ARGS") or "").strip()
        if not raw:
            print(
                "用法: workbuddy_dispatch.py <子命令> [选项…]",
                file=sys.stderr,
            )
            print(
                "示例: workbuddy_dispatch.py preview --desktop",
                file=sys.stderr,
            )
            return 2
        tokens = shlex.split(raw, posix=os.name != "nt")

    here = Path(__file__).resolve()
    docmind = here.parent / "docmind.py"
    uid = resolve_user_id(os.getenv("DOCMIND_USER_ID"))
    env = os.environ.copy()
    env.setdefault("DOCMIND_PLATFORM", "workbuddy")
    cmd = [sys.executable, str(docmind), *tokens]
    if "--user-id" not in tokens:
        cmd.extend(["--user-id", uid])
    return subprocess.run(cmd, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
