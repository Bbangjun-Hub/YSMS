import os
import logging
import pytz
from datetime import datetime, timedelta
from typing import Dict, List
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Subscription, EmailLog

# OpenAI 설정
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI 라이브러리가 설치되지 않았습니다.")

# YouTube 다운로더 import
try:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from youtube_download import YouTubeTranscriptDownloader
    YOUTUBE_DOWNLOADER_AVAILABLE = True
except ImportError:
    YOUTUBE_DOWNLOADER_AVAILABLE = False
    logging.warning("YouTube 다운로더가 설치되지 않았습니다.")

logger = logging.getLogger(__name__)


class YouTubeMailService:
    """YouTube 채널 콘텐츠 요약 및 이메일 발송 서비스"""
    
    def __init__(self):
        self.downloader = None
        self.openai_client = None
        self._initialize_services()
    
    def _initialize_services(self):
        """서비스 초기화"""
        # YouTube 다운로더 초기화
        if YOUTUBE_DOWNLOADER_AVAILABLE:
            try:
                self.downloader = YouTubeTranscriptDownloader()
                credentials_path = os.path.join(
                    settings.BASE_DIR, 'credentials.json'
                )
                if os.path.exists(credentials_path):
                    try:
                        self.downloader.authenticate(credentials_path)
                        logger.info("YouTube 다운로더 초기화 완료")
                    except Exception as auth_error:
                        logger.warning(f"YouTube API 인증 실패: {str(auth_error)}")
                        logger.info("인증 없이 웹 스크래핑 모드로 작동합니다.")
                        # 인증 실패해도 다운로더 객체는 유지 (웹 스크래핑 기능 사용)
                else:
                    logger.warning("credentials.json 파일을 찾을 수 없습니다.")
                    logger.info("인증 없이 웹 스크래핑 모드로 작동합니다.")
            except Exception as e:
                logger.error(f"YouTube 다운로더 초기화 실패: {str(e)}")
                # 다운로더 객체라도 생성해서 웹 스크래핑은 가능하도록
                self.downloader = YouTubeTranscriptDownloader()
        
        # OpenAI 초기화
        if OPENAI_AVAILABLE:
            try:
                api_key = getattr(settings, 'OPENAI_API_KEY', '')
                if api_key:
                    self.openai_client = OpenAI(api_key=api_key)
                    logger.info("OpenAI 클라이언트 초기화 완료")
                else:
                    logger.error("OPENAI_API_KEY가 설정되지 않았습니다.")
            except Exception as e:
                logger.error(f"OpenAI 초기화 실패: {str(e)}")
    
    def get_video_transcripts(self, subscriptions: List[Subscription]) -> Dict:
        """구독 정보에서 YouTube 자막 가져오기"""
        if not self.downloader:
            logger.error("YouTube 다운로더가 초기화되지 않았습니다.")
            return {}
        
        # 채널 ID 수집
        channel_ids = []
        for subscription in subscriptions:
            channel_url = subscription.youtube_channel_url
            if channel_url:
                # URL에서 채널 ID 추출 또는 채널명으로 검색
                channel_id = self.downloader.get_channel_id_by_name(
                    channel_url
                )
                if channel_id:
                    channel_ids.append(channel_id)
        
        if not channel_ids:
            logger.warning("유효한 채널 ID를 찾을 수 없습니다.")
            return {}
        
        # YouTube API가 인증되지 않은 경우 빈 결과 반환
        if not self.downloader.youtube:
            logger.warning("YouTube API 인증이 되지 않아 자막 수집을 건너뜁니다.")
            return {}
        
        # 자막 수집
        try:
            transcripts = self.downloader.get_channel_transcripts(channel_ids)
            logger.info(f"{len(transcripts)}개 채널의 자막을 수집했습니다.")
            return transcripts
        except Exception as e:
            logger.error(f"자막 수집 중 오류: {str(e)}")
            return {}
    
    def summarize_content(self, video_transcripts: Dict) -> str:
        """OpenAI를 사용하여 자막 내용 정리"""
        if not self.openai_client:
            logger.error("OpenAI 클라이언트가 초기화되지 않았습니다.")
            return self._create_simple_summary(video_transcripts)
        
        if not video_transcripts:
            return ""
        
        summaries = []
        for channel_name, videos in video_transcripts.items():
            channel_summary = f"""
            <div class="channel-section">
                <h2 class="channel-title">{channel_name}</h2>
            """
            
            for video in videos:
                prompt = f"""
                다음 유튜브 영상의 자막을 분석하고 정리해주세요.
                이때 영상의 제목과 자막 내용을 참고하여 영상의 내용을 요약해주세요.
                논점 세부 내용은 각각 최소 3문장 이상으로 자세하게 작성해주세요.
                제목: {video['title']}
                내용: {video['transcript']}
                
                다음 HTML 형식으로 작성해주세요:
                <div class="video-card">
                    <h3 class="video-title">{video['title']}</h3>
                    <div class="video-content">
                        <div class="content-block">
                            <h4>영상 개요</h4>
                            <p>[전체적인 내용 한 문장으로]</p>
                        </div>
                        
                        <div class="content-block">
                            <h4>주요 논점</h4>
                            <ul class="key-points">
                                <li>[핵심 논점 1]</li>
                                <li>[핵심 논점 2]</li>
                                <li>[핵심 논점 3]</li>
                            </ul>
                        </div>
                        
                        <div class="content-block">
                            <h4>논점 세부사항</h4>
                            <ul class="details">
                                <li>[논점 세부내용 1]</li>
                                <li>[논점 세부내용 2]</li>
                                <li>[논점 세부내용 3]</li>
                            </ul>
                        </div>
                        
                        <div class="content-block">
                            <h4>총평 및 시사점</h4>
                            <p>[내용에 대한 총평 및 시사점]</p>
                        </div>
                    </div>
                    <div class="video-link">
                        <a href="{video['url']}" target="_blank">영상 보기</a>
                    </div>
                </div>
                """
                
                try:
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "당신은 유튜브 영상 내용을 분석하고 요약하는 전문가입니다. 주어진 HTML 형식을 정확히 따라 작성해주세요. 단, ```html``` 태그는 사용하지 않습니다."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=4096,
                        temperature=0.3
                    )
                    
                    summary = response.choices[0].message.content
                    channel_summary += summary
                    
                except Exception as e:
                    logger.error(f"OpenAI API 호출 실패: {str(e)}")
                    # 실패 시 간단한 요약 생성
                    channel_summary += f"""
                    <div class="video-card">
                        <h3 class="video-title">{video['title']}</h3>
                        <div class="video-content">
                            <p>자막 내용을 요약할 수 없습니다. 원본 영상을 확인해주세요.</p>
                        </div>
                        <div class="video-link">
                            <a href="{video['url']}" target="_blank">영상 보기</a>
                        </div>
                    </div>
                    """
            
            channel_summary += "</div>"
            summaries.append(channel_summary)
        
        return '\n'.join(summaries)
    
    def _create_simple_summary(self, video_transcripts: Dict) -> str:
        """OpenAI 없이 간단한 요약 생성"""
        if not video_transcripts:
            return ""
        
        summaries = []
        for channel_name, videos in video_transcripts.items():
            channel_summary = f"""
            <div class="channel-section">
                <h2 class="channel-title">{channel_name}</h2>
            """
            
            for video in videos:
                # 자막의 첫 200자만 미리보기로 사용
                preview = video['transcript'][:200] + "..." if len(
                    video['transcript']
                ) > 200 else video['transcript']
                
                channel_summary += f"""
                <div class="video-card">
                    <h3 class="video-title">{video['title']}</h3>
                    <div class="video-content">
                        <div class="content-block">
                            <h4>영상 미리보기</h4>
                            <p>{preview}</p>
                        </div>
                    </div>
                    <div class="video-link">
                        <a href="{video['url']}" target="_blank">영상 보기</a>
                    </div>
                </div>
                """
            
            channel_summary += "</div>"
            summaries.append(channel_summary)
        
        css_styles = self._get_email_css()
        return css_styles + "\n".join(summaries)
    
    def _get_email_css(self) -> str:
        """이메일용 CSS 스타일 반환"""
        return """
        <style>
            .channel-section {
                margin: 20px 0;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
            
            .channel-title {
                color: #d04a02;
                border-bottom: 2px solid #d04a02;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            
            .video-card {
                margin: 15px 0;
                padding: 15px;
                background-color: white;
                border-left: 4px solid #d04a02;
                border-radius: 4px;
            }
            
            .video-title {
                color: #2d2d2d;
                margin-bottom: 15px;
            }
            
            .video-content {
                margin: 10px 0;
            }
            
            .content-block {
                margin: 15px 0;
            }
            
            .content-block h4 {
                color: #d04a02;
                margin-bottom: 10px;
            }
            
            .content-block p,
            .content-block ul {
                color: #2d2d2d;
                margin: 8px 0;
            }
            
            .content-block ul {
                padding-left: 20px;
            }
            
            .content-block li {
                margin: 5px 0;
            }
            
            .video-link {
                margin-top: 15px;
            }
            
            .video-link a {
                color: #d04a02;
                text-decoration: none;
                padding: 8px 0;
                display: inline-block;
            }
            
            @media screen and (max-width: 600px) {
                .channel-section {
                    padding: 15px;
                    margin: 15px 0;
                }
                
                .video-card {
                    padding: 12px;
                    margin: 12px 0;
                }
                
                .video-title {
                    font-size: 1.2em;
                }
                
                .content-block h4 {
                    font-size: 1.1em;
                }
                
                .content-block ul {
                    padding-left: 15px;
                }
                
                .content-block p,
                .content-block li {
                    font-size: 0.95em;
                }
            }
        </style>
        """
    
    def send_summary_emails(self, subscriptions: List[Subscription], 
                           summarized_content: str) -> bool:
        """요약된 콘텐츠를 이메일로 발송"""
        kst = pytz.timezone('Asia/Seoul')
        current_date = datetime.now(kst).strftime('%Y-%m-%d')
        
        success_count = 0
        total_count = len(subscriptions)
        
        # Gmail API 서비스 초기화
        gmail_service = None
        try:
            from auth_manager import GoogleAuthManager
            gmail_service = GoogleAuthManager.get_service(
                service_type='gmail',
                credentials_path=os.path.join(
                    settings.BASE_DIR, 'credentials.json'
                ),
                api_name='gmail',
                api_version='v1'
            )
            logger.info("Gmail API 서비스 초기화 성공")
        except Exception as e:
            logger.error(f"Gmail API 초기화 실패: {str(e)}")
            # Gmail API 실패 시 Django 기본 이메일 백엔드 사용
            gmail_service = None
        
        for subscription in subscriptions:
            try:
                # 이메일 제목
                subject = f'YouTube 채널 요약 - {current_date}'
                
                # 콘텐츠가 없는 경우
                if not summarized_content.strip():
                    html_content = self._create_no_content_email(
                        subscription, current_date
                    )
                else:
                    html_content = self._create_summary_email(
                        subscription, current_date, summarized_content
                    )
                
                # Gmail API 사용 시도
                if gmail_service:
                    success = self._send_email_via_gmail_api(
                        gmail_service, subscription.email, subject, html_content
                    )
                    if success:
                        success_count += 1
                        logger.info(f"Gmail API로 이메일 발송 성공: {subscription.email}")
                    else:
                        logger.error(f"Gmail API로 이메일 발송 실패: {subscription.email}")
                else:
                    # Django 기본 이메일 백엔드 사용
                    send_mail(
                        subject=subject,
                        message='',  # HTML 이메일이므로 텍스트 메시지는 비움
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[subscription.email],
                        html_message=html_content,
                        fail_silently=False,
                    )
                    success_count += 1
                    logger.info(f"Django 이메일로 발송 성공: {subscription.email}")
                
                # 이메일 로그 저장
                EmailLog.objects.create(
                    subscription=subscription,
                    subject=subject,
                    content=html_content[:1000],  # 내용 일부만 저장
                    is_successful=True
                )
                
            except Exception as e:
                logger.error(f"이메일 발송 실패 ({subscription.email}): {str(e)}")
                
                # 실패 로그 저장
                EmailLog.objects.create(
                    subscription=subscription,
                    subject=subject if 'subject' in locals() else '',
                    content="",
                    is_successful=False,
                    error_message=str(e)
                )
        
        logger.info(f"이메일 발송 완료: {success_count}/{total_count}")
        return success_count == total_count
    
    def _send_email_via_gmail_api(self, gmail_service, to_email, subject, html_content):
        """Gmail API를 사용하여 이메일 발송"""
        try:
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # 이메일 메시지 생성
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, 'html', 'utf-8')
            message.attach(html_part)
            
            # 메시지를 base64로 인코딩
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Gmail API로 전송
            send_result = gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Gmail API 전송 결과: {send_result.get('id', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail API 이메일 발송 실패: {str(e)}")
            return False
    
    def _create_summary_email(self, subscription: Subscription, 
                             current_date: str, content: str) -> str:
        """요약 콘텐츠가 있는 이메일 생성"""
        return f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                {self._get_email_css()}
            </head>
            <body>
                <div class="date-info" style="color: #666666; text-align: right; margin-bottom: 20px;">
                    발송일: {current_date}
                </div>
                
                <div class="email-header" style="background-color: white; padding: 30px; border-bottom: 3px solid #d04a02; margin-bottom: 30px; text-align: center;">
                    <h1 style="margin: 0; color: #2d2d2d;">{subscription.name}님을 위한 오늘의 YouTube 콘텐츠 요약</h1>
                    <p style="margin: 10px 0 0 0; color: #666666;">구독하신 채널의 최신 콘텐츠를 AI가 요약했습니다</p>
                </div>

                <div class="content-section" style="margin: 20px 0;">
                    {content}
                </div>
                
                <div class="email-footer" style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-top: 3px solid #d04a02; text-align: center;">
                    <p style="color: #2d2d2d; margin: 5px 0;">이 메일은 자동으로 생성된 유튜브 콘텐츠 요약 서비스입니다.</p>
                    <p style="color: #2d2d2d; margin: 5px 0;">문의사항이 있으시면 답장해 주시기 바랍니다.</p>
                    <p style="color: #2d2d2d; margin: 5px 0;">감사합니다.</p>
                </div>
            </body>
        </html>
        """
    
    def _create_no_content_email(self, subscription: Subscription, 
                                current_date: str) -> str:
        """콘텐츠가 없는 경우의 이메일 생성"""
        return f"""
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                {self._get_email_css()}
            </head>
            <body>
                <div class="date-info" style="color: #666666; text-align: right; margin-bottom: 20px;">
                    발송일: {current_date}
                </div>
                
                <div class="email-header" style="background-color: white; padding: 30px; border-bottom: 3px solid #d04a02; margin-bottom: 30px; text-align: center;">
                    <h1 style="margin: 0; color: #2d2d2d;">{subscription.name}님을 위한 오늘의 YouTube 콘텐츠 요약</h1>
                    <p style="margin: 10px 0 0 0; color: #666666;">구독하신 채널의 최신 콘텐츠를 확인했습니다</p>
                </div>

                <div class="content-section" style="margin: 20px 0;">
                    <div class="no-content-message" style="text-align: center; padding: 30px; background-color: #f8f9fa; border-radius: 8px;">
                        <h2 style="color: #666666;">새로운 업데이트가 없습니다</h2>
                        <p style="color: #888888;">구독하신 채널에 어제 오전 7시 이후 업로드된 새로운 콘텐츠가 없습니다.</p>
                        <p style="color: #888888;">다음 업데이트를 기다려주세요!</p>
                    </div>
                </div>
                
                <div class="email-footer" style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-top: 3px solid #d04a02; text-align: center;">
                    <p style="color: #2d2d2d; margin: 5px 0;">이 메일은 자동으로 생성된 유튜브 콘텐츠 요약 서비스입니다.</p>
                    <p style="color: #2d2d2d; margin: 5px 0;">문의사항이 있으시면 답장해 주시기 바랍니다.</p>
                    <p style="color: #2d2d2d; margin: 5px 0;">감사합니다.</p>
                </div>
            </body>
        </html>
        """
    
    def process_daily_summaries(self) -> Dict:
        """일일 요약 처리 메인 함수"""
        logger.info("일일 YouTube 요약 처리 시작")
        
        # 활성 구독 가져오기
        active_subscriptions = Subscription.objects.filter(is_active=True)
        
        if not active_subscriptions.exists():
            logger.info("활성 구독이 없습니다.")
            return {
                'success': True,
                'message': '활성 구독이 없습니다.',
                'processed_count': 0
            }
        
        try:
            # 1. 자막 수집
            logger.info("YouTube 자막 수집 시작")
            video_transcripts = self.get_video_transcripts(
                list(active_subscriptions)
            )
            
            # 2. 콘텐츠 요약
            logger.info("콘텐츠 요약 시작")
            summarized_content = self.summarize_content(video_transcripts)
            
            # 3. 이메일 발송
            logger.info("이메일 발송 시작")
            success = self.send_summary_emails(
                list(active_subscriptions), 
                summarized_content
            )
            
            return {
                'success': success,
                'message': '일일 요약 처리 완료',
                'processed_count': len(active_subscriptions),
                'channels_found': len(video_transcripts)
            }
            
        except Exception as e:
            logger.error(f"일일 요약 처리 중 오류: {str(e)}")
            return {
                'success': False,
                'message': f'처리 중 오류 발생: {str(e)}',
                'processed_count': 0
            } 