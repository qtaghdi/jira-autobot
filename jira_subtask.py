"""
Jira 서브태스크 자동 등록 스크립트

data.json 파일에서 날짜별 업무 목록을 읽어,
Jira Cloud의 부모 이슈 아래에 서브태스크로 자동 등록합니다.

사전 준비:
  1. https://id.atlassian.com/manage-profile/security/api-tokens 에서 API 토큰 생성
  2. 아래 설정값(JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, PROJECT_KEY, PARENT_ISSUE_KEY) 입력
  3. pip install requests

사용법:
  python jira_subtask.py                          # data.json 사용
  python jira_subtask.py --data other.json         # 다른 파일 지정
  python jira_subtask.py --parent PROJ-456        # 부모 이슈 지정
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests

# ============================================================
# 설정 영역 - 본인 환경에 맞게 수정하세요
# ============================================================
JIRA_URL = "https://your-domain.atlassian.net"
JIRA_EMAIL = "your-email@example.com"
JIRA_API_TOKEN = "your-api-token"
PROJECT_KEY = "DEV"
PARENT_ISSUE_KEY = "DEV-44"
ASSIGNEE_ACCOUNT_ID = ""
YEAR = 2025

# Start date 커스텀 필드 ID (Jira 설정에 따라 다름)
# 확인 방법: GET /rest/api/3/field 호출 후 "Start date" 또는 "시작일" 검색
START_DATE_FIELD = "customfield_10015"

# 완료 상태 이름 (Jira 워크플로우에 따라 다름: "Done", "완료", "Closed" 등)
DONE_STATUS_NAME = "완료"

def load_data(path: str | Path) -> list[tuple[str, str]]:
    """data.json을 읽어 (YYYY-MM-DD, tasks) 리스트를 날짜 오름차순으로 반환한다."""
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    entries = [(f"{YEAR}-{key}", value) for key, value in raw.items()]
    entries.sort(key=lambda x: x[0])
    return entries


def parse_chat_message(text: str) -> list[str]:
    """채팅 메시지를 파싱하여 서브태스크 제목 목록을 반환한다.

    첫 줄이 '이름 [오전/오후 H:MM]' 형식이면 헤더로 간주하고 건너뛴다.
    빈 줄은 무시한다.
    """
    lines = text.strip().splitlines()
    tasks = []
    header_pattern = re.compile(r".+\s+\[오[전후]\s+\d{1,2}:\d{2}\]")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if header_pattern.match(stripped):
            continue
        tasks.append(stripped)

    return tasks


def create_session() -> requests.Session:
    """Jira API 인증이 설정된 세션을 생성한다."""
    session = requests.Session()
    session.auth = (JIRA_EMAIL, JIRA_API_TOKEN)
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return session


def create_subtask(
    session: requests.Session,
    parent_key: str,
    summary: str,
    task_date: str,
) -> dict:
    """Jira에 서브태스크를 생성하고 응답을 반환한다."""
    url = f"{JIRA_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "parent": {"key": parent_key},
            "summary": summary,
            "issuetype": {"name": "하위 작업"},
            "assignee": {"accountId": ASSIGNEE_ACCOUNT_ID},
            "duedate": task_date,
            START_DATE_FIELD: task_date,
        }
    }

    print(f"  [DEBUG] URL: {url}")
    print(f"  [DEBUG] Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    resp = session.post(url, json=payload)
    print(f"  [DEBUG] Status: {resp.status_code}")
    print(f"  [DEBUG] Response: {resp.text}")
    if resp.status_code not in (200, 201):
        print(f"  [ERROR] 서브태스크 생성 실패: {resp.status_code}")
        resp.raise_for_status()

    data = resp.json()
    print(f"  [OK] 생성됨: {data['key']} - {summary}")
    return data


def transition_to_done(session: requests.Session, issue_key: str) -> None:
    """이슈의 상태를 완료로 전환한다."""
    # 사용 가능한 전환 목록 조회
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/transitions"
    resp = session.get(url)
    resp.raise_for_status()

    transitions = resp.json().get("transitions", [])
    done_transition = None
    for t in transitions:
        if t["name"] == DONE_STATUS_NAME or t.get("to", {}).get("name") == DONE_STATUS_NAME:
            done_transition = t
            break

    if not done_transition:
        available = [f"{t['name']}(id={t['id']})" for t in transitions]
        print(f"  [WARN] '{DONE_STATUS_NAME}' 전환을 찾을 수 없습니다.")
        print(f"         사용 가능한 전환: {', '.join(available)}")
        print(f"         DONE_STATUS_NAME 설정을 확인하세요.")
        return

    # 전환 실행
    resp = session.post(url, json={"transition": {"id": done_transition["id"]}})
    if resp.status_code == 204:
        print(f"  [OK] 상태 전환 완료: {issue_key} → {DONE_STATUS_NAME}")
    else:
        print(f"  [ERROR] 상태 전환 실패: {resp.status_code} {resp.text}")


def main():
    script_dir = Path(__file__).resolve().parent
    default_data = script_dir / "data.json"

    parser = argparse.ArgumentParser(description="data.json → Jira 서브태스크 자동 등록")
    parser.add_argument("--data", default=str(default_data),
                        help=f"데이터 파일 경로 (기본: {default_data})")
    parser.add_argument("--parent", default=PARENT_ISSUE_KEY,
                        help=f"부모 이슈 키 (기본: {PARENT_ISSUE_KEY})")
    args = parser.parse_args()

    # 설정 확인
    if "your-domain" in JIRA_URL or "your-email" in JIRA_EMAIL or "your-api-token" in JIRA_API_TOKEN:
        print("=" * 60)
        print("Jira 설정이 필요합니다!")
        print()
        print("1. https://id.atlassian.com/manage-profile/security/api-tokens")
        print("   에서 API 토큰을 생성하세요.")
        print("2. 스크립트 상단의 설정값을 수정하세요:")
        print("   - JIRA_URL")
        print("   - JIRA_EMAIL")
        print("   - JIRA_API_TOKEN")
        print("   - PROJECT_KEY")
        print("   - PARENT_ISSUE_KEY")
        print("=" * 60)
        sys.exit(1)

    entries = load_data(args.data)
    if not entries:
        print("데이터가 비어 있습니다. 데이터 파일을 확인하세요.")
        sys.exit(1)

    session = create_session()

    for task_date, raw_tasks in entries:
        tasks = parse_chat_message(raw_tasks)
        if not tasks:
            print(f"[{task_date}] 파싱된 서브태스크가 없습니다. 건너뜁니다.")
            continue

        print(f"=== {task_date} ({len(tasks)}개) ===")
        print(f"부모 이슈: {args.parent}")
        for i, t in enumerate(tasks, 1):
            print(f"  {i}. {t}")
        print()

        for task_summary in tasks:
            try:
                result = create_subtask(session, args.parent, task_summary, task_date)
                issue_key = result["key"]
                transition_to_done(session, issue_key)
            except requests.HTTPError:
                print(f"  [SKIP] '{task_summary}' 처리 중 오류 발생, 다음으로 넘어갑니다.")
            print()

    print("완료!")


if __name__ == "__main__":
    main()
