from __future__ import annotations

import json

from groq import Groq

from models import CommitInfo, TaskEntry

MODEL_NAME = "llama-3.3-70b-versatile"


def analyze_commits(commits: list[CommitInfo], api_key: str) -> list[TaskEntry]:
    client = Groq(api_key=api_key)

    prompt = _build_prompt(commits)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return _parse_response(response.choices[0].message.content)


def _build_prompt(commits: list[CommitInfo]) -> str:
    commit_text = "\n".join(
        f"[{c.date}] {c.hash} - {c.message}"
        for c in commits
    )
    return f"""아래 git 커밋 목록을 분석해서 Jira 서브태스크 요약을 만들어줘.

규칙:
1. 날짜별로 묶되, 하루에 태스크를 최대 3개로 제한해
2. 비슷하거나 연관된 커밋은 반드시 하나로 합쳐. 세세하게 쪼개지 말고 큰 단위로 묶어
3. 예: "로그인 버그 수정", "상품 목록 API 개선", "배포 및 환경 설정" 같은 굵직한 업무 단위
4. 요약은 한 줄, 50자 이내, 동사로 끝내지 말고 명사형으로 끝내
5. 커밋 메시지가 한국어면 한국어로, 영어면 한국어로 번역해서 작성
6. 반드시 아래 JSON 형식으로만 응답, 설명 없이:

{{"YYYY-MM-DD": ["태스크 요약 1", "태스크 요약 2"], ...}}

커밋 목록:
{commit_text}"""


def _parse_response(response_text: str) -> list[TaskEntry]:
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    data = json.loads(cleaned)
    tasks: list[TaskEntry] = []
    for date_str, summaries in sorted(data.items()):
        for summary in summaries:
            tasks.append(TaskEntry(date=date_str, summary=summary))
    return tasks
