# Youngrok Job Radar

평일마다 공개 채용 페이지를 확인해 마감·고용형태·직무 적합성을 검증하고, 조건을 통과한
공고만 텔레그램으로 보내는 개인 채용 레이더입니다.

## 동작 흐름

1. 08:20 KST에 원티드와 리멤버의 공개 검색/상세 페이지를 확인합니다.
2. 상세 페이지 접근, 지원하기 버튼, 마감일, 정규직 여부를 먼저 검증합니다.
3. 직무명이 선호 목록에 포함되고 명백한 UI/UX 직무가 아닌 공고만 AI로 분석합니다.
4. 공고에 있는 근거만으로 UI/UX 비중, 적합도, 회사 신호, 연봉 신뢰도를 산출합니다.
5. SQLite `fingerprint`로 중복을 막고 08:30에 상위 3~7개를 전송합니다.
6. 텔레그램 버튼으로 관심·지원 예정·제외·회사 제외 상태를 저장합니다.

엄격 기준을 통과한 공고가 0건이면 명백한 비정규직·마감·지원 불가·UI/UX 중심 직무를
제외한 후보 중 최고점 1건을 보냅니다. 정규직 여부가 불명확하면 메시지에 확인 경고를
표시합니다.

점수 명세의 구성요소 합계는 최대 90점(직무 35 + 회사 30 + 지원 현실성 25)입니다.
따라서 예시에 맞춰 72점을 기본 발송 기준으로 사용합니다.

## 빠른 검증

Python 3.12 이상이 필요합니다.

```bash
cd /Users/goorm/Documents/포트폴리오/youngrok-job-radar
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
playwright install chromium
python -m job_radar dry-run
```

`dry-run`은 API 키, 텔레그램, 실제 웹 접속 없이 `data/sample_jobs.json`을 사용합니다.
샘플 3건 중 정규직 브랜드 공고 1건만 최종 메시지로 출력되어야 합니다.

## 사용자가 준비할 값

1. Telegram에서 `@BotFather`에게 `/newbot`을 보내 봇 토큰을 발급합니다.
2. 발급한 봇에게 아무 메시지나 한 번 보냅니다.
3. 아래 주소를 브라우저에서 열어 응답의 `message.chat.id`를 확인합니다.

   ```text
   https://api.telegram.org/bot<봇토큰>/getUpdates
   ```

4. [OpenAI API 키 페이지](https://platform.openai.com/api-keys)에서 프로젝트 API 키를
   발급하고 사용 한도를 설정합니다.
5. `.env.example`을 `.env`로 복사한 뒤 다음 값을 채웁니다.

   ```dotenv
   OPENAI_API_KEY=...
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   TELEGRAM_ADMIN_CHAT_ID=...
   ```

`TELEGRAM_ADMIN_CHAT_ID`를 비우면 일반 채팅방으로 오류를 알립니다. 비밀값이 든 `.env`와
SQLite DB는 Git에 포함되지 않습니다.

## 실행 명령

```bash
# DB 테이블만 초기화
python -m job_radar init-db

# 실제 사이트 수집·분석·즉시 전송
python -m job_radar run

# 수집·분석과 전송을 따로 점검
python -m job_radar collect
python -m job_radar send

# 08:20 수집, 08:30 전송, 텔레그램 버튼 처리 상시 실행
python -m job_radar serve
```

처음에는 `HEADLESS=false python -m job_radar collect`로 브라우저를 보면서 사이트 접근과
지원 버튼 인식을 확인하는 것이 안전합니다.

## 설정

개인 조건과 점수 기준은 `preferences.yaml`에서 수정합니다. OpenAI 모델은
`OPENAI_MODEL`로 바꿀 수 있으며 기본값은 비용 민감한 일일 분류에 맞춘
`gpt-5.6-luna`입니다. 구현은 OpenAI 공식
[Responses API 구조화 출력](https://developers.openai.com/api/docs/guides/structured-outputs)의
Pydantic 파싱 방식을 사용합니다.

AI는 최종 진실 공급원이 아닙니다. 아래 조건은 코드가 먼저 검증합니다.

- 상세 페이지 접근 가능
- 지원하기 버튼 존재
- 마감일이 지나지 않음
- 정규직이 명시됨(0건일 때는 불명확 후보 1건에 경고 표시)
- 계약직·인턴·파견직이 아님
- 직무명이 선호 목록에 포함됨

공식 공고와 플랫폼 공고가 충돌하면 공식 페이지를 우선해야 합니다. 현재 MVP는 플랫폼
상세 페이지까지만 자동 검증하며, 회사 공식 채용 페이지 교차 확인은 다음 단계입니다.

## 테스트와 품질 검사

```bash
ruff check .
mypy
pytest
python -m job_radar dry-run
```

테스트는 fingerprint 중복 제거, 마감·정규직·UI/UX 필터, JSON-LD 파싱, 점수 재계산,
SQLite 상태 보존, 전체 dry-run 흐름을 검증합니다.

## 상시 서버 운영(선택)

텔레그램의 관심·지원 예정·제외 버튼까지 상시 사용하려면 Railway/Render/Fly.io 같은
서버에서 `python -m job_radar serve`를 실행해야 합니다. 영속 볼륨을 `/app/data`에
연결하고 다음처럼 DB 경로를 지정해야 재배포 후에도 중복 이력이 유지됩니다.

```dotenv
DATABASE_URL=sqlite:////app/data/jobs.db
```

현재 기본 운영 방식은 아래의 무료 GitHub Actions입니다. 상시 서버는 텔레그램 상태 버튼이
실제로 필요해졌을 때만 전환하는 선택지입니다.

## 운영상 제한과 안전

- 공개 페이지를 개인 구직 목적으로 낮은 빈도로 읽으며 로그인·CAPTCHA·차단을 우회하지
  않습니다. 각 사이트 약관이나 robots 정책이 자동 수집을 금지하면 해당 수집기를 끄고
  공식 API/알림 메일 입력 방식으로 교체해야 합니다.
- 사이트 DOM이 바뀌면 링크나 지원 버튼 탐지가 실패할 수 있습니다. 이 경우 잘못된 공고를
  보내지 않고 해당 공고를 제외합니다.
- 평판·연봉 근거가 공고에 없으면 정보를 만들지 않습니다. 현재는 `정보 없음`으로 표시합니다.
- 입력 공고 본문은 OpenAI API로 전송됩니다. 개인 지원서나 민감정보는 수집 대상에 넣지
  마세요.

## 구조

```text
src/job_radar/
├── collectors/       # 원티드·리멤버 공개 페이지와 JSON-LD 파서
├── analyzer.py       # OpenAI 구조화 분석 / 로컬 dry-run 분석
├── config.py         # YAML·환경변수
├── database.py       # SQLite 중복·상태·회사 블랙리스트
├── main.py           # CLI
├── scheduler.py      # 08:20/08:30 스케줄
├── service.py        # 수집→검증→분석→발송 흐름
├── telegram.py       # 메시지·인라인 버튼·콜백
└── validation.py     # 보수적 사전 필터
```

FastAPI, 관리 대시보드, 피드백 기반 자동학습은 MVP 범위에서 제외했습니다. 실제 오탐·누락
데이터가 쌓인 뒤 필요성이 확인될 때 추가하는 편이 안전합니다.

## GitHub Actions 무료 운영

저장소 루트의 `.github/workflows/job-radar.yml`은 평일 KST 08:25에 실행을 시작합니다.
의존성 설치와 수집이 끝나는 08:30 전후에 텔레그램 메시지가 도착합니다. GitHub 실행이
지연되면 발송도 늦어질 수 있습니다.

Actions Secrets에는 다음 값을 등록해야 합니다.

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TELEGRAM_ADMIN_CHAT_ID`

Actions 환경에서는 `ENABLED_COLLECTORS=remember`, `TELEGRAM_INTERACTIVE=false`를 사용합니다.
원티드는 GitHub 호스팅 브라우저 요청을 차단하므로 제외하고, 상시 콜백 프로세스가 없기
때문에 텔레그램 상태 버튼 대신 공고 링크만 표시합니다.

SQLite DB는 Actions 캐시에 보존됩니다. 캐시는 무료 MVP에 적합한 최선형 저장소이므로
캐시가 정리되면 과거 공고가 한 번 재발송될 수 있습니다. 이 문제가 실제로 발생하면 무료
데이터베이스 또는 유료 영속 볼륨으로 이전해야 합니다.
