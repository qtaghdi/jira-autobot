from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gui.app import App


class ActionPanel(ttk.Frame):
    def __init__(self, parent_frame: tk.Widget, app: App):
        super().__init__(parent_frame)
        self.app = app

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=(5, 3))

        self.create_btn = ttk.Button(top, text="Jira에 서브태스크 생성", command=self.app.on_create_all)
        self.create_btn.pack(side="left")

        self.progress_label = ttk.Label(top, text="")
        self.progress_label.pack(side="right", padx=(5, 0))

        self.progress_bar = ttk.Progressbar(top, mode="determinate", length=300)
        self.progress_bar.pack(side="right", padx=(10, 0))

        log_frame = ttk.LabelFrame(self, text="처리 로그")
        log_frame.pack(fill="both", expand=True, padx=8, pady=(0, 5))

        self.log_text = tk.Text(log_frame, height=6, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.log_text.tag_configure("ok", foreground="green")
        self.log_text.tag_configure("error", foreground="red")
        self.log_text.tag_configure("warn", foreground="orange")
        self.log_text.tag_configure("info", foreground="black")

    def log(self, message: str, level: str = "info") -> None:
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n", level)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def start_progress(self, total: int) -> None:
        self.progress_bar.config(maximum=total, value=0)
        self.progress_label.config(text=f"0/{total}")

    def update_progress(self, current: int, total: int) -> None:
        self.progress_bar.config(value=current)
        self.progress_label.config(text=f"{current}/{total}")

    def reset(self) -> None:
        self.progress_bar.config(value=0)
        self.progress_label.config(text="")
        self.create_btn.config(state="normal")
