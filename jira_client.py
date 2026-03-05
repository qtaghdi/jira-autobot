from __future__ import annotations

import requests

from config import AppConfig
from models import TaskEntry


class JiraApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Jira API Error ({status_code}): {message}")


class JiraClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.auth = (self.config.jira_email, self.config.jira_api_token)
        session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        return session

    def test_connection(self) -> tuple[bool, str]:
        try:
            resp = self.session.get(f"{self.config.jira_url}/rest/api/3/myself")
            if resp.status_code == 200:
                name = resp.json().get("displayName", "Unknown")
                return True, f"Connected as: {name}"
            return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.ConnectionError:
            return False, "Connection failed. Check JIRA_URL."
        except Exception as e:
            return False, str(e)

    def create_subtask(self, task: TaskEntry, parent_key: str) -> str:
        url = f"{self.config.jira_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.config.project_key},
                "parent": {"key": parent_key},
                "summary": task.summary,
                "issuetype": {"name": "하위 작업"},
                "assignee": {"accountId": self.config.assignee_account_id},
                "duedate": task.date,
                self.config.start_date_field: task.date,
            }
        }

        resp = self.session.post(url, json=payload)
        if resp.status_code not in (200, 201):
            raise JiraApiError(resp.status_code, resp.text[:500])

        data = resp.json()
        return data["key"]

    def transition_to_done(self, issue_key: str) -> None:
        url = f"{self.config.jira_url}/rest/api/3/issue/{issue_key}/transitions"
        resp = self.session.get(url)
        if resp.status_code != 200:
            raise JiraApiError(resp.status_code, resp.text[:500])

        transitions = resp.json().get("transitions", [])
        done_transition = None
        for t in transitions:
            if (t["name"] == self.config.done_status_name
                    or t.get("to", {}).get("name") == self.config.done_status_name):
                done_transition = t
                break

        if not done_transition:
            available = [f"{t['name']}(id={t['id']})" for t in transitions]
            raise JiraApiError(
                0,
                f"'{self.config.done_status_name}' transition not found. "
                f"Available: {', '.join(available)}"
            )

        resp = self.session.post(url, json={"transition": {"id": done_transition["id"]}})
        if resp.status_code not in (200, 204):
            raise JiraApiError(resp.status_code, resp.text[:500])

    def create_and_complete_task(self, task: TaskEntry, parent_key: str) -> None:
        issue_key = self.create_subtask(task, parent_key)
        task.issue_key = issue_key
        task.status = "created"

        self.transition_to_done(issue_key)
        task.status = "done"
