# 🚀 YouTube 메일링 서비스 설정 가이드

## 📋 **사전 요구사항**

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- Git

## 🔧 **1. 프로젝트 클론 및 초기 설정**

```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd Youtube-Mailing

# 2. 백엔드 환경 설정
cd backend
cp env.example .env
```

## 🔑 **2. 환경 변수 설정**

`backend/.env` 파일을 편집하여 다음 값들을 설정하세요:

```env
# Django 설정
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 데이터베이스 설정 (PostgreSQL)
DB_NAME=youtube_mailing
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# API 키 설정
OPENAI_API_KEY=your-openai-api-key-here
YOUTUBE_API_KEY=your-youtube-api-key-here

# 이메일 설정
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Gmail API 설정 (선택사항)
GMAIL_API_ENABLED=True
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Celery 설정
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🔐 **3. Google API 설정**

### **YouTube Data API**

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. API 키 생성 후 `YOUTUBE_API_KEY`에 설정

### **Gmail API (선택사항)**

1. Gmail API 활성화
2. OAuth 2.0 클라이언트 ID 생성
3. `credentials.json` 파일을 `backend/` 디렉토리에 저장
4. 토큰 생성: `python generate_token.py`

## 🐳 **4. Docker로 실행 (권장)**

```bash
# 프로젝트 루트에서 실행
docker-compose up -d

# 데이터베이스 초기화
docker-compose exec backend python init_db.py

# 로그 확인
docker-compose logs -f
```

## 🔧 **5. 로컬 개발 환경 설정**

### **백엔드 설정**

```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python init_db.py

# 개발 서버 실행
python manage.py runserver
```

### **프론트엔드 설정**

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

### **Celery 워커 실행**

```bash
cd backend

# Celery 워커 시작
celery -A youtube_mail_project worker --loglevel=info

# Celery Beat 스케줄러 시작 (별도 터미널)
celery -A youtube_mail_project beat --loglevel=info
```

## 📊 **6. 서비스 확인**

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **관리자 페이지**: http://localhost:8000/admin

## 🔍 **7. 문제 해결**

### **일반적인 오류들**

**1. Gmail API 권한 오류**

```bash
# 토큰 재생성
cd backend
python generate_token.py
```

**2. 데이터베이스 연결 오류**

```bash
# PostgreSQL 서비스 확인
docker-compose ps
docker-compose restart db
```

**3. Celery 작업 실패**

```bash
# Redis 연결 확인
docker-compose logs redis

# Celery 워커 재시작
docker-compose restart celery
```

## 🚀 **8. 프로덕션 배포**

### **환경 변수 수정**

```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com
```

### **정적 파일 수집**

```bash
python manage.py collectstatic
```

### **보안 설정**

- SECRET_KEY 변경
- HTTPS 설정
- 방화벽 구성
- 데이터베이스 보안 강화

## 📝 **9. 개발 참고사항**

### **주요 디렉토리 구조**

```
Youtube-Mailing/
├── backend/
│   ├── subscriptions/          # 구독 관리 앱
│   ├── youtube_mail_project/   # Django 프로젝트 설정
│   ├── init_db.py             # DB 초기화 스크립트
│   └── requirements.txt       # Python 의존성
├── frontend/
│   ├── src/components/        # React 컴포넌트
│   └── package.json          # Node.js 의존성
└── docker-compose.yml        # Docker 설정
```

### **API 엔드포인트**

- `POST /api/auth/register/` - 사용자 등록
- `POST /api/auth/login/` - 로그인
- `GET /api/subscriptions/` - 구독 목록
- `POST /api/subscriptions/` - 구독 추가
- `POST /api/admin/process-summaries/` - 요약 처리

## 🆘 **도움이 필요하신가요?**

1. **로그 확인**: `docker-compose logs -f [service-name]`
2. **컨테이너 상태**: `docker-compose ps`
3. **데이터베이스 접속**: `docker-compose exec db psql -U postgres -d youtube_mailing`

---

**🎉 설정이 완료되었습니다! 이제 YouTube 메일링 서비스를 사용할 수 있습니다.**
