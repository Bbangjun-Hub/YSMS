# YouTube 메일링 서비스 (YSMS)

YouTube 채널의 최신 콘텐츠를 자동으로 요약하여 이메일로 발송하는 서비스입니다.

## 기능

- YouTube 채널 구독 관리
- 자동 자막 추출 및 AI 요약
- 스케줄된 이메일 발송
- Gmail API 연동
- OpenAI GPT-4o를 통한 콘텐츠 요약

## 설치 및 설정

### 1. 환경 변수 설정

`backend/.env` 파일을 생성하고 다음 내용을 입력하세요:

```bash
# Django 설정
SECRET_KEY=your_secret_key_here
DEBUG=True

# 데이터베이스 설정
DATABASE_URL=postgresql://postgres:postgres@db:5432/youtube_mail_db

# Redis 설정 (Celery)
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key_here

# 이메일 설정 (SMTP)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
DEFAULT_FROM_EMAIL=your_email@gmail.com

# YouTube API 설정
YOUTUBE_API_KEY=your_youtube_api_key_here
```

### 2. API 키 발급

#### OpenAI API 키

1. [OpenAI 플랫폼](https://platform.openai.com/)에 접속
2. API Keys 섹션에서 새 키 생성
3. `.env` 파일의 `OPENAI_API_KEY`에 입력

#### YouTube API 키

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. 사용자 인증 정보 생성 (OAuth 2.0 클라이언트 ID)
5. `credentials.json` 파일을 프로젝트 루트에 저장

#### Gmail API 설정

1. Google Cloud Console에서 Gmail API 활성화
2. OAuth 2.0 동의 화면 설정
3. 필요한 스코프 추가:
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.readonly`
   - `https://www.googleapis.com/auth/gmail.labels`

### 3. 토큰 생성

```bash
cd backend
python generate_token.py
```

### 4. Docker 실행

```bash
docker-compose up --build
```

## 사용법

### 1. 구독 추가

- 프론트엔드 (http://localhost:3000)에서 구독 관리
- 또는 Django Admin (http://localhost:8000/admin)에서 직접 관리

### 2. 수동 요약 처리

```bash
curl -X POST http://localhost:8000/api/subscriptions/admin/process-youtube-summaries/ \
     -H "Content-Type: application/json"
```

### 3. 로그 확인

```bash
docker-compose logs backend
```

## 프로젝트 구조

```
├── backend/                 # Django 백엔드
│   ├── subscriptions/       # 구독 관리 앱
│   ├── youtube_download.py  # YouTube 자막 다운로더
│   ├── auth_manager.py      # Google API 인증 관리
│   ├── generate_token.py    # 토큰 생성 스크립트
│   └── .env                 # 환경 변수 파일
├── frontend/                # React 프론트엔드
├── docker-compose.yml       # Docker 설정
├── credentials.json         # Google API 인증 파일
└── token.json              # Google API 토큰 파일
```

## 문제 해결

### 1. Gmail API 권한 오류

- `token.json` 파일 삭제 후 재생성
- OAuth 동의 화면에서 스코프 확인

### 2. OpenAI API 오류

- API 키 유효성 확인
- 사용량 한도 확인

### 3. YouTube API 오류

- `credentials.json` 파일 확인
- API 할당량 확인

## 라이선스

MIT License
