# Google OAuth 인증 설정 가이드

YouTube 메일링 서비스를 사용하기 위해서는 Google OAuth 인증이 필요합니다. 이 가이드를 따라 인증을 설정하세요.

## 1. Google Cloud Console 설정

### 1.1 프로젝트 생성 및 API 활성화

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 다음 API들을 활성화:
   - YouTube Data API v3
   - Gmail API

### 1.2 OAuth 2.0 클라이언트 ID 생성

1. **API 및 서비스 > 사용자 인증 정보**로 이동
2. **+ 사용자 인증 정보 만들기 > OAuth 클라이언트 ID** 클릭
3. 애플리케이션 유형: **데스크톱 애플리케이션** 선택
4. 이름: `YouTube Mailing Service` (또는 원하는 이름)
5. **만들기** 클릭
6. **JSON 다운로드** 버튼을 클릭하여 `credentials.json` 파일 다운로드

### 1.3 OAuth 동의 화면 설정

1. **API 및 서비스 > OAuth 동의 화면**으로 이동
2. 사용자 유형: **외부** 선택 (개인 사용의 경우)
3. 필수 정보 입력:
   - 앱 이름: `YouTube Mailing Service`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
4. **범위** 단계에서 다음 범위 추가:
   - `https://www.googleapis.com/auth/youtube.readonly`
   - `https://www.googleapis.com/auth/gmail.send`
   - `https://www.googleapis.com/auth/gmail.compose`

## 2. 로컬 인증 실행

### 2.1 파일 준비

1. 다운로드한 `credentials.json` 파일을 `backend/` 폴더에 복사
2. 파일 구조 확인:
   ```
   backend/
   ├── credentials.json     ← 여기에 위치
   ├── generate_token.py
   └── ...
   ```

### 2.2 필요한 패키지 설치

```bash
# backend 폴더로 이동
cd backend

# 필요한 패키지 설치
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2.3 토큰 생성 실행

```bash
# backend 폴더에서 실행
python generate_token.py
```

### 2.4 브라우저 인증

1. 스크립트 실행 시 브라우저가 자동으로 열림
2. Google 계정으로 로그인
3. 권한 요청 화면에서 **허용** 클릭
4. "인증 흐름이 완료되었습니다" 메시지 확인
5. 터미널에서 "✅ 토큰 생성이 완료되었습니다!" 메시지 확인

### 2.5 생성된 파일 확인

```bash
# token.json 파일이 생성되었는지 확인
ls -la token.json

# 파일 내용이 있는지 확인 (0 bytes가 아니어야 함)
wc -c token.json
```

## 3. Docker 실행

토큰이 성공적으로 생성되었다면 Docker 컨테이너를 시작할 수 있습니다:

```bash
# 프로젝트 루트 폴더로 이동
cd ..

# Docker 컨테이너 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
```

## 4. 문제 해결

### 4.1 "credentials.json 파일을 찾을 수 없습니다"

- `credentials.json` 파일이 `backend/` 폴더에 있는지 확인
- 파일명이 정확한지 확인 (대소문자 구분)

### 4.2 "토큰 파일이 비어있습니다"

- 인증 과정에서 오류가 발생했을 가능성
- `token.json` 파일을 삭제하고 다시 실행

### 4.3 "권한이 거부되었습니다"

- OAuth 동의 화면에서 모든 권한을 허용했는지 확인
- Google Cloud Console에서 API가 활성화되어 있는지 확인

### 4.4 Docker에서 "YouTube 인증 실패"

- `token.json` 파일이 올바르게 생성되었는지 확인
- Docker 컨테이너를 재시작: `docker-compose restart backend`

## 5. 토큰 갱신

- 토큰은 자동으로 갱신됩니다
- 문제가 발생하면 `generate_token.py`를 다시 실행하여 새 토큰 생성

## 6. 보안 주의사항

- `credentials.json`과 `token.json` 파일을 Git에 커밋하지 마세요
- 이 파일들은 개인 정보이므로 안전하게 보관하세요
- 프로덕션 환경에서는 환경 변수나 시크릿 관리 서비스 사용을 권장합니다
