from celery import shared_task
from django.conf import settings
from .models import Subscription, EmailLog
from .youtube_mail_service import YouTubeMailService
from openai import OpenAI
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import os
import pytz
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Gmail API 범위 설정
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/forms.responses.readonly'
]


@shared_task
def prepare_scheduled_emails():
    """10분 후 발송될 이메일들을 미리 준비하는 태스크 (30분 단위 시간 대응)"""
    try:
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        
        # 10분 후 시간 계산
        target_time = (current_time + timedelta(minutes=10)).time()
        
        # 30분 단위로 설정된 알림 시간 중 10분 후에 해당하는 구독들 조회
        # 예: 현재 16:50 -> 10분 후 17:00 -> 17:00 또는 17:30에 설정된 구독 찾기
        target_hour = target_time.hour
        target_minute = target_time.minute
        
        # 30분 단위로 반올림 (0분 또는 30분)
        if target_minute < 15:
            rounded_minute = 0
        elif target_minute < 45:
            rounded_minute = 30
        else:
            # 45분 이상이면 다음 시간의 0분
            rounded_minute = 0
            target_hour = (target_hour + 1) % 24
        
        # 정확한 30분 단위 시간으로 변환
        from datetime import time
        rounded_target_time = time(target_hour, rounded_minute, 0)
        
        # 해당 시간에 발송해야 할 구독들 조회
        subscriptions = Subscription.objects.filter(
            is_active=True,
            notification_time=rounded_target_time
        )
        
        logger.info(f"현재 시간: {current_time.strftime('%H:%M')}")
        logger.info(f"10분 후: {target_time.strftime('%H:%M')}")
        logger.info(f"반올림된 타겟 시간: {rounded_target_time.strftime('%H:%M')}")
        logger.info(f"발송 예정 구독 수: {subscriptions.count()}")
        
        if not subscriptions.exists():
            logger.info(f"10분 후({rounded_target_time}) 발송할 구독이 없습니다.")
            return {
                'success': True,
                'message': f'10분 후({rounded_target_time}) 발송할 구독이 없습니다.',
                'target_time': rounded_target_time.strftime('%H:%M'),
                'subscription_count': 0
            }
        
        logger.info(
            f"10분 후({rounded_target_time}) 발송 예정인 {subscriptions.count()}개 "
            f"구독에 대한 준비 작업 시작"
        )
        
        # YouTube 메일 서비스 초기화
        mail_service = YouTubeMailService()
        
        # 자막 수집 (시간이 오래 걸리는 작업)
        logger.info("YouTube 자막 수집 시작...")
        video_transcripts = mail_service.get_video_transcripts(
            list(subscriptions)
        )
        
        # 콘텐츠 요약 (OpenAI API 호출)
        logger.info("콘텐츠 요약 시작...")
        summarized_content = mail_service.summarize_content(video_transcripts)
        
        # 준비된 콘텐츠를 캐시에 저장 (더미 캐시 대응)
        try:
            from django.core.cache import cache
            cache_key = f"prepared_content_{rounded_target_time.strftime('%H_%M')}"
            cache_data = {
                'content': summarized_content,
                'subscriptions': [sub.id for sub in subscriptions],
                'prepared_at': current_time.isoformat()
            }
            cache.set(cache_key, cache_data, timeout=3600)  # 1시간 후 만료
            logger.info(f"콘텐츠 준비 완료. 캐시 키: {cache_key}")
        except Exception as cache_error:
            logger.warning(f"캐시 저장 실패 (더미 캐시 사용 중): {str(cache_error)}")
        
        return {
            'success': True,
            'message': f'{subscriptions.count()}개 구독에 대한 콘텐츠 준비 완료',
            'target_time': rounded_target_time.strftime('%H:%M'),
            'cache_key': cache_key,
            'subscription_count': subscriptions.count(),
            'channels_found': len(video_transcripts)
        }
        
    except Exception as e:
        logger.error(f"이메일 준비 작업 실패: {str(e)}")
        return {
            'success': False,
            'message': f'준비 작업 실패: {str(e)}'
        }


@shared_task
def send_scheduled_emails():
    """정시에 이메일을 발송하는 태스크 (30분 단위 시간 대응)"""
    try:
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        current_time_str = current_time.time()
        
        # 30분 단위로 설정된 알림 시간과 정확히 일치하는 구독들만 조회
        # 예: 17:00:xx 또는 17:30:xx
        current_hour = current_time_str.hour
        current_minute = current_time_str.minute
        
        # 30분 단위 시간인지 확인 (0분 또는 30분)
        if current_minute == 0 or current_minute == 30:
            # 정확한 30분 단위 시간으로 변환
            from datetime import time
            exact_time = time(current_hour, current_minute, 0)
            
            # 해당 시간에 발송해야 할 구독들 조회
            subscriptions = Subscription.objects.filter(
                is_active=True,
                notification_time=exact_time
            )
        else:
            # 30분 단위가 아닌 시간에는 발송하지 않음
            subscriptions = Subscription.objects.none()
            exact_time = current_time_str
        
        logger.info(f"현재 시간: {current_time.strftime('%H:%M')}")
        logger.info(f"정확한 발송 시간: {exact_time.strftime('%H:%M')}")
        logger.info(f"발송 예정 구독 수: {subscriptions.count()}")
        
        if not subscriptions.exists():
            logger.info(f"현재 시간({exact_time}) 발송할 구독이 없습니다.")
            return {
                'success': True,
                'message': f'현재 시간({exact_time}) 발송할 구독이 없습니다.',
                'sent_time': exact_time.strftime('%H:%M'),
                'subscription_count': 0
            }
        
        logger.info(
            f"현재 시간({exact_time}) 발송 예정인 {subscriptions.count()}개 "
            f"구독에 대한 이메일 발송 시작"
        )
        
        # 캐시에서 준비된 콘텐츠 확인 (더미 캐시 대응)
        summarized_content = None
        cached_data = None
        
        try:
            from django.core.cache import cache
            cache_key = f"prepared_content_{exact_time.strftime('%H_%M')}"
            cached_data = cache.get(cache_key)
            
            if cached_data:
                logger.info(f"캐시된 콘텐츠 발견: {cache_key}")
                summarized_content = cached_data['content']
                
                # 캐시된 구독 ID와 현재 구독 ID가 일치하는지 확인
                cached_subscription_ids = set(cached_data['subscriptions'])
                current_subscription_ids = set(sub.id for sub in subscriptions)
                
                if cached_subscription_ids == current_subscription_ids:
                    logger.info("캐시된 콘텐츠를 사용하여 이메일 발송")
                else:
                    logger.warning("구독 정보가 변경되어 실시간으로 콘텐츠 생성")
                    summarized_content = None
            else:
                logger.warning("캐시된 콘텐츠가 없어 실시간으로 콘텐츠 생성")
        except Exception as cache_error:
            logger.warning(f"캐시 조회 실패 (더미 캐시 사용 중): {str(cache_error)}")
        
        # 캐시된 콘텐츠가 없으면 실시간 생성
        if summarized_content is None:
            mail_service = YouTubeMailService()
            video_transcripts = mail_service.get_video_transcripts(
                list(subscriptions)
            )
            summarized_content = mail_service.summarize_content(
                video_transcripts
            )
        
        # 이메일 발송
        mail_service = YouTubeMailService()
        success = mail_service.send_summary_emails(
            list(subscriptions), 
            summarized_content
        )
        
        # 캐시 정리 (더미 캐시 대응)
        try:
            if cached_data:
                cache.delete(cache_key)
        except Exception as cache_error:
            logger.warning(f"캐시 삭제 실패 (더미 캐시 사용 중): {str(cache_error)}")
        
        return {
            'success': success,
            'message': f'{subscriptions.count()}개 구독에 대한 이메일 발송 완료',
            'sent_time': exact_time.strftime('%H:%M'),
            'used_cache': cached_data is not None,
            'subscription_count': subscriptions.count()
        }
        
    except Exception as e:
        logger.error(f"이메일 발송 실패: {str(e)}")
        return {
            'success': False,
            'message': f'이메일 발송 실패: {str(e)}'
        }


@shared_task
def send_test_email_task(subscription_id):
    """테스트 이메일 발송을 위한 별칭 함수"""
    return test_email_task(subscription_id)


@shared_task
def test_email_task(subscription_id):
    """테스트 이메일 발송 태스크"""
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        logger.info(f"테스트 이메일 발송 시작: {subscription.email}")
        
        # YouTube 메일 서비스 사용
        mail_service = YouTubeMailService()
        
        # 자막 수집
        video_transcripts = mail_service.get_video_transcripts([subscription])
        
        # 콘텐츠 요약
        summarized_content = mail_service.summarize_content(video_transcripts)
        
        # 이메일 발송
        success = mail_service.send_summary_emails(
            [subscription], 
            summarized_content
        )
        
        if success:
            logger.info(f"테스트 이메일 발송 성공: {subscription.email}")
            return {
                'success': True,
                'message': '테스트 이메일 발송 성공',
                'email': subscription.email
            }
        else:
            logger.error(f"테스트 이메일 발송 실패: {subscription.email}")
            return {
                'success': False,
                'message': '테스트 이메일 발송 실패',
                'email': subscription.email
            }
            
    except Subscription.DoesNotExist:
        logger.error(f"구독 정보를 찾을 수 없음: {subscription_id}")
        return {
            'success': False,
            'message': '구독 정보를 찾을 수 없습니다.'
        }
    except Exception as e:
        logger.error(f"테스트 이메일 발송 중 오류: {str(e)}")
        return {
            'success': False,
            'message': f'오류 발생: {str(e)}'
        }


@shared_task
def cleanup_old_cache():
    """오래된 캐시 데이터 정리"""
    try:
        from django.core.cache import cache
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        
        # 지난 24시간의 모든 시간대에 대한 캐시 키 생성
        for hour in range(24):
            for minute in [0, 30]:  # 정시와 30분
                time_str = f"{hour:02d}_{minute:02d}"
                cache_key = f"prepared_content_{time_str}"
                
                # 캐시 데이터 확인
                cached_data = cache.get(cache_key)
                if cached_data:
                    prepared_at = datetime.fromisoformat(
                        cached_data['prepared_at']
                    )
                    
                    # 2시간 이상 된 캐시는 삭제
                    if (current_time - prepared_at).total_seconds() > 7200:
                        cache.delete(cache_key)
                        logger.info(f"오래된 캐시 삭제: {cache_key}")
        
        logger.info("캐시 정리 완료")
        return {'success': True, 'message': '캐시 정리 완료'}
        
    except Exception as e:
        logger.error(f"캐시 정리 실패: {str(e)}")
        return {'success': False, 'message': f'캐시 정리 실패: {str(e)}'}


def summarize_transcripts(transcripts):
    """자막을 요약합니다."""
    if not transcripts:
        return ""
    
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        summaries = []
        for channel_name, videos in transcripts.items():
            channel_summary = f"<h2>{channel_name}</h2>\n"
            
            for video in videos:
                prompt = f"""
                다음 유튜브 영상의 자막을 분석하고 정리해주세요.
                제목: {video['title']}
                내용: {video['transcript']}
                
                다음 형식으로 작성해주세요:
                <h3>{video['title']}</h3>
                <p>영상 개요: [전체적인 내용 한 문장으로]</p>
                <ul>
                <li>주요 논점 1</li>
                <li>주요 논점 2</li>
                <li>주요 논점 3</li>
                </ul>
                <p>총평: [내용에 대한 총평]</p>
                <a href="{video['url']}" target="_blank">영상 보기</a>
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "당신은 유튜브 영상 내용을 분석하고 요약하는 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2048,
                    temperature=0.3
                )
                
                summary = response.choices[0].message.content
                channel_summary += summary + "\n"
            
            summaries.append(channel_summary)
        
        return '\n'.join(summaries)
        
    except Exception as e:
        logger.error(f"자막 요약 실패: {str(e)}")
        return ""


def send_summary_email(subscription, content, email_log):
    """요약 이메일을 발송합니다."""
    try:
        # Gmail API 인증
        service = get_gmail_service()
        
        current_date = datetime.now(pytz.timezone('Asia/Seoul')).strftime(
            '%Y년 %m월 %d일'
        )
        
        message = MIMEMultipart()
        message['from'] = 'admin@pwc-edge.com'
        message['to'] = subscription.email
        message['subject'] = 'Edge Center Youtube Summary Letter'
        
        html_content = f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #2d2d2d;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    
                    .email-header {{
                        background-color: white;
                        padding: 30px;
                        border-bottom: 3px solid #d04a02;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    
                    .header-logo {{
                        max-width: 200px;
                        width: 80%;
                        height: auto;
                        margin-bottom: 20px;
                    }}
                    
                    .email-footer {{
                        margin-top: 30px;
                        padding: 20px;
                        background-color: #f8f9fa;
                        border-top: 3px solid #d04a02;
                        text-align: center;
                    }}
                    
                    .footer-text {{
                        color: #2d2d2d;
                        margin: 5px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="date-info">
                    발송일: {current_date}
                </div>
                
                <div class="email-header">
                    <h1>
                        {subscription.email.split('@')[0]}님을 위한 오늘의 YouTube 콘텐츠 요약
                    </h1>
                    <p>구독하신 채널의 최신 콘텐츠를 AI가 요약했습니다</p>
                </div>

                <div class="content-section">
                    {content}
                </div>
                
                <div class="email-footer">
                    <p class="footer-text">
                        이 메일은 자동으로 생성된 유튜브 콘텐츠 요약 서비스입니다.
                    </p>
                    <p class="footer-text">
                        문의사항이 있으시면 답장해 주시기 바랍니다.
                    </p>
                    <p class="footer-text">감사합니다.</p>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, 'html'))
        
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        email_log.status = 'success'
        email_log.save()
        
        logger.info(f"이메일 발송 완료: {subscription.email}")
        
    except Exception as e:
        logger.error(f"이메일 발송 실패: {str(e)}")
        email_log.status = 'failed'
        email_log.error_message = str(e)
        email_log.save()


def send_no_content_email(subscription, email_log):
    """콘텐츠가 없을 때 이메일을 발송합니다."""
    try:
        service = get_gmail_service()
        
        current_date = datetime.now(pytz.timezone('Asia/Seoul')).strftime(
            '%Y-%m-%d'
        )
        
        message = MIMEMultipart()
        message['from'] = 'admin@pwc-edge.com'
        message['to'] = subscription.email
        message['subject'] = 'Edge Center Youtube Summary Letter'
        
        html_content = f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        line-height: 1.6;
                        color: #2d2d2d;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    
                    .email-header {{
                        background-color: white;
                        padding: 30px;
                        border-bottom: 3px solid #d04a02;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    
                    .no-content-message {{
                        text-align: center;
                        padding: 30px;
                        background-color: #f8f9fa;
                        border-radius: 8px;
                    }}
                </style>
            </head>
            <body>
                <div class="date-info">
                    발송일: {current_date}
                </div>
                
                <div class="email-header">
                    <h1>
                        {subscription.email.split('@')[0]}
                    </h1>
                    <p>구독하신 채널의 최신 콘텐츠를 확인했습니다</p>
                </div>

                <div class="no-content-message">
                    <h2 style="color: #666666;">새로운 업데이트가 없습니다</h2>
                    <p style="color: #888888;">
                        구독하신 채널에 어제 오전 7시 이후 업로드된 새로운 콘텐츠가 없습니다.
                    </p>
                    <p style="color: #888888;">다음 업데이트를 기다려주세요!</p>
                </div>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_content, 'html'))
        
        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode('utf-8')
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        email_log.status = 'success'
        email_log.video_count = 0
        email_log.save()
        
        logger.info(f"빈 콘텐츠 이메일 발송 완료: {subscription.email}")
        
    except Exception as e:
        logger.error(f"빈 콘텐츠 이메일 발송 실패: {str(e)}")
        email_log.status = 'failed'
        email_log.error_message = str(e)
        email_log.save()


def get_gmail_service():
    """Gmail API 서비스 가져오기"""
    creds = None
    
    if os.path.exists(settings.YOUTUBE_API_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(
            settings.YOUTUBE_API_TOKEN_PATH, 
            SCOPES
        )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.YOUTUBE_API_CREDENTIALS_PATH, 
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        
        with open(settings.YOUTUBE_API_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds) 