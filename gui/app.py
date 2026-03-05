from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from config import AppConfig
from models import TaskEntry
from jira_client import JiraClient, JiraApiError
from gui.settings_dialog import SettingsDialog
from gui.input_panel import InputPanel
from gui.staging_panel import StagingPanel
from gui.action_panel import ActionPanel


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Jira 서브태스크 생성기")
        self.geometry("900x750")
        self.minsize(800, 600)

        self.app_config = AppConfig.from_env()
        self._running = False

        self._build_ui()
        self.update_idletasks()
        self.lift()
        self.focus_force()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=10, pady=(8, 0))

        ttk.Button(toolbar, text="설정", command=self._open_settings).pack(side="left")
        ttk.Label(toolbar, text="Jira 서브태스크 생성기", font=("", 14, "bold")).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=5)

        self.input_panel = InputPanel(self, self)
        self.input_panel.pack(fill="x", padx=10, pady=(0, 5))

        self.staging_panel = StagingPanel(self, self)
        self.staging_panel.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.action_panel = ActionPanel(self, self)
        self.action_panel.pack(fill="x", padx=10, pady=(0, 8))

    def _open_settings(self) -> None:
        SettingsDialog(self, self.app_config, self._on_config_saved)

    def _on_config_saved(self, new_config: AppConfig) -> None:
        self.app_config = new_config
        self.action_panel.log("[정보] 설정이 저장되었습니다.", "info")

    def add_tasks_to_staging(self, tasks: list[TaskEntry]) -> None:
        self.staging_panel.add_tasks(tasks)
        self.action_panel.log(f"[정보] {len(tasks)}개 태스크가 목록에 추가되었습니다.", "info")

    def on_create_all(self) -> None:
        pending = self.staging_panel.get_pending_tasks()
        if not pending:
            messagebox.showinfo("알림", "생성할 태스크가 없습니다.")
            return

        if not self.app_config.jira_url or not self.app_config.jira_api_token:
            messagebox.showwarning("경고", "Jira 설정이 없습니다. 설정을 먼저 완료하세요.")
            return

        parent_key = self.app_config.parent_issue_key
        if not parent_key:
            messagebox.showwarning("경고", "부모 이슈 키가 설정되지 않았습니다. 설정을 확인하세요.")
            return

        confirm = messagebox.askyesno(
            "확인",
            f"{parent_key} 아래에 서브태스크 {len(pending)}개를 Jira에 생성할까요?",
        )
        if not confirm:
            return

        self._running = True
        self.action_panel.create_btn.config(state="disabled")
        self.action_panel.start_progress(len(pending))

        thread = threading.Thread(target=self._create_tasks_worker, args=(pending, parent_key), daemon=True)
        thread.start()

    def _create_tasks_worker(self, tasks: list[TaskEntry], parent_key: str) -> None:
        client = JiraClient(self.app_config)

        for i, task in enumerate(tasks):
            if not self._running:
                self.after(0, lambda: self.action_panel.log("[경고] 사용자가 취소했습니다.", "warn"))  # noqa
                break

            idx = self.staging_panel.tasks.index(task)

            try:
                client.create_and_complete_task(task, parent_key)
                self.after(0, self._on_task_done, idx, task)
            except JiraApiError as e:
                task.status = "error"
                task.error_msg = str(e)
                self.after(0, self._on_task_error, idx, task, str(e))
            except Exception as e:
                task.status = "error"
                task.error_msg = str(e)
                self.after(0, self._on_task_error, idx, task, str(e))

            self.after(0, self.action_panel.update_progress, i + 1, len(tasks))

        self.after(0, self._on_all_done)

    def _on_task_done(self, index: int, task: TaskEntry) -> None:
        self.staging_panel.update_task_status(index, "done", task.issue_key)
        self.action_panel.log(f"[완료] {task.issue_key} - {task.summary}", "ok")

    def _on_task_error(self, index: int, task: TaskEntry, error: str) -> None:
        self.staging_panel.update_task_status(index, "error")
        self.action_panel.log(f"[오류] {task.summary}: {error}", "error")

    def _on_all_done(self) -> None:
        self._running = False
        self.action_panel.create_btn.config(state="normal")
        self.action_panel.log("[정보] 모든 태스크 처리가 완료되었습니다.", "info")
