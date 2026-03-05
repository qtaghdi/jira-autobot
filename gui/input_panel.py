from __future__ import annotations

import datetime
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import TYPE_CHECKING

from models import TaskEntry

if TYPE_CHECKING:
    from gui.app import App


class InputPanel(ttk.LabelFrame):
    def __init__(self, parent_frame: tk.Widget, app: App):
        super().__init__(parent_frame, text="입력 방식")
        self.app = app

        self.source_var = tk.StringVar(value="daily")

        radio_frame = ttk.Frame(self)
        radio_frame.pack(fill="x", padx=8, pady=(5, 0))

        ttk.Radiobutton(radio_frame, text="Git 커밋 분석", value="git",
                         variable=self.source_var, command=self._on_source_changed).pack(side="left", padx=(0, 15))
        ttk.Radiobutton(radio_frame, text="오늘 한 일 입력", value="daily",
                         variable=self.source_var, command=self._on_source_changed).pack(side="left", padx=(0, 15))
        ttk.Radiobutton(radio_frame, text="JSON 파일", value="json",
                         variable=self.source_var, command=self._on_source_changed).pack(side="left")

        self.git_frame = self._build_git_frame()
        self.daily_frame = self._build_daily_frame()
        self.json_frame = self._build_json_frame()

        self._on_source_changed()

    def _build_git_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        pad = {"padx": 8, "pady": 3}

        ttk.Label(frame, text="저장소 경로:").grid(row=0, column=0, sticky="w", **pad)
        self.repo_entry = ttk.Entry(frame, width=40)
        self.repo_entry.grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(frame, text="찾아보기", command=self._browse_repo).grid(row=0, column=2, **pad)

        ttk.Label(frame, text="시작일:").grid(row=1, column=0, sticky="w", **pad)
        self.date_from_entry = ttk.Entry(frame, width=15)
        self.date_from_entry.grid(row=1, column=1, sticky="w", **pad)
        self.date_from_entry.insert(0, (datetime.date.today() - datetime.timedelta(days=7)).isoformat())

        ttk.Label(frame, text="종료일:").grid(row=2, column=0, sticky="w", **pad)
        self.date_to_entry = ttk.Entry(frame, width=15)
        self.date_to_entry.grid(row=2, column=1, sticky="w", **pad)
        self.date_to_entry.insert(0, datetime.date.today().isoformat())

        self.analyze_btn = ttk.Button(frame, text="분석 후 목록에 추가", command=self._analyze_commits)
        self.analyze_btn.grid(row=3, column=0, columnspan=3, pady=(5, 5))

        frame.columnconfigure(1, weight=1)
        return frame

    def _build_daily_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        pad = {"padx": 8, "pady": 3}

        date_frame = ttk.Frame(frame)
        date_frame.pack(fill="x", **pad)
        ttk.Label(date_frame, text="날짜:").pack(side="left")
        self.daily_date_entry = ttk.Entry(date_frame, width=15)
        self.daily_date_entry.pack(side="left", padx=(5, 0))
        self.daily_date_entry.insert(0, datetime.date.today().isoformat())
        ttk.Label(date_frame, text="(YYYY-MM-DD)", foreground="gray").pack(side="left", padx=(5, 0))

        self.daily_text = tk.Text(frame, height=6, width=50, wrap="word")
        self.daily_text.pack(fill="both", expand=True, **pad)
        self.daily_text.insert("1.0", "업무 내용을 한 줄에 하나씩 입력하세요...\n")
        self.daily_text.bind("<FocusIn>", self._clear_placeholder)

        ttk.Button(frame, text="목록에 추가", command=self._add_daily_tasks).pack(pady=(3, 5))

        return frame

    def _build_json_frame(self) -> ttk.Frame:
        frame = ttk.Frame(self)
        pad = {"padx": 8, "pady": 3}

        row = ttk.Frame(frame)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="파일:").pack(side="left")
        self.json_entry = ttk.Entry(row, width=40)
        self.json_entry.pack(side="left", fill="x", expand=True, padx=(5, 5))
        ttk.Button(row, text="찾아보기", command=self._browse_json).pack(side="left")

        year_row = ttk.Frame(frame)
        year_row.pack(fill="x", **pad)
        ttk.Label(year_row, text="연도:").pack(side="left")
        self.year_entry = ttk.Entry(year_row, width=6)
        self.year_entry.pack(side="left", padx=(5, 0))
        self.year_entry.insert(0, str(datetime.date.today().year))

        ttk.Button(frame, text="불러와서 목록에 추가", command=self._load_json).pack(pady=(3, 5))

        return frame

    def _on_source_changed(self) -> None:
        for f in (self.git_frame, self.daily_frame, self.json_frame):
            f.pack_forget()

        source = self.source_var.get()
        if source == "git":
            self.git_frame.pack(fill="both", expand=True, padx=5, pady=5)
        elif source == "daily":
            self.daily_frame.pack(fill="both", expand=True, padx=5, pady=5)
        elif source == "json":
            self.json_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def _clear_placeholder(self, _event: tk.Event) -> None:
        content = self.daily_text.get("1.0", "end-1c")
        if content.startswith("업무 내용을"):
            self.daily_text.delete("1.0", tk.END)

    def _browse_repo(self) -> None:
        path = filedialog.askdirectory(title="Git 저장소 선택")
        if path:
            self.repo_entry.delete(0, tk.END)
            self.repo_entry.insert(0, path)

    def _browse_json(self) -> None:
        path = filedialog.askopenfilename(
            title="데이터 파일 선택",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
        )
        if path:
            self.json_entry.delete(0, tk.END)
            self.json_entry.insert(0, path)

    def _analyze_commits(self) -> None:
        repo_path = self.repo_entry.get().strip()
        date_from = self.date_from_entry.get().strip()
        date_to = self.date_to_entry.get().strip()

        if not repo_path:
            messagebox.showwarning("경고", "Git 저장소를 선택하세요.", parent=self)
            return

        from git_client import validate_repo, get_commits
        from groq_client import analyze_commits

        ok, msg = validate_repo(repo_path)
        if not ok:
            messagebox.showerror("오류", f"유효하지 않은 저장소: {msg}", parent=self)
            return

        gemini_key = self.app.app_config.groq_api_key
        if not gemini_key:
            messagebox.showwarning("경고", "Groq API 키가 설정되지 않았습니다. 설정을 확인하세요.", parent=self)
            return

        self.analyze_btn.config(state="disabled", text="분석 중...")

        def _run():
            try:
                commits = get_commits(repo_path, date_from, date_to)
                if not commits:
                    self.after(0, lambda: messagebox.showinfo(
                        "알림", "해당 기간에 커밋이 없습니다.", parent=self))
                    return
                tasks = analyze_commits(commits, gemini_key)
                self.after(0, lambda: self.app.add_tasks_to_staging(tasks))
            except Exception as e:
                err = str(e)
                self.after(0, lambda err=err: messagebox.showerror("오류", err, parent=self))
            finally:
                self.after(0, lambda: self.analyze_btn.config(state="normal", text="분석 후 목록에 추가"))

        threading.Thread(target=_run, daemon=True).start()

    def _add_daily_tasks(self) -> None:
        date_str = self.daily_date_entry.get().strip()
        text = self.daily_text.get("1.0", "end-1c").strip()

        if not date_str:
            messagebox.showwarning("경고", "날짜를 입력하세요.", parent=self)
            return
        if not text or text.startswith("업무 내용을"):
            messagebox.showwarning("경고", "업무 내용을 입력하세요.", parent=self)
            return

        bullet_pattern = re.compile(r"^[-•*]\s*")
        tasks: list[TaskEntry] = []
        for line in text.splitlines():
            stripped = bullet_pattern.sub("", line.strip())
            if stripped:
                tasks.append(TaskEntry(date=date_str, summary=stripped))

        if tasks:
            self.app.add_tasks_to_staging(tasks)
            self.daily_text.delete("1.0", tk.END)

    def _load_json(self) -> None:
        path = self.json_entry.get().strip()
        year_str = self.year_entry.get().strip()

        if not path:
            messagebox.showwarning("경고", "JSON 파일을 선택하세요.", parent=self)
            return

        try:
            year = int(year_str)
        except ValueError:
            messagebox.showwarning("경고", "연도가 올바르지 않습니다.", parent=self)
            return

        from data_parser import load_from_json

        try:
            tasks = load_from_json(path, year)
            if not tasks:
                messagebox.showinfo("알림", "파일에서 태스크를 찾을 수 없습니다.", parent=self)
                return
            self.app.add_tasks_to_staging(tasks)
        except Exception as e:
            messagebox.showerror("오류", str(e), parent=self)
