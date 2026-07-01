"""DocMind 桌面应用入口。"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print(
            "缺少桌面 UI 依赖，请执行:\n"
            "  pip install -r desktop/requirements.txt",
            file=sys.stderr,
        )
        return 1

    from desktop.app import DocMindApp

    app = DocMindApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
