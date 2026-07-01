"""DocMind 桌面应用 UI。"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Any

import customtkinter as ctk

from .archive_picker import ask_archive_location
from .services import DocMindService, open_path_in_explorer
from lib.payment_hint import PaymentRequiredError


class DocMindApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.service = DocMindService()
        self._last_operations: list[dict[str, Any]] = []
        self._last_source_root: Path | None = None
        self._busy = False

        self.title("DocMind 文件智能管家")
        self.geometry("960x640")
        self.minsize(800, 520)

        if not self.service.has_config():
            self.service.init_default_config()

        self._build_header()
        self._build_tabs()
        self.after(300, self._refresh_quota)
        self.after(100, self._ensure_archive_location)

    def _ensure_archive_location(self) -> None:
        if not self.service.archive_root():
            self._pick_archive_location(required=True)

    def _refresh_archive_label(self) -> None:
        path = self.service.archive_root() or "（未设置，请点击下方按钮选择）"
        self.archive_label.configure(text=f"整理后保存到：{path}")
        self.set_archive.set("" if path.startswith("（") else path)
        if hasattr(self, "settings_archive_label"):
            self.settings_archive_label.configure(
                text=path if not path.startswith("（") else "（未设置）"
            )

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=(12, 0))

        ctk.CTkLabel(
            bar,
            text="DocMind",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        self.quota_label = ctk.CTkLabel(
            bar,
            text="额度加载中…",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self.quota_label.pack(side="right")

    def _build_tabs(self) -> None:
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=16, pady=12)

        tab_org = tabs.add("整理")
        tab_search = tabs.add("搜索")
        tab_settings = tabs.add("设置")

        self._build_organize_tab(tab_org)
        self._build_search_tab(tab_search)
        self._build_settings_tab(tab_settings)

    def _build_organize_tab(self, parent: ctk.CTkFrame) -> None:
        archive_bar = ctk.CTkFrame(parent, fg_color=("gray92", "gray20"), corner_radius=8)
        archive_bar.pack(fill="x", padx=4, pady=(8, 4))
        self.archive_label = ctk.CTkLabel(
            archive_bar,
            text="",
            anchor="w",
            justify="left",
            wraplength=820,
        )
        self.archive_label.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        ctk.CTkButton(
            archive_bar,
            text="更改保存位置",
            width=110,
            command=lambda: self._pick_archive_location(required=False),
        ).pack(side="right", padx=12, pady=8)
        self._refresh_archive_label()

        top = ctk.CTkFrame(parent, fg_color="transparent")
        top.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(top, text="整理来源：").pack(side="left", padx=(4, 8))
        self.source_var = tk.StringVar(value="desktop")
        self.source_menu = ctk.CTkOptionMenu(
            top,
            variable=self.source_var,
            values=["desktop", "downloads", "custom"],
            command=self._on_source_change,
            width=140,
        )
        self.source_menu.pack(side="left")

        self.custom_path_var = tk.StringVar()
        self.custom_entry = ctk.CTkEntry(
            top,
            textvariable=self.custom_path_var,
            placeholder_text="选择自定义文件夹…",
            width=320,
        )
        self.custom_entry.pack(side="left", padx=8)
        self.custom_entry.pack_forget()

        ctk.CTkButton(top, text="浏览…", width=72, command=self._browse_source).pack(
            side="left"
        )

        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x", pady=8)

        self.btn_preview = ctk.CTkButton(
            actions,
            text="预览整理",
            command=self._on_preview,
            width=120,
        )
        self.btn_preview.pack(side="left", padx=4)

        self.btn_run = ctk.CTkButton(
            actions,
            text="执行整理",
            fg_color="#2d8a4e",
            hover_color="#246b3d",
            command=self._on_run,
            width=120,
        )
        self.btn_run.pack(side="left", padx=4)

        self.btn_undo = ctk.CTkButton(
            actions,
            text="撤销上次",
            fg_color="#8a4e2d",
            hover_color="#6b3d24",
            command=self._on_undo,
            width=120,
        )
        self.btn_undo.pack(side="left", padx=4)

        ctk.CTkButton(
            actions,
            text="打开归档目录",
            command=self._open_archive,
            width=120,
        ).pack(side="right", padx=4)

        self.status_label = ctk.CTkLabel(
            parent,
            text="先预览整理方案，确认后再执行。预览免费。",
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=4, pady=(0, 4))

        self.result_box = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Consolas", size=12))
        self.result_box.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_search_tab(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(12, 8), padx=4)

        self.search_var = tk.StringVar()
        entry = ctk.CTkEntry(
            row,
            textvariable=self.search_var,
            placeholder_text="输入关键词，如：东方广场 合同",
            width=480,
        )
        entry.pack(side="left", padx=(0, 8))
        entry.bind("<Return>", lambda _e: self._on_search())

        ctk.CTkButton(row, text="搜索", width=88, command=self._on_search).pack(
            side="left"
        )

        self.search_box = ctk.CTkTextbox(parent, font=ctk.CTkFont(family="Consolas", size=12))
        self.search_box.pack(fill="both", expand=True, padx=4, pady=4)

    def _build_settings_tab(self, parent: ctk.CTkFrame) -> None:
        cfg = self.service.load_config()
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=8, pady=12)

        def row(label: str, var: tk.StringVar, browse: bool = False) -> None:
            line = ctk.CTkFrame(form, fg_color="transparent")
            line.pack(fill="x", pady=6)
            ctk.CTkLabel(line, text=label, width=120, anchor="w").pack(side="left")
            ctk.CTkEntry(line, textvariable=var, width=400).pack(side="left", padx=8)
            if browse:
                ctk.CTkButton(
                    line,
                    text="浏览",
                    width=64,
                    command=lambda v=var: self._browse_into(v),
                ).pack(side="left")

        self.set_target = tk.StringVar(value=cfg.get("target_folder", ""))
        self.set_archive = tk.StringVar(value=cfg.get("archive_root", ""))
        self.set_industry = tk.StringVar(value=cfg.get("industry", ""))
        self.set_job = tk.StringVar(value=cfg.get("job_title", ""))

        row("待整理目录", self.set_target, browse=True)

        archive_line = ctk.CTkFrame(form, fg_color="transparent")
        archive_line.pack(fill="x", pady=6)
        ctk.CTkLabel(
            archive_line, text="整理后保存到", width=120, anchor="w"
        ).pack(side="left")
        self.settings_archive_label = ctk.CTkLabel(
            archive_line,
            text=self.set_archive.get() or "（未设置）",
            anchor="w",
            wraplength=400,
            justify="left",
        )
        self.settings_archive_label.pack(side="left", padx=8, fill="x", expand=True)
        ctk.CTkButton(
            archive_line,
            text="选择磁盘/文件夹…",
            width=140,
            command=lambda: self._pick_archive_location(required=False),
        ).pack(side="left")

        ctk.CTkLabel(
            parent,
            text="可将归档目录设在任意磁盘（如 D:\\我的归档、/Volumes/外置盘/DocMind）。",
            text_color="gray",
            anchor="w",
            wraplength=820,
        ).pack(fill="x", padx=12, pady=(0, 4))

        row("行业", self.set_industry)
        row("职位", self.set_job)

        ctk.CTkButton(
            parent,
            text="保存设置",
            command=self._save_settings,
            width=140,
        ).pack(anchor="w", padx=8, pady=8)

        info = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        info.pack(fill="x", padx=8, pady=12)

        uid = self.service.user_id
        cpath = self.service.config_path()
        ctk.CTkLabel(
            info,
            text=f"用户 ID：{uid}\n配置文件：{cpath}",
            justify="left",
            anchor="w",
        ).pack(padx=12, pady=12, anchor="w")

    def _on_source_change(self, _value: str) -> None:
        if self.source_var.get() == "custom":
            self.custom_entry.pack(side="left", padx=8, after=self.source_menu)
        else:
            self.custom_entry.pack_forget()

    def _browse_source(self) -> None:
        path = filedialog.askdirectory(title="选择待整理文件夹")
        if path:
            self.source_var.set("custom")
            self.custom_path_var.set(path)
            self._on_source_change("custom")

    def _browse_into(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(title="选择文件夹")
        if path:
            var.set(path)

    def _source_kwargs(self) -> dict[str, str | None]:
        choice = self.source_var.get()
        return {
            "source_choice": choice,
            "custom_path": self.custom_path_var.get() if choice == "custom" else None,
        }

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        for btn in (self.btn_preview, self.btn_run, self.btn_undo):
            btn.configure(state=state)
        if message:
            self.status_label.configure(text=message)

    def _format_operations(self, ops: list[dict[str, Any]]) -> str:
        if not ops:
            return "（无待整理文件）"
        lines = [f"共 {len(ops)} 个文件：\n"]
        for i, op in enumerate(ops, 1):
            name = Path(op["source"]).name
            dest = op.get("target_path", "")
            lines.append(f"{i:3}. {name}")
            lines.append(f"     → {dest}/")
        return "\n".join(lines)

    def _on_preview(self) -> None:
        if self._busy:
            return
        self._set_busy(True, "正在预览整理方案…")
        self.result_box.delete("1.0", "end")

        def work():
            return self.service.preview(**self._source_kwargs())

        def ok(ops: list[dict[str, Any]]) -> None:
            self._last_operations = ops
            try:
                src, _ = self.service.resolve_source(**self._source_kwargs())
                self._last_source_root = src
            except Exception:
                self._last_source_root = None
            self.result_box.insert("end", self._format_operations(ops))
            self._set_busy(False, f"预览完成，共 {len(ops)} 个文件。执行前请确认方案。")

        def err(exc: Exception) -> None:
            self._handle_error(exc, "预览失败")
            self._set_busy(False)

        self.service.run_in_thread(work, on_success=ok, on_error=err)

    def _on_run(self) -> None:
        if self._busy:
            return
        if not self._last_operations:
            if not messagebox.askyesno(
                "确认",
                "尚未预览，是否直接执行整理？\n（将移动文件并扣除 1 次整理额度）",
            ):
                return
        elif not messagebox.askyesno(
            "确认执行",
            f"将移动 {len(self._last_operations)} 个文件到归档目录。\n确定执行？",
        ):
            return

        self._set_busy(True, "正在整理文件…")
        self.result_box.delete("1.0", "end")

        def work():
            return self.service.run_organize(**self._source_kwargs())

        def ok(ops: list[dict[str, Any]]) -> None:
            self._last_operations = ops
            try:
                src, _ = self.service.resolve_source(**self._source_kwargs())
                self._last_source_root = src
            except Exception:
                pass
            self.result_box.insert("end", self._format_operations(ops))
            self._set_busy(False, f"整理完成，已移动 {len(ops)} 个文件。")
            self._refresh_quota()

        def err(exc: Exception) -> None:
            self._handle_error(exc, "整理失败")
            self._set_busy(False)

        self.service.run_in_thread(work, on_success=ok, on_error=err)

    def _on_undo(self) -> None:
        if self._busy:
            return
        root = self._last_source_root
        if not root:
            try:
                root, _ = self.service.resolve_source(**self._source_kwargs())
            except Exception as exc:
                messagebox.showerror("撤销失败", str(exc))
                return
        if not messagebox.askyesno("确认撤销", f"将恢复「{root}」上次整理移动的文件。\n确定？"):
            return

        self._set_busy(True, "正在撤销…")

        def work():
            return self.service.undo(root)

        def ok(ops: list[dict[str, Any]]) -> None:
            self.result_box.delete("1.0", "end")
            self.result_box.insert("end", f"已撤销 {len(ops)} 个文件。\n")
            self._last_operations = []
            self._set_busy(False, "撤销完成。")

        def err(exc: Exception) -> None:
            self._handle_error(exc, "撤销失败")
            self._set_busy(False)

        self.service.run_in_thread(work, on_success=ok, on_error=err)

    def _on_search(self) -> None:
        query = self.search_var.get().strip()
        if not query:
            return
        self.search_box.delete("1.0", "end")
        self.search_box.insert("end", "搜索中…\n")

        def work():
            return self.service.search(query)

        def ok(results: list[dict[str, Any]]) -> None:
            self.search_box.delete("1.0", "end")
            if not results:
                self.search_box.insert("end", "未找到匹配文件。")
                return
            lines = [f"找到 {len(results)} 条结果：\n"]
            for i, row in enumerate(results, 1):
                score = row.get("score", "")
                path = row.get("path", row.get("filename", ""))
                snippet = (row.get("content_snippet") or "")[:80]
                lines.append(f"{i}. [{score}] {path}")
                if snippet:
                    lines.append(f"   {snippet}")
            self.search_box.insert("end", "\n".join(lines))

        def err(exc: Exception) -> None:
            self.search_box.delete("1.0", "end")
            self._handle_error(exc, "搜索失败")

        self.service.run_in_thread(work, on_success=ok, on_error=err)

    def _pick_archive_location(self, *, required: bool) -> None:
        current = self.service.archive_root()

        def on_saved(path: str) -> None:
            try:
                self.service.save_archive_root(path)
            except Exception as exc:
                messagebox.showerror("保存失败", str(exc))
                if required:
                    self.after(100, lambda: self._pick_archive_location(required=True))
                return
            self._refresh_archive_label()
            if not required:
                messagebox.showinfo("已保存", f"整理后文件将保存到：\n{path}")

        ask_archive_location(self, initial_path=current, on_saved=on_saved)
        if required and not self.service.archive_root():
            messagebox.showwarning(
                "需要设置保存位置",
                "请先选择整理后文件的保存目录，才能开始整理。",
            )
            self.after(100, lambda: self._pick_archive_location(required=True))

    def _save_settings(self) -> None:
        try:
            self.service.save_settings(
                target_folder=self.set_target.get(),
                archive_root=self.set_archive.get(),
                industry=self.set_industry.get(),
                job_title=self.set_job.get(),
            )
            messagebox.showinfo("已保存", "设置已写入配置文件。")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _open_archive(self) -> None:
        try:
            cfg = self.service.load_config()
            root = cfg.get("archive_root")
            if not root:
                raise FileNotFoundError("请先在设置中配置归档根目录")
            open_path_in_explorer(root)
        except Exception as exc:
            messagebox.showerror("无法打开", str(exc))

    def _refresh_quota(self) -> None:
        def work():
            return self.service.fetch_quota()

        def ok(data: dict[str, Any]) -> None:
            trial = data.get("free_trial_active")
            days = data.get("free_trial_days_remaining")
            org = data.get("organize_remaining", data.get("organize_quota"))
            search = data.get("search_remaining", data.get("search_quota"))
            parts = []
            if trial:
                parts.append(f"试用剩余 {days} 天")
            if org is not None:
                parts.append(f"整理 {org}")
            if search is not None:
                parts.append(f"搜索 {search}")
            text = " · ".join(parts) if parts else "额度已加载"
            self.quota_label.configure(text=text)

        def err(_exc: Exception) -> None:
            self.quota_label.configure(text="额度暂不可用（请检查网络）")

        self.service.run_in_thread(work, on_success=ok, on_error=err)

    def _handle_error(self, exc: Exception, title: str) -> None:
        if isinstance(exc, PaymentRequiredError):
            payload = getattr(exc, "payload", {}) or {}
            products = payload.get("products", [])
            msg = str(exc)
            if products:
                sku_lines = [
                    f"- {p.get('name', p.get('id', ''))}: ¥{p.get('price', '?')}"
                    for p in products[:5]
                ]
                msg += "\n\n可购套餐：\n" + "\n".join(sku_lines)
            messagebox.showwarning(title, msg)
            self._refresh_quota()
            return
        messagebox.showerror(title, str(exc))
