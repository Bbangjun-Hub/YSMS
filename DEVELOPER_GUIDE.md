# YouTube 메일링 서비스 개발자 가이드

## 🏗️ 프로젝트 개요

YouTube 메일링 서비스는 React 프론트엔드와 Django 백엔드로 구성된 풀스택 웹 애플리케이션입니다. 사용자가 YouTube 채널을 구독하고 새로운 영상 업로드 시 AI 요약과 함께 이메일 알림을 받을 수 있는 서비스입니다.

## 🛠️ 기술 스택

### Frontend

- **React 18**: 사용자 인터페이스
- **Material-UI (MUI)**: UI 컴포넌트 라이브러리
- **React Router**: 클라이언트 사이드 라우팅
- **Axios**: HTTP 클라이언트

### Backend

- **Django 4.2**: 웹 프레임워크
- **Django REST Framework**: API 개발
- **PostgreSQL**: 데이터베이스
- **Celery**: 비동기 작업 처리
- **Redis**: 메시지 브로커 및 캐시

### External APIs

- **YouTube Data API v3**: 채널 정보 및 영상 데이터
- **YouTube Transcript API**: 영상 자막 추출
- **OpenAI API**: AI 기반 영상 요약
- **Gmail API**: 이메일 발송

### Infrastructure

- **Docker & Docker Compose**: 컨테이너화
- **Nginx**: 리버스 프록시 (프로덕션)

## 📁 프로젝트 구조

```
Youtube Mailing/
├── frontend/                 # React 프론트엔드
│   ├── public/
│   │   ├── components/       # React 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── App.js           # 메인 앱 컴포넌트
│   │   └── index.js         # 엔트리 포인트
│   ├── package.json
│   └── Dockerfile
├── backend/                  # Django 백엔드
│   ├── youtube_mail_project/ # Django 프로젝트 설정
│   │   ├── settings.py      # Django 설정
│   │   ├── urls.py          # URL 라우팅
│   │   └── celery.py        # Celery 설정
│   ├── subscriptions/        # 메인 앱
│   │   ├── models.py        # 데이터 모델
│   │   ├── views.py         # API 뷰
│   │   ├── serializers.py   # DRF 시리얼라이저
│   │   ├── tasks.py         # Celery 태스크
│   │   └── youtube_mail_service.py # 핵심 비즈니스 로직
│   ├── auth_manager.py      # Google OAuth 관리
│   ├── youtube_download.py  # YouTube 데이터 처리
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml       # Docker Compose 설정
├── USER_GUIDE.md           # 사용자 가이드
├── DEVELOPER_GUIDE.md      # 개발자 가이드 (이 파일)
└── README.md               # 프로젝트 개요
```

## 🚀 개발 환경 설정

### 1. 필수 요구사항

- Docker & Docker Compose
- Node.js 18+ (로컬 개발 시)
- Python 3.11+ (로컬 개발 시)

### 2. 환경 변수 설정

#### 백엔드 환경 변수 (.env)

```bash
# Django 설정
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 데이터베이스
DB_NAME=youtube_mail_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_URL=redis://redis:6379/0

# YouTube API
YOUTUBE_API_KEY=your-youtube-api-key

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Gmail API
GMAIL_CREDENTIALS_PATH=/app/credentials.json
GMAIL_TOKEN_PATH=/app/token.json

# 이메일 설정
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 3. Google API 설정

#### YouTube Data API

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. YouTube Data API v3 활성화
4. API 키 생성 및 `YOUTUBE_API_KEY`에 설정

#### Gmail API

1. Google Cloud Console에서 Gmail API 활성화
2. OAuth 2.0 클라이언트 ID 생성
3. `credentials.json` 파일 다운로드
4. 백엔드 루트 디렉토리에 배치

### 4. 프로젝트 실행

#### Docker Compose 사용 (권장)

```bash
# 전체 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그 확인
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

#### 로컬 개발 환경

```bash
# 백엔드
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# 프론트엔드 (새 터미널)
cd frontend
npm install
npm start

# Celery Worker (새 터미널)
cd backend
celery -A youtube_mail_project worker --loglevel=info

# Celery Beat (새 터미널)
cd backend
celery -A youtube_mail_project beat --loglevel=info
```

## 🔧 핵심 컴포넌트

### 1. 데이터 모델

#### Subscription 모델

```python
class Subscription(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # 해시화됨
    youtube_channel_url = models.URLField()
    channel_name = models.CharField(max_length=100)
    notification_time = models.TimeField()  # 30분 단위
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### EmailLog 모델

```python
class EmailLog(models.Model):
    subscription = models.ForeignKey(Subscription)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
```

### 2. Celery 태스크

#### 이메일 준비 태스크 (10분 전 실행)

```python
@shared_task
def prepare_scheduled_emails():
    """10분 후 발송될 이메일들을 미리 준비"""
    # 1. 10분 후 시간을 30분 단위로 반올림
    # 2. 해당 시간에 발송할 구독들 조회
    # 3. YouTube 자막 수집 (시간 소요)
    # 4. OpenAI로 콘텐츠 요약
    # 5. 캐시에 저장
```

#### 이메일 발송 태스크 (정시 실행)

```python
@shared_task
def send_scheduled_emails():
    """정시에 이메일을 발송"""
    # 1. 현재 시간이 30분 단위인지 확인
    # 2. 캐시에서 준비된 콘텐츠 조회
    # 3. Gmail API로 이메일 발송
    # 4. 발송 로그 기록
```

### 3. YouTube 데이터 처리

#### 채널 ID 추출

```python
def get_channel_id_by_name(self, channel_name: str) -> str:
    """다양한 YouTube URL 형식에서 채널 ID 추출"""
    # 1. 직접 채널 ID (UC...)
    # 2. 핸들 형식 (@username) - 웹 스크래핑
    # 3. 사용자명 - YouTube API
    # 4. 검색 API (할당량 소비 많음)
```

#### 영상 필터링

```python
def get_latest_videos(self, channel_id):
    """전날 업로드된 적절한 영상들 조회"""
    # 필터링 조건:
    # - 전날 오전 7시 ~ 당일 오전 7시 업로드
    # - 60초 초과 (쇼츠 제외)
    # - 1시간 이하
    # - 스트리밍 제외
```

### 4. AI 요약 시스템

#### OpenAI 통합

```python
def summarize_content(self, video_transcripts):
    """영상 자막을 AI로 요약"""
    # 1. 자막 텍스트 전처리
    # 2. OpenAI API 호출
    # 3. 구조화된 요약 생성
    # 4. 이메일 템플릿에 맞게 포맷팅
```

## 📊 스케줄링 시스템

### Celery Beat 스케줄

```python
app.conf.beat_schedule = {
    'prepare-emails-10min-before': {
        'task': 'subscriptions.tasks.prepare_scheduled_emails',
        'schedule': 60.0,  # 매분 실행하여 10분 전 체크
    },
    'send-scheduled-emails': {
        'task': 'subscriptions.tasks.send_scheduled_emails',
        'schedule': 60.0,  # 매분 실행하되 30분 단위만 처리
    },
    'cleanup-old-cache': {
        'task': 'subscriptions.tasks.cleanup_old_cache',
        'schedule': crontab(hour=2, minute=0),  # 매일 새벽 2시
    },
}
```

### 시간 반올림 로직

```python
def round_to_30min(target_time):
    """시간을 30분 단위로 반올림"""
    if target_minute < 15:
        rounded_minute = 0
    elif target_minute < 45:
        rounded_minute = 30
    else:
        rounded_minute = 0
        target_hour = (target_hour + 1) % 24
    return time(target_hour, rounded_minute, 0)
```

## 🔒 보안 고려사항

### 1. 비밀번호 보안

- Django의 `make_password()` 사용하여 해시화
- 평문 비밀번호는 저장하지 않음
- 최소 6자 이상 요구

### 2. API 보안

- CORS 설정으로 허용된 도메인만 접근
- 환경 변수로 민감한 정보 관리
- API 키 노출 방지

### 3. 이메일 보안

- OAuth 2.0 사용하여 Gmail API 인증
- 앱 비밀번호 대신 OAuth 토큰 사용

## 🧪 테스트

### 단위 테스트

```bash
# Django 테스트
cd backend
python manage.py test

# React 테스트
cd frontend
npm test
```

### API 테스트

```bash
# 구독 생성 테스트
curl -X POST http://localhost:8000/api/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트",
    "email": "test@example.com",
    "password": "password123",
    "youtube_channel_url": "https://www.youtube.com/@test",
    "notification_time": "09:00"
  }'
```

### Celery 태스크 테스트

```bash
# 관리자 페이지에서 테스트 이메일 발송
# 또는 Django shell에서:
python manage.py shell
>>> from subscriptions.tasks import send_test_email_task
>>> send_test_email_task.delay(subscription_id=1)
```

## 📈 모니터링 및 로깅

### 로그 확인

```bash
# 전체 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f celery-beat

# 최근 N줄만 확인
docker-compose logs --tail=50 backend
```

### 성능 모니터링

- Celery 태스크 실행 시간 모니터링
- YouTube API 할당량 사용량 추적
- 이메일 발송 성공률 모니터링

## 🚀 배포

### 프로덕션 환경 설정

1. **환경 변수 업데이트**:

   - `DEBUG=False`
   - `ALLOWED_HOSTS` 설정
   - 실제 도메인 및 SSL 인증서

2. **데이터베이스**:

   - PostgreSQL 외부 인스턴스 사용
   - 백업 및 복구 전략 수립

3. **정적 파일**:

   - Django `collectstatic` 실행
   - Nginx로 정적 파일 서빙

4. **보안**:
   - HTTPS 강제 설정
   - 방화벽 규칙 설정
   - 정기적인 보안 업데이트

### Docker 프로덕션 빌드

```bash
# 프로덕션용 이미지 빌드
docker-compose -f docker-compose.prod.yml build

# 프로덕션 환경 실행
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 문제 해결

### 일반적인 문제들

#### 1. Celery Beat가 시작되지 않음

```bash
# 로그 확인
docker-compose logs celery-beat

# 컨테이너 재시작
docker-compose restart celery-beat
```

#### 2. YouTube API 할당량 초과

- API 키 사용량 확인
- 요청 최적화 (배치 처리)
- 캐싱 활용

#### 3. 이메일 발송 실패

- Gmail API 인증 상태 확인
- 토큰 갱신 필요 여부 확인
- 스팸 정책 준수 확인

#### 4. 자막 추출 실패

- YouTube 요청 제한 확인
- 프록시 설정 검토
- 재시도 로직 확인

## 📚 추가 리소스

### API 문서

- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Gmail API](https://developers.google.com/gmail/api)
- [OpenAI API](https://platform.openai.com/docs)

### 프레임워크 문서

- [Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [React](https://react.dev/)
- [Material-UI](https://mui.com/)
- [Celery](https://docs.celeryq.dev/)

### 개발 도구

- [Docker](https://docs.docker.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Redis](https://redis.io/documentation)

---

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

---

**Happy Coding!** 🎉
