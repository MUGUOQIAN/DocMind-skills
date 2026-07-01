"""归档目录选择对话框（桌面应用）。"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Callable

import customtkinter as ctk

from lib.archive_location import (
    DEFAULT_ARCHIVE_FOLDER_NAME,
    join_archive_path,
    list_storage_roots,
    validate_archive_root,
)


class ArchiveLocationDialog(ctk.CTkToplevel):
    """选择整理后文件保存的磁盘与文件夹。"""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        initial_path: str = "",
        on_saved: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.title("选择归档保存位置")
        self.geometry("560x360")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self._on_saved = on_saved
        self._roots = list_storage_roots()

        self.mode_var = tk.StringVar(value="drive")
        self.drive_var = tk.StringVar()
        self.folder_var = tk.StringVar(value=DEFAULT_ARCHIVE_FOLDER_NAME)
        self.custom_var = tk.StringVar(value=initial_path)

        self._apply_initial_path(initial_path)
        self._build()
        self._refresh_preview()

    def _apply_initial_path(self, initial_path: str) -> None:
        if not initial_path:
            if self._roots:
                self.drive_var.set(self._roots[0]["path"])
            return
        p = Path(initial_path)
        if p.is_absolute() and len(p.parts) >= 2:
            parent = str(p.parent.resolve())
            for item in self._roots:
                if item["path"].lower() == parent.lower() or item["path"] == parent:
                    self.mode_var.set("drive")
                    self.drive_var.set(item["path"])
                    self.folder_var.set(p.name)
                    return
        self.mode_var.set("custom")
        self.custom_var.set(initial_path)

    def _build(self) -> None:
        pad = {"padx": 16, "pady": 6}
        ctk.CTkLabel(
            self,
            text="整理后的文件将保存到您选择的磁盘与文件夹下",
            font=ctk.CTkFont(size=15, weight="bold"),
            wraplength=500,
        ).pack(anchor="w", **pad)

        ctk.CTkLabel(
            self,
            text="建议选择空间充足的磁盘（如 D:、E: 或外置硬盘）。",
            text_color="gray",
            wraplength=500,
        ).pack(anchor="w", padx=16)

        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", **pad)
        ctk.CTkRadioButton(
            mode_row,
            text="按磁盘选择",
            variable=self.mode_var,
            value="drive",
            command=self._on_mode_change,
        ).pack(side="left", padx=(0, 16))
        ctk.CTkRadioButton(
            mode_row,
            text="自定义完整路径",
            variable=self.mode_var,
            value="custom",
            command=self._on_mode_change,
        ).pack(side="left")

        self.drive_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.drive_frame.pack(fill="x", **pad)

        ctk.CTkLabel(self.drive_frame, text="磁盘", width=72, anchor="w").pack(
            side="left"
        )
        drive_values = [r["display"] for r in self._roots]
        self._drive_display_map = {r["display"]: r["path"] for r in self._roots}
        self._drive_path_map = {r["path"]: r["display"] for r in self._roots}
        initial_display = self._drive_path_map.get(
            self.drive_var.get(), drive_values[0] if drive_values else ""
        )
        self.drive_menu = ctk.CTkOptionMenu(
            self.drive_frame,
            values=drive_values or ["（无可用磁盘）"],
            command=self._on_drive_selected,
            width=380,
        )
        self.drive_menu.set(initial_display)
        self.drive_menu.pack(side="left", padx=8)

        folder_row = ctk.CTkFrame(self, fg_color="transparent")
        folder_row.pack(fill="x", **pad)
        self.folder_row = folder_row
        ctk.CTkLabel(folder_row, text="文件夹名", width=72, anchor="w").pack(
            side="left"
        )
        folder_entry = ctk.CTkEntry(
            folder_row, textvariable=self.folder_var, width=380
        )
        folder_entry.pack(side="left", padx=8)
        folder_entry.bind("<KeyRelease>", lambda _e: self._refresh_preview())

        self.custom_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkLabel(self.custom_frame, text="完整路径", width=72, anchor="w").pack(
            side="left"
        )
        custom_entry = ctk.CTkEntry(
            self.custom_frame, textvariable=self.custom_var, width=320
        )
        custom_entry.pack(side="left", padx=8)
        ctk.CTkButton(
            self.custom_frame,
            text="浏览…",
            width=72,
            command=self._browse_custom,
        ).pack(side="left")
        custom_entry.bind("<KeyRelease>", lambda _e: self._refresh_preview())

        self.preview_label = ctk.CTkLabel(
            self,
            text="",
            justify="left",
            anchor="w",
            wraplength=500,
            fg_color=("gray92", "gray18"),
            corner_radius=8,
        )
        self.preview_label.pack(fill="x", padx=16, pady=12, ipady=10)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(btn_row, text="保存", width=120, command=self._save).pack(
            side="right"
        )
        ctk.CTkButton(
            btn_row,
            text="取消",
            width=88,
            fg_color="gray40",
            hover_color="gray30",
            command=self.destroy,
        ).pack(side="right", padx=8)

        self._on_mode_change()

    def _on_mode_change(self) -> None:
        if self.mode_var.get() == "drive":
            self.drive_frame.pack(fill="x", padx=16, pady=6)
            self.folder_row.pack(fill="x", padx=16, pady=6)
            self.custom_frame.pack_forget()
        else:
            self.drive_frame.pack_forget()
            self.folder_row.pack_forget()
            self.custom_frame.pack(fill="x", padx=16, pady=6)
        self._refresh_preview()

    def _on_drive_selected(self, display: str) -> None:
        path = self._drive_display_map.get(display, "")
        if path:
            self.drive_var.set(path)
        self._refresh_preview()

    def _browse_custom(self) -> None:
        path = filedialog.askdirectory(title="选择归档根目录")
        if path:
            self.custom_var.set(path)
            self._refresh_preview()

    def _resolved_path(self) -> str:
        if self.mode_var.get() == "custom":
            return self.custom_var.get().strip()
        return str(join_archive_path(self.drive_var.get(), self.folder_var.get()))

    def _refresh_preview(self) -> None:
        path = self._resolved_path() or "（未填写）"
        self.preview_label.configure(text=f"整理后文件将保存到：\n{path}")

    def _save(self) -> None:
        try:
            resolved = validate_archive_root(self._resolved_path(), create=True)
        except (ValueError, OSError) as exc:
            messagebox.showerror("无法保存", str(exc), parent=self)
            return
        self._on_saved(str(resolved))
        self.destroy()


def ask_archive_location(
    master: ctk.CTk,
    *,
    initial_path: str = "",
    on_saved: Callable[[str], None],
) -> ArchiveLocationDialog:
    dialog = ArchiveLocationDialog(master, initial_path=initial_path, on_saved=on_saved)
    master.wait_window(dialog)
    return dialog
