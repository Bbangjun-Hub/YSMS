#!/usr/bin/env python3
"""
Google OAuth 토큰 생성 스크립트

이 스크립트를 로컬에서 실행하여 브라우저를 통해 Google OAuth 인증을 수행하고
token.json 파일을 생성합니다.

사용법:
    python generate_token.py

필요한 파일:
    - credentials.json (Google Cloud Console에서 다운로드한 OAuth 2.0 클라이언트 ID)

생성되는 파일:
    - token.json (YouTube API 및 Gmail API 접근을 위한 토큰)
"""

import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def generate_token():
    """Google OAuth 토큰을 생성합니다."""
    
    # 필요한 권한 범위 설정
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.readonly',  # YouTube 읽기
        'https://www.googleapis.com/auth/gmail.send',        # Gmail 발송
        'https://www.googleapis.com/auth/gmail.compose',     # Gmail 작성
        'https://www.googleapis.com/auth/gmail.readonly',    # Gmail 읽기
        'https://www.googleapis.com/auth/gmail.labels'       # Gmail 라벨
    ]
    
    # 파일 경로 설정
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    
    # credentials.json 파일 확인
    if not os.path.exists(credentials_file):
        print(f"❌ {credentials_file} 파일을 찾을 수 없습니다.")
        print("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고")
        print("credentials.json 파일을 다운로드하여 이 스크립트와 같은 폴더에 저장하세요.")
        print("\n참고: https://console.cloud.google.com/apis/credentials")
        return False
    
    creds = None
    
    # 기존 토큰 파일이 있는지 확인
    if os.path.exists(token_file):
        print(f"📄 기존 {token_file} 파일을 발견했습니다.")
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            print("✅ 기존 토큰을 로드했습니다.")
        except Exception as e:
            print(f"⚠️  기존 토큰 로드 실패: {e}")
            creds = None
    
    # 토큰이 유효하지 않거나 없는 경우
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 만료된 토큰을 갱신하는 중...")
                creds.refresh(Request())
                print("✅ 토큰 갱신 완료!")
            except Exception as e:
                print(f"❌ 토큰 갱신 실패: {e}")
                creds = None
        
        # 새로운 인증이 필요한 경우
        if not creds:
            print("🌐 브라우저를 통한 새로운 인증을 시작합니다...")
            print("브라우저가 자동으로 열리고 Google 로그인 페이지가 표시됩니다.")
            print("다음 권한을 허용해주세요:")
            print("  - YouTube 데이터 읽기")
            print("  - Gmail 이메일 발송")
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                print("✅ 인증 완료!")
            except Exception as e:
                print(f"❌ 인증 실패: {e}")
                return False
    
    # 토큰 저장
    try:
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 토큰이 {token_file} 파일에 저장되었습니다.")
        
        # 파일 권한 확인
        file_size = os.path.getsize(token_file)
        print(f"📊 파일 크기: {file_size} bytes")
        
        if file_size > 0:
            print("✅ 토큰 생성이 완료되었습니다!")
            print("\n다음 단계:")
            print("1. Docker 컨테이너를 시작하세요: docker-compose up -d")
            print("2. 애플리케이션이 자동으로 이 토큰을 사용합니다.")
            print("3. 토큰은 필요시 자동으로 갱신됩니다.")
            return True
        else:
            print("❌ 토큰 파일이 비어있습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 토큰 저장 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("🔐 Google OAuth 토큰 생성기")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f"📁 현재 디렉토리: {current_dir}")
    
    # 토큰 생성 실행
    success = generate_token()
    
    if success:
        print("\n🎉 모든 작업이 완료되었습니다!")
        sys.exit(0)
    else:
        print("\n💥 토큰 생성에 실패했습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main() 