import os
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class GoogleAuthManager:
    """Google API 인증을 관리하는 클래스"""
    
    @staticmethod
    def get_service(service_type, credentials_path, api_name, api_version,
                    scopes=None):
        """
        Google API 서비스 객체를 반환합니다.
        
        Args:
            service_type (str): 서비스 타입 ('youtube', 'gmail', 'forms')
            credentials_path (str): credentials.json 파일 경로
            api_name (str): API 이름
            api_version (str): API 버전
            scopes (list): 필요한 권한 범위 (선택사항)
        
        Returns:
            googleapiclient.discovery.Resource: API 서비스 객체
        """
        
        # 기본 스코프 설정
        default_scopes = {
            'youtube': ['https://www.googleapis.com/auth/youtube.readonly'],
            'gmail': [
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.compose',
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.labels'
            ],
            'forms': [
                'https://www.googleapis.com/auth/forms.body.readonly',
                'https://www.googleapis.com/auth/forms.responses.readonly'
            ]
        }
        
        if scopes is None:
            scopes = default_scopes.get(service_type, [])
        
        # 토큰 파일 경로 - 설정에 맞춰 token.json 사용
        base_dir = os.path.dirname(credentials_path)
        token_path = os.path.join(base_dir, 'token.json')
        
        creds = None
        
        # 기존 토큰 파일이 있는지 확인
        if os.path.exists(token_path) and os.path.getsize(token_path) > 0:
            try:
                logger.info(f"기존 토큰 파일 로드 시도: {token_path}")
                creds = Credentials.from_authorized_user_file(
                    token_path, scopes)
                logger.info("토큰 파일 로드 성공")
            except Exception as e:
                logger.warning(f"토큰 로드 실패: {str(e)}")
                creds = None
        else:
            logger.warning(f"토큰 파일이 없거나 비어있음: {token_path}")
        
        # 토큰이 유효하지 않거나 없는 경우
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("만료된 토큰 갱신 시도")
                    creds.refresh(Request())
                    logger.info("토큰 갱신 성공")
                    
                    # 갱신된 토큰 저장
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("갱신된 토큰 저장 완료")
                    
                except Exception as e:
                    logger.error(f"토큰 갱신 실패: {str(e)}")
                    creds = None
            
            # 새로운 인증이 필요한 경우 - Docker 환경에서는 실행하지 않음
            if not creds:
                if os.path.exists('/.dockerenv'):
                    # Docker 환경에서는 브라우저 인증 불가
                    logger.error("Docker 환경에서는 새로운 인증을 수행할 수 없습니다.")
                    logger.error("로컬에서 token.json 파일을 생성한 후 Docker 컨테이너에 복사하세요.")
                    raise Exception("Docker 환경에서 브라우저 인증 불가")
                else:
                    # 로컬 환경에서만 브라우저 인증 수행
                    logger.info("새로운 인증 수행")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_path, scopes)
                    creds = flow.run_local_server(port=0)
                    
                    # 토큰 저장
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    logger.info("새 토큰 저장 완료")
        
        # API 서비스 객체 생성
        service = build(api_name, api_version, credentials=creds)
        logger.info(f"{service_type} API 서비스 객체 생성 완료")
        return service