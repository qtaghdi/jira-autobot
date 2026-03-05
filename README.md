# Jira Autobot

Git 커밋 로그 또는 직접 입력한 업무 목록을 기반으로 Jira 서브태스크를 자동 생성하고 완료 처리하는 GUI 도구입니다.

## 주요 기능

- **Git 커밋 분석**: Git 저장소의 커밋 로그를 Groq LLM으로 분석하여 Jira 태스크 자동 생성
- **오늘 한 일 입력**: 수동으로 업무 내용을 입력하여 서브태스크 등록
- **JSON 파일 불러오기**: 날짜별 업무 목록이 담긴 JSON 파일에서 일괄 등록
- **서브태스크 자동 완료**: 생성된 서브태스크를 즉시 "완료" 상태로 전환
- **GUI 설정 관리**: Jira/Groq 설정을 GUI에서 편집하고 `.env`에 저장

## 사전 준비

1. **Python 3.10+**
2. **Jira API 토큰**: [Atlassian API 토큰 관리](https://id.atlassian.com/manage-profile/security/api-tokens)에서 생성
3. **Groq API 키**: [Groq Console](https://console.groq.com)에서 발급 (Git 커밋 분석 기능 사용 시)

## 설치

```bash
git clone https://github.com/your-username/jira-autobot.git
cd jira-autobot
pip install -r requirements.txt
```

## 설정

`.env.example`을 복사하여 `.env` 파일을 만들고 값을 채웁니다:

```bash
cp .env.example .env
```

```env
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=DEV
JIRA_PARENT_ISSUE_KEY=DEV-44
JIRA_ASSIGNEE_ACCOUNT_ID=your-account-id
JIRA_START_DATE_FIELD=customfield_10015
JIRA_DONE_STATUS_NAME=완료
GROQ_API_KEY=your-groq-api-key
```

| 변수 | 설명 |
|------|------|
| `JIRA_URL` | Jira Cloud 인스턴스 URL |
| `JIRA_EMAIL` | Jira 로그인 이메일 |
| `JIRA_API_TOKEN` | Jira API 토큰 |
| `JIRA_PROJECT_KEY` | 프로젝트 키 (예: `DEV`) |
| `JIRA_PARENT_ISSUE_KEY` | 서브태스크를 붙일 부모 이슈 키 |
| `JIRA_ASSIGNEE_ACCOUNT_ID` | 담당자 Account ID |
| `JIRA_START_DATE_FIELD` | 시작일 커스텀 필드 ID (`GET /rest/api/3/field`로 확인) |
| `JIRA_DONE_STATUS_NAME` | 완료 상태 이름 (워크플로우에 따라 `완료`, `Done` 등) |
| `GROQ_API_KEY` | Groq API 키 (Git 커밋 분석용) |

또는 앱 실행 후 **설정** 버튼에서 GUI로 설정할 수 있습니다.

## 실행

```bash
python main.py
```

### 사용 방법

#### 1. Git 커밋 분석
1. "Git 커밋 분석" 탭 선택
2. Git 저장소 경로와 기간 입력
3. "분석 후 목록에 추가" 클릭 → Groq LLM이 커밋을 분석하여 태스크 목록 생성

#### 2. 오늘 한 일 입력
1. "오늘 한 일 입력" 탭 선택
2. 날짜 확인 후 업무 내용을 한 줄에 하나씩 입력
3. "목록에 추가" 클릭

#### 3. JSON 파일 불러오기
1. "JSON 파일" 탭 선택
2. JSON 파일 선택 및 연도 입력
3. "불러와서 목록에 추가" 클릭

JSON 형식:
```json
{
  "02-09": "태스크1\n태스크2\n태스크3",
  "02-10": "태스크1\n태스크2"
}
```

#### 4. Jira 등록
1. 등록 대기 목록에서 태스크 확인 (편집/삭제 가능)
2. "Jira에 서브태스크 생성" 클릭
3. 처리 로그에서 결과 확인

## CLI (독립 실행 스크립트)

`jira_subtask.py`는 GUI 없이 `data.json`에서 직접 서브태스크를 등록하는 스크립트입니다:

```bash
python jira_subtask.py                    # data.json 사용
python jira_subtask.py --data other.json  # 다른 파일 지정
python jira_subtask.py --parent DEV-99    # 부모 이슈 지정
```

> **참고**: CLI 스크립트는 `.env` 대신 파일 내 상수를 직접 수정해야 합니다.

## 프로젝트 구조

```
jira-autobot/
├── main.py              # 앱 진입점
├── config.py            # .env 기반 설정 관리
├── models.py            # 데이터 모델 (CommitInfo, TaskEntry)
├── jira_client.py       # Jira REST API 클라이언트
├── git_client.py        # Git 로그 조회
├── groq_client.py       # Groq LLM 커밋 분석
├── data_parser.py       # 채팅/JSON 데이터 파서
├── jira_subtask.py      # CLI 독립 실행 스크립트
├── gui/
│   ├── app.py           # 메인 윈도우
│   ├── input_panel.py   # 입력 패널 (Git/수동/JSON)
│   ├── staging_panel.py # 등록 대기 목록
│   ├── action_panel.py  # 실행 버튼 및 로그
│   └── settings_dialog.py # 설정 다이얼로그
├── requirements.txt
├── .env.example
└── .gitignore
```
