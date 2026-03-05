from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).resolve().parent / ".env"


def _load_env() -> None:
    load_dotenv(ENV_PATH, override=True)


@dataclass
class AppConfig:
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    project_key: str = ""
    parent_issue_key: str = ""
    assignee_account_id: str = ""
    start_date_field: str = "customfield_10015"
    done_status_name: str = "완료"
    groq_api_key: str = ""

    @classmethod
    def from_env(cls) -> AppConfig:
        _load_env()
        return cls(
            jira_url=os.getenv("JIRA_URL", ""),
            jira_email=os.getenv("JIRA_EMAIL", ""),
            jira_api_token=os.getenv("JIRA_API_TOKEN", ""),
            project_key=os.getenv("JIRA_PROJECT_KEY", ""),
            parent_issue_key=os.getenv("JIRA_PARENT_ISSUE_KEY", ""),
            assignee_account_id=os.getenv("JIRA_ASSIGNEE_ACCOUNT_ID", ""),
            start_date_field=os.getenv("JIRA_START_DATE_FIELD", "customfield_10015"),
            done_status_name=os.getenv("JIRA_DONE_STATUS_NAME", "완료"),
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
        )

    def save_to_env(self) -> None:
        if not ENV_PATH.exists():
            ENV_PATH.touch()
        set_key(str(ENV_PATH), "JIRA_URL", self.jira_url)
        set_key(str(ENV_PATH), "JIRA_EMAIL", self.jira_email)
        set_key(str(ENV_PATH), "JIRA_API_TOKEN", self.jira_api_token)
        set_key(str(ENV_PATH), "JIRA_PROJECT_KEY", self.project_key)
        set_key(str(ENV_PATH), "JIRA_PARENT_ISSUE_KEY", self.parent_issue_key)
        set_key(str(ENV_PATH), "JIRA_ASSIGNEE_ACCOUNT_ID", self.assignee_account_id)
        set_key(str(ENV_PATH), "JIRA_START_DATE_FIELD", self.start_date_field)
        set_key(str(ENV_PATH), "JIRA_DONE_STATUS_NAME", self.done_status_name)
        set_key(str(ENV_PATH), "GROQ_API_KEY", self.groq_api_key)
