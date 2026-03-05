from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from config import AppConfig
from jira_client import JiraClient


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, config: AppConfig, on_save: callable):
        super().__init__(parent)
        self.title("설정")
        self.geometry("520x480")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = config
        self.on_save = on_save

        self._build_ui()
        self._load_values()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 3}

        jira_frame = ttk.LabelFrame(self, text="Jira 설정")
        jira_frame.pack(fill="x", padx=10, pady=(10, 5))

        labels = [
            ("URL:", "jira_url"),
            ("이메일:", "jira_email"),
            ("API 토큰:", "jira_api_token"),
            ("프로젝트 키:", "project_key"),
            ("부모 이슈:", "parent_issue_key"),
            ("담당자 ID:", "assignee_account_id"),
            ("시작일 필드:", "start_date_field"),
            ("완료 상태명:", "done_status_name"),
        ]

        self.entries: dict[str, ttk.Entry] = {}
        for i, (label, key) in enumerate(labels):
            ttk.Label(jira_frame, text=label).grid(row=i, column=0, sticky="w", **pad)
            show = "*" if key == "jira_api_token" else ""
            entry = ttk.Entry(jira_frame, width=45, show=show)
            entry.grid(row=i, column=1, sticky="ew", **pad)
            self.entries[key] = entry

        jira_frame.columnconfigure(1, weight=1)

        gemini_frame = ttk.LabelFrame(self, text="Groq 설정")
        gemini_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(gemini_frame, text="API 키:").grid(row=0, column=0, sticky="w", **pad)
        entry = ttk.Entry(gemini_frame, width=45, show="*")
        entry.grid(row=0, column=1, sticky="ew", **pad)
        self.entries["groq_api_key"] = entry
        gemini_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(btn_frame, text="연결 테스트", command=self._test_connection).pack(side="left")
        ttk.Button(btn_frame, text="취소", command=self.destroy).pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="저장", command=self._save).pack(side="right")

    def _load_values(self) -> None:
        mapping = {
            "jira_url": self.config.jira_url,
            "jira_email": self.config.jira_email,
            "jira_api_token": self.config.jira_api_token,
            "project_key": self.config.project_key,
            "parent_issue_key": self.config.parent_issue_key,
            "assignee_account_id": self.config.assignee_account_id,
            "start_date_field": self.config.start_date_field,
            "done_status_name": self.config.done_status_name,
            "groq_api_key": self.config.groq_api_key,
        }
        for key, value in mapping.items():
            self.entries[key].insert(0, value)

    def _read_values(self) -> AppConfig:
        return AppConfig(
            jira_url=self.entries["jira_url"].get().strip(),
            jira_email=self.entries["jira_email"].get().strip(),
            jira_api_token=self.entries["jira_api_token"].get().strip(),
            project_key=self.entries["project_key"].get().strip(),
            parent_issue_key=self.entries["parent_issue_key"].get().strip(),
            assignee_account_id=self.entries["assignee_account_id"].get().strip(),
            start_date_field=self.entries["start_date_field"].get().strip(),
            done_status_name=self.entries["done_status_name"].get().strip(),
            groq_api_key=self.entries["groq_api_key"].get().strip(),
        )

    def _save(self) -> None:
        new_config = self._read_values()
        if not new_config.jira_url or not new_config.jira_email:
            messagebox.showwarning("경고", "Jira URL과 이메일은 필수입니다.", parent=self)
            return
        new_config.save_to_env()
        self.on_save(new_config)
        self.destroy()

    def _test_connection(self) -> None:
        config = self._read_values()
        if not config.jira_url or not config.jira_api_token:
            messagebox.showwarning("경고", "URL과 API 토큰을 입력하세요.", parent=self)
            return

        def _run():
            client = JiraClient(config)
            ok, msg = client.test_connection()
            self.after(0, lambda: messagebox.showinfo(
                "연결 테스트",
                msg,
                parent=self,
            ))

        threading.Thread(target=_run, daemon=True).start()
