from __future__ import annotations

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import TYPE_CHECKING

from models import TaskEntry

if TYPE_CHECKING:
    from gui.app import App


class StagingPanel(ttk.LabelFrame):
    def __init__(self, parent_frame: tk.Widget, app: App):
        super().__init__(parent_frame, text="등록 대기 목록 (0개)")
        self.app = app
        self.tasks: list[TaskEntry] = []

        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=(5, 0))

        ttk.Button(toolbar, text="편집", command=self._edit_selected).pack(side="left", padx=(0, 3))
        ttk.Button(toolbar, text="삭제", command=self._delete_selected).pack(side="left", padx=(0, 3))
        ttk.Button(toolbar, text="전체 비우기", command=self._clear_all).pack(side="left")

        self.count_label = ttk.Label(toolbar, text="")
        self.count_label.pack(side="right")

        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("num", "date", "summary", "status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("num", text="#")
        self.tree.heading("date", text="날짜")
        self.tree.heading("summary", text="내용")
        self.tree.heading("status", text="상태")

        self.tree.column("num", width=40, stretch=False, anchor="center")
        self.tree.column("date", width=100, stretch=False)
        self.tree.column("summary", width=400, stretch=True)
        self.tree.column("status", width=80, stretch=False, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.tag_configure("pending", foreground="gray")
        self.tree.tag_configure("created", foreground="blue")
        self.tree.tag_configure("done", foreground="green")
        self.tree.tag_configure("error", foreground="red")

        # 클릭하면 자동으로 포커스
        self.tree.bind("<Button-1>", lambda _: self.tree.focus_set())

        # 더블클릭 or Enter → 편집
        self.tree.bind("<Double-1>", lambda _: self._edit_selected())
        self.tree.bind("<Return>", lambda _: self._edit_selected())

        # Delete / BackSpace → 삭제
        self.tree.bind("<Delete>", lambda _: self._delete_selected())
        self.tree.bind("<BackSpace>", lambda _: self._delete_selected())

    def add_tasks(self, new_tasks: list[TaskEntry]) -> None:
        for task in new_tasks:
            self.tasks.append(task)
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, task in enumerate(self.tasks):
            status_text = {
                "pending": "대기",
                "created": "생성됨",
                "done": "완료",
                "error": "오류",
            }.get(task.status, task.status)

            self.tree.insert("", "end", iid=str(i), values=(
                i + 1, task.date, task.summary, status_text,
            ), tags=(task.status,))

        self._update_count()

    def _update_count(self) -> None:
        n = len(self.tasks)
        self.configure(text=f"등록 대기 목록 ({n}개)")

    def update_task_status(self, index: int, status: str, issue_key: str = "") -> None:
        if 0 <= index < len(self.tasks):
            task = self.tasks[index]
            task.status = status
            if issue_key:
                task.issue_key = issue_key

            status_text = {
                "pending": "대기",
                "created": "생성됨",
                "done": "완료",
                "error": "오류",
            }.get(status, status)

            self.tree.item(str(index), values=(
                index + 1, task.date, task.summary, status_text,
            ), tags=(status,))

    def _edit_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        task = self.tasks[idx]

        new_summary = simpledialog.askstring(
            "태스크 편집",
            "내용:",
            initialvalue=task.summary,
            parent=self,
        )
        if new_summary and new_summary.strip():
            task.summary = new_summary.strip()
            self._refresh_tree()

    def _delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return

        indices = sorted([int(s) for s in selected], reverse=True)
        for idx in indices:
            if 0 <= idx < len(self.tasks):
                self.tasks.pop(idx)
        self._refresh_tree()

    def _clear_all(self) -> None:
        self.tasks.clear()
        self._refresh_tree()

    def get_pending_tasks(self) -> list[TaskEntry]:
        return [t for t in self.tasks if t.status == "pending"]
