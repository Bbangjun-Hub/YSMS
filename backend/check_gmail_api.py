#!/usr/bin/env python3
"""
Gmail API 상태 확인 스크립트

Google Cloud Console 설정과 Gmail API 권한을 확인합니다.
"""

import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def check_credentials_file():
    """credentials.json 파일 확인"""
    print("1. credentials.json 파일 확인")
    if os.path.exists('credentials.json'):
        try:
            with open('credentials.json', 'r') as f:
                creds_data = json.load(f)
            
            client_info = creds_data.get('installed', {})
            print(f"   ✅ 파일 존재")
            print(f"   📋 클라이언트 ID: {client_info.get('client_id', 'N/A')[:20]}...")
            print(f"   🔗 프로젝트 ID: {client_info.get('project_id', 'N/A')}")
            return True
        except Exception as e:
            print(f"   ❌ 파일 읽기 실패: {e}")
            return False
    else:
        print("   ❌ credentials.json 파일이 없습니다.")
        return False


def check_token_file():
    """token.json 파일 확인"""
    print("\n2. token.json 파일 확인")
    if os.path.exists('token.json'):
        try:
            with open('token.json', 'r') as f:
                token_data = json.load(f)
            
            print(f"   ✅ 파일 존재")
            print(f"   📅 만료 시간: {token_data.get('expiry', 'N/A')}")
            print(f"   🔑 스코프:")
            for scope in token_data.get('scopes', []):
                print(f"      - {scope}")
            return token_data
        except Exception as e:
            print(f"   ❌ 파일 읽기 실패: {e}")
            return None
    else:
        print("   ❌ token.json 파일이 없습니다.")
        return None


def test_gmail_api_access(token_data):
    """Gmail API 접근 테스트"""
    print("\n3. Gmail API 접근 테스트")
    
    try:
        # 토큰으로 credentials 생성
        creds = Credentials.from_authorized_user_info(token_data)
        
        # Gmail 서비스 빌드
        service = build('gmail', 'v1', credentials=creds)
        
        # 프로필 정보 가져오기 (가장 기본적인 테스트)
        profile = service.users().getProfile(userId='me').execute()
        print(f"   ✅ Gmail API 연결 성공")
        print(f"   📧 이메일: {profile.get('emailAddress', 'N/A')}")
        print(f"   📊 총 메시지 수: {profile.get('messagesTotal', 'N/A')}")
        
        # 라벨 목록 가져오기
        labels = service.users().labels().list(userId='me').execute()
        print(f"   📁 라벨 수: {len(labels.get('labels', []))}")
        
        return True
        
    except HttpError as e:
        print(f"   ❌ Gmail API HTTP 오류: {e}")
        if e.resp.status == 403:
            print("   💡 권한 부족 - OAuth 동의 화면에서 Gmail 스코프를 승인해야 합니다.")
        elif e.resp.status == 401:
            print("   💡 인증 실패 - 토큰을 다시 생성해야 합니다.")
        return False
        
    except Exception as e:
        print(f"   ❌ Gmail API 일반 오류: {e}")
        return False


def test_gmail_send_permission(token_data):
    """Gmail 발송 권한 테스트"""
    print("\n4. Gmail 발송 권한 테스트")
    
    try:
        creds = Credentials.from_authorized_user_info(token_data)
        service = build('gmail', 'v1', credentials=creds)
        
        # 드래프트 생성 테스트 (실제 발송하지 않음)
        import base64
        from email.mime.text import MIMEText
        
        message = MIMEText("테스트 메시지")
        message['to'] = "test@example.com"
        message['subject'] = "Gmail API 테스트"
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # 드래프트로만 생성 (실제 발송 안함)
        draft = service.users().drafts().create(
            userId='me',
            body={'message': {'raw': raw_message}}
        ).execute()
        
        # 생성한 드래프트 삭제
        service.users().drafts().delete(
            userId='me',
            id=draft['id']
        ).execute()
        
        print("   ✅ Gmail 발송 권한 확인됨")
        return True
        
    except HttpError as e:
        print(f"   ❌ Gmail 발송 권한 오류: {e}")
        if "insufficient" in str(e).lower():
            print("   💡 발송 권한 부족 - OAuth 동의 화면에서 Gmail 발송 스코프를 승인해야 합니다.")
        return False
        
    except Exception as e:
        print(f"   ❌ Gmail 발송 테스트 오류: {e}")
        return False


def provide_solutions():
    """해결 방법 제시"""
    print("\n" + "="*60)
    print("🔧 Gmail API 문제 해결 방법")
    print("="*60)
    
    print("\n1. Google Cloud Console 확인사항:")
    print("   - https://console.cloud.google.com/apis/dashboard")
    print("   - Gmail API가 활성화되어 있는지 확인")
    print("   - API 및 서비스 > 라이브러리에서 'Gmail API' 검색 후 사용 설정")
    
    print("\n2. OAuth 동의 화면 확인:")
    print("   - https://console.cloud.google.com/apis/credentials/consent")
    print("   - 스코프 섹션에서 다음 스코프들이 추가되어 있는지 확인:")
    print("     * https://www.googleapis.com/auth/gmail.send")
    print("     * https://www.googleapis.com/auth/gmail.compose")
    print("     * https://www.googleapis.com/auth/youtube.readonly")
    
    print("\n3. 새 토큰 생성:")
    print("   - python generate_token.py")
    print("   - 브라우저에서 모든 권한을 승인")
    
    print("\n4. 테스트 앱 상태 확인:")
    print("   - OAuth 동의 화면이 '테스트' 상태인 경우")
    print("   - 테스트 사용자에 Gmail 계정이 추가되어 있는지 확인")


def main():
    """메인 함수"""
    print("🔍 Gmail API 상태 진단")
    print("="*60)
    
    # 1. credentials.json 확인
    if not check_credentials_file():
        print("\n❌ credentials.json 파일 문제로 진단을 중단합니다.")
        provide_solutions()
        return
    
    # 2. token.json 확인
    token_data = check_token_file()
    if not token_data:
        print("\n❌ token.json 파일 문제로 진단을 중단합니다.")
        provide_solutions()
        return
    
    # 3. Gmail API 접근 테스트
    api_access = test_gmail_api_access(token_data)
    
    # 4. Gmail 발송 권한 테스트
    send_permission = test_gmail_send_permission(token_data)
    
    # 5. 결과 요약
    print("\n" + "="*60)
    print("📊 진단 결과 요약")
    print("="*60)
    print(f"Gmail API 접근: {'✅ 성공' if api_access else '❌ 실패'}")
    print(f"Gmail 발송 권한: {'✅ 성공' if send_permission else '❌ 실패'}")
    
    if not (api_access and send_permission):
        provide_solutions()
    else:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("Gmail API를 통한 이메일 발송이 가능합니다.")


if __name__ == "__main__":
    main() 