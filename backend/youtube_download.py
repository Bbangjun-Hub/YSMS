from auth_manager import GoogleAuthManager
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict
import re
import os
import pickle
import logging
import pytz
from datetime import datetime, timedelta
import sys
import time
import random
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, YouTubeRequestFailed

# 로거가 이미 설정되었는지 확인
logger = logging.getLogger(__name__)
# 핸들러가 없는 경우에만 핸들러 추가
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
# 상위 로거로 메시지 전파 방지
logger.propagate = False


class YouTubeTranscriptDownloader:
    def __init__(self):
        self.youtube = None
        
    def authenticate(self, client_secrets_file: str):
        """OAuth 2.0 인증 수행"""
        try:
            self.youtube = GoogleAuthManager.get_service(
                service_type='youtube',
                credentials_path=client_secrets_file,
                api_name='youtube',
                api_version='v3'
            )
        except Exception as e:
            logger.error(f"YouTube 인증 실패: {str(e)}")
            raise
    
    def extract_channel_id(self, url: str) -> str:
        """YouTube 채널 URL에서 채널 ID 추출"""
        if 'youtube.com/channel/' in url:
            return url.split('youtube.com/channel/')[-1].split('/')[0]
        return None
    
    def parse_duration(self, duration_str):
        """ISO 8601 형식의 동영상 길이를 초 단위로 변환"""
        import re
        
        # PT1H2M10S 형식에서 시간, 분, 초를 추출
        hours = re.search(r'(\d+)H', duration_str)
        minutes = re.search(r'(\d+)M', duration_str)
        seconds = re.search(r'(\d+)S', duration_str)
        
        # 각 부분을 초로 변환
        total_seconds = 0
        if hours:
            total_seconds += int(hours.group(1)) * 3600
        if minutes:
            total_seconds += int(minutes.group(1)) * 60
        if seconds:
            total_seconds += int(seconds.group(1))
            
        return total_seconds

    def get_channel_id_by_name(self, channel_name: str, enable_search_api=False) -> str:
        """
        채널 이름으로 채널 ID 검색
        
        Args:
            channel_name (str): YouTube 채널 이름, 핸들(@username), 또는 채널 URL
            enable_search_api (bool): search API 사용 활성화 여부(기본값: False, 비활성화)
        
        Returns:
            str: 채널 ID 또는 None
        """
        try:
            # 채널 URL 형식 체크
            if channel_name.startswith('http') and ('youtube.com' in channel_name or 'youtu.be' in channel_name):
                logger.info(f"채널 URL 감지됨: {channel_name}")
                
                # 기존 채널 ID 포맷(UC...)으로 된 URL인 경우
                channel_id = self.extract_channel_id(channel_name)
                if channel_id and channel_id.startswith('UC'):
                    logger.info(f"URL에서 채널 ID 추출: {channel_id}")
                    return channel_id
                    
                # 핸들 형식(@username) URL인 경우, 웹 스크래핑으로 채널 ID 추출 시도
                if '/@' in channel_name:
                    # URL에서 핸들 추출
                    handle = channel_name.split('/@')[-1].split('/')[0].split('?')[0]
                    if handle:
                        logger.info(f"URL에서 추출한 핸들: @{handle}, 웹 스크래핑으로 채널 ID 추출 시도")
                        return self.get_channel_id_by_scraping_url(f"https://www.youtube.com/@{handle}")
            
            # 핸들(@username) 형식인 경우 웹 스크래핑 시도
            if channel_name.startswith('@'):
                handle = channel_name[1:]  # @ 기호 제거
                logger.info(f"채널 핸들 감지됨: @{handle}, 웹 스크래핑으로 채널 ID 추출 시도")
                return self.get_channel_id_by_scraping_url(f"https://www.youtube.com/@{handle}")
            
            # 일반 사용자명으로 시도 (할당량 1 사용)
            logger.info(f"forUsername으로 채널 검색 시도: {channel_name}")
            channel_response = self.youtube.channels().list(
                part="id",
                forUsername=channel_name,
                fields="items/id"
            ).execute()
            
            if channel_response.get('items'):
                channel_id = channel_response['items'][0]['id']
                logger.info(f"forUsername으로 채널 ID 발견: {channel_id}")
                return channel_id
            
            # search API 사용이 활성화된 경우 (할당량 100 사용)
            if enable_search_api:
                search_query = channel_name
                logger.warning(f"search API로 '{search_query}' 검색 중... (할당량 100 소비)")
                
                search_response = self.youtube.search().list(
                    part='snippet',
                    q=search_query,
                    type='channel',
                    maxResults=1,
                    fields="items(snippet/channelId)"
                ).execute()
                
                if search_response.get('items'):
                    channel_id = search_response['items'][0]['snippet']['channelId']
                    logger.info(f"search API로 채널 ID 발견: {channel_id}")
                    return channel_id
            
            # 모든 방법으로 찾을 수 없는 경우
            if channel_name.startswith('@'):
                logger.warning(f"핸들 '{channel_name}'를 가진 채널을 찾을 수 없습니다.")
            else:
                logger.warning(f"사용자명 '{channel_name}'을 가진 채널을 찾을 수 없습니다.")
                
            logger.warning("채널 ID를 직접 입력하거나 전체 채널 URL을 사용하세요.")
            return None
            
        except Exception as e:
            logger.error(f"채널 ID 검색 실패: {str(e)}")
            return None
            
    def get_channel_id_by_scraping_url(self, channel_url: str) -> str:
        """
        웹 스크래핑으로 채널 URL에서 채널 ID 추출 (API 할당량 소비 없음)
        
        Args:
            channel_url (str): YouTube 채널 URL (https://www.youtube.com/channel/UC... 또는 https://www.youtube.com/@username)
            
        Returns:
            str: 채널 ID 또는 None
        """
        try:
            import requests
            
            logger.info(f"웹 스크래핑으로 채널 ID 추출 시도: {channel_url}")
            
            # User-Agent 설정으로 봇 차단 방지
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 채널 페이지 요청
            response = requests.get(channel_url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"채널 페이지 요청 실패: HTTP {response.status_code}")
                return None
                
            # HTML에서 채널 ID 찾기
            html_content = response.text
            
            # 방법 1: 'https://www.youtube.com/channel/UC' 패턴 검색
            import re
            channel_id_pattern = r'https://www.youtube.com/channel/(UC[a-zA-Z0-9_-]{22})'
            matches = re.findall(channel_id_pattern, html_content)
            
            if matches:
                channel_id = matches[0]
                logger.info(f"웹 스크래핑으로 채널 ID 발견: {channel_id}")
                return channel_id
                
            # 방법 2: 'channelId":"UC' 패턴 검색 (JSON 데이터에서)
            channel_id_json_pattern = r'channelId":"(UC[a-zA-Z0-9_-]{22})'
            matches = re.findall(channel_id_json_pattern, html_content)
            
            if matches:
                channel_id = matches[0]
                logger.info(f"웹 스크래핑으로 채널 ID 발견: {channel_id}")
                return channel_id
                
            logger.warning(f"웹 스크래핑으로 채널 ID를 찾을 수 없음: {channel_url}")
            return None
            
        except Exception as e:
            logger.error(f"웹 스크래핑 실패: {str(e)}")
            return None

    def get_latest_videos(self, channel_id):
        """채널의 전날 업로드된 모든 일반 영상 가져오기"""
        try:
            # 1. 채널 정보와 업로드 플레이리스트 ID 가져오기 (Playlists:list)
            # 필요한 필드만 지정하여 데이터 전송량 최소화
            channel_response = self.youtube.channels().list(
                part="contentDetails,snippet",
                id=channel_id,
                fields="items(snippet/title,contentDetails/relatedPlaylists/uploads)"
            ).execute()
            
            if not channel_response.get('items'):
                return None, None
            
            channel_name = channel_response['items'][0]['snippet']['title']
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            videos = []
            
            # 현재 시간(KST) 기준으로 체크
            kst = pytz.timezone('Asia/Seoul')
            kst_now = datetime.now(kst)
            
            # 전날 오전 7시부터 오늘 오전 7시까지의 기간 설정
            today_7am = kst_now.replace(hour=7, minute=0, second=0, microsecond=0)
            yesterday_7am = today_7am - timedelta(days=1)
            # 더 넓은 범위로 검색 (최근 7일)
            seven_days_ago = today_7am - timedelta(days=7)
            
            logger.info(f"검색 기간: {yesterday_7am.strftime('%Y-%m-%d %H:%M')} ~ {today_7am.strftime('%Y-%m-%d %H:%M')} (KST)")
            
            # 2. 업로드된 모든 비디오의 ID 가져오기 (PlaylistItems:list)
            # 최대 50개씩, 3번 페이징하여 최대 150개 영상 확인 (더 오래된 영상은 필요 없음)
            next_page_token = None
            all_video_ids = []
            max_pages = 3
            current_page = 0
            total_videos_checked = 0
            videos_in_date_range = 0
            
            while current_page < max_pages:
                # 필요한 필드만 요청하여 불필요한 데이터 전송 줄이기
                playlist_items_params = {
                    "part": "snippet,contentDetails",
                    "playlistId": uploads_playlist_id,
                    "maxResults": 50,
                    "fields": "nextPageToken,items(contentDetails/videoId,snippet/publishedAt,snippet/title)"
                }
                
                if next_page_token:
                    playlist_items_params["pageToken"] = next_page_token
                
                playlist_items_response = self.youtube.playlistItems().list(**playlist_items_params).execute()
                
                # 페이지별로 동영상 정보 수집
                video_ids_in_date_range = []
                all_too_old = True
                
                for item in playlist_items_response.get('items', []):
                    video_id = item['contentDetails']['videoId']
                    video_title = item['snippet']['title']
                    published_at = datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                    published_at_kst = published_at.astimezone(kst)
                    total_videos_checked += 1
                    
                    logger.info(f"영상 확인: '{video_title}' (업로드: {published_at_kst.strftime('%Y-%m-%d %H:%M')})")
                    
                    # 전날 오전 7시부터 현재 시간 사이에 업로드된 영상만 필터링
                    if yesterday_7am <= published_at_kst < kst_now:
                        video_ids_in_date_range.append(video_id)
                        videos_in_date_range += 1
                        all_too_old = False
                        logger.info(f"✅ 날짜 범위 내 영상: '{video_title}'")
                    elif published_at_kst >= today_7am:
                        # 너무 최근 영상은 무시하고 계속 확인
                        all_too_old = False
                        
                    elif published_at_kst < seven_days_ago:
                        # 너무 오래된 영상이 나오기 시작하면, 이후 영상도 모두 오래된 것일 가능성 높음                        
                        pass
                    else:
                        all_too_old = False
                
                all_video_ids.extend(video_ids_in_date_range)
                
                # 다음 페이지 확인 또는 종료 조건
                next_page_token = playlist_items_response.get('nextPageToken')
                current_page += 1
                
                # 모든 영상이 너무 오래됐거나, 다음 페이지가 없으면 종료
                if all_too_old or not next_page_token:
                    break
            
            logger.info(f"총 {total_videos_checked}개 영상 확인, 날짜 범위 내 영상: {videos_in_date_range}개")
            
            # 해당 날짜 범위의 영상이 없으면 종료
            if not all_video_ids:
                logger.warning(f"날짜 범위 내 영상이 없습니다: {yesterday_7am.strftime('%Y-%m-%d %H:%M')} ~ {today_7am.strftime('%Y-%m-%d %H:%M')}")
                return None, channel_name
            
            # 3. 영상 ID로 세부 정보 요청 (Videos:list)
            # 50개씩 나누어 영상 정보 요청 (YouTube API 제한)
            suitable_videos = 0
            excluded_videos = 0
            
            for i in range(0, len(all_video_ids), 50):
                batch_video_ids = all_video_ids[i:i+50]
                
                # 필요한 필드만 요청하여 데이터 전송량 줄이기
                video_details_response = self.youtube.videos().list(
                    part="contentDetails,snippet,statistics",
                    id=','.join(batch_video_ids),
                    fields="items(id,snippet(title,publishedAt),contentDetails/duration,statistics)"
                ).execute()
                
                for item in video_details_response.get('items', []):
                    video_id = item['id']
                    duration = item['contentDetails']['duration']
                    duration_seconds = self.parse_duration(duration)
                    title = item['snippet']['title']
                    title_lower = title.lower()
                    
                    logger.info(f"\n영상 세부 분석: '{title}'")
                    logger.info(f"  - 길이: {duration_seconds}초 ({duration})")
                    
                    # 영상 필터링 조건
                    is_shorts = '#shorts' in title_lower or 'shorts' in title_lower or duration_seconds <= 60
                    is_stream = any(keyword in title_lower for keyword in ['stream', '스트리밍', '생방송', 'live'])
                    is_too_long = duration_seconds > 3600  # 1시간 초과
                    
                    # 필터링 이유 로그
                    exclusion_reasons = []
                    if is_shorts:
                        if duration_seconds <= 60:
                            exclusion_reasons.append(f"쇼츠 영상 (길이: {duration_seconds}초)")
                        else:
                            exclusion_reasons.append("제목에 'shorts' 포함")
                    if is_stream:
                        exclusion_reasons.append("스트리밍/생방송 영상")
                    if is_too_long:
                        exclusion_reasons.append(f"너무 긴 영상 ({duration_seconds}초 > 3600초)")
                    
                    # 적절한 영상 조건
                    if not any([is_shorts, is_stream, is_too_long]):
                        logger.info(f"✅ 적절한 영상: '{title}' ({duration_seconds}초)")
                        videos.append({
                            'video_id': video_id,
                            'title': item['snippet']['title'],
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'published_at': item['snippet']['publishedAt'],
                            'duration': duration_seconds
                        })
                        suitable_videos += 1
                    else:
                        logger.info(f"❌ 영상 제외: {', '.join(exclusion_reasons)}")
                        excluded_videos += 1
            
            logger.info(f"\n필터링 결과:")
            logger.info(f"  - 적절한 영상: {suitable_videos}개")
            logger.info(f"  - 제외된 영상: {excluded_videos}개")
            
            return videos, channel_name
            
        except Exception as e:
            logger.error(f"최신 일반 영상 검색 실패: {str(e)}")
            return None, None

    def get_channel_transcripts(self, channel_ids):
        """각 채널의 전날 업로드된 모든 일반 영상 가져오기"""
        transcripts = {}
        processed_channels = 0
        
        # YouTube API가 인증되지 않은 경우 조기 반환
        if not self.youtube:
            logger.error("YouTube API가 인증되지 않았습니다. 자막 수집을 건너뜁니다.")
            return {}
        
        # SOCKS 프록시 설정 (선택적)
        proxies = None
        try:
            # Tor 프록시 연결 테스트
            import requests
            test_proxies = {
                "https": "socks5://127.0.0.1:9050",
                "http": "socks5://127.0.0.1:9050",
            }
            # 간단한 연결 테스트
            response = requests.get("https://httpbin.org/ip", 
                                  proxies=test_proxies, timeout=5)
            if response.status_code == 200:
                proxies = test_proxies
                logger.info("Tor 프록시 연결 성공, SOCKS 프록시를 사용합니다.")
            else:
                logger.info("Tor 프록시 테스트 실패, 직접 연결을 사용합니다.")
        except Exception as e:
            logger.info(f"Tor 프록시를 사용할 수 없습니다: {str(e)}")
            logger.info("직접 연결을 사용합니다.")
        
        # IP 차단 방지를 위한 재시도 설정
        max_retries = 3
        retry_delay = 5  # 초 단위 기본 대기 시간
        
        # 채널 ID 목록을 한 번에 요청하여 채널 정보 가져오기 (배치 처리로 최적화)
        channel_info_map = {}
        if len(channel_ids) > 0:
            for i in range(0, len(channel_ids), 50):  # 최대 50개씩 처리
                batch_channel_ids = channel_ids[i:i+50]
                try:
                    channels_response = self.youtube.channels().list(
                        part="snippet",
                        id=','.join(batch_channel_ids),
                        fields="items(id,snippet/title)"  # 필요한 필드만 요청
                    ).execute()
                    
                    for item in channels_response.get('items', []):
                        channel_info_map[item['id']] = item['snippet']['title']
                except Exception as e:
                    logger.error(f"채널 정보 일괄 요청 중 오류: {str(e)}")
        
        for channel_id in channel_ids:
            try:
                # 미리 가져온 채널 정보 사용
                if channel_id in channel_info_map:
                    channel_name = channel_info_map[channel_id]
                else:
                    # 개별 요청으로 폴백
                    try:
                        channel_response = self.youtube.channels().list(
                            part="snippet",
                            id=channel_id,
                            fields="items(snippet/title)"  # 필요한 필드만 요청
                        ).execute()
                        
                        if not channel_response.get('items'):
                            logger.error(f"채널 정보를 찾을 수 없음: {channel_id}")
                            continue
                            
                        channel_name = channel_response['items'][0]['snippet']['title']
                    except Exception as e:
                        logger.error(f"채널 정보 요청 실패 ({channel_id}): {str(e)}")
                        continue
                
                logger.info(f"\n=== {channel_name} 채널 처리 시작 ===")
                
                # 전날 업로드된 모든 영상 가져오기
                videos, _ = self.get_latest_videos(channel_id)
                if not videos:
                    logger.error(f"{channel_name}: 적절한 일반 영상을 찾을 수 없음")
                    continue

                channel_transcripts = []
                for video in videos:
                    logger.info(f"영상 정보:")
                    logger.info(f"제목: {video['title']}")
                    logger.info(f"URL: {video['url']}")
                    logger.info(f"게시일: {video['published_at']}")

                    # 영상 정보를 가져온 후 요청 과부하 방지를 위해 약간의 지연 추가
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    try:
                        transcript_list = None
                        language = None
                        
                        # 재시도 로직 적용
                        for attempt in range(max_retries):
                            try:
                                # 자막을 개별적으로 시도하는 방식으로 변경
                                logger.info("자막 가져오기 시도...")
                                
                                # 먼저 한국어 자막 시도
                                try:
                                    transcript_list = YouTubeTranscriptApi.get_transcript(
                                        video['video_id'], 
                                        languages=['ko'],
                                        proxies=proxies
                                    )
                                    language = 'ko'
                                    logger.info("한국어 자막을 찾았습니다.")
                                    break
                                except (TranscriptsDisabled, NoTranscriptFound):
                                    logger.info("한국어 자막이 없습니다. 영어 자막을 시도합니다.")
                                except YouTubeRequestFailed as e:
                                    if "Too Many Requests" in str(e):
                                        logger.warning(f"YouTube 요청 제한에 도달했습니다. 재시도 중... ({attempt+1}/{max_retries})")
                                        # 지수 백오프 전략 적용 - 실패할 때마다 대기 시간 증가
                                        wait_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                                        logger.info(f"{wait_time:.1f}초 대기 후 재시도합니다.")
                                        time.sleep(wait_time)
                                        continue
                                    else:
                                        raise
                                    
                                # 영어 자막 시도
                                try:
                                    transcript_list = YouTubeTranscriptApi.get_transcript(
                                        video['video_id'], 
                                        languages=['en'],
                                        proxies=proxies
                                    )
                                    language = 'en'
                                    logger.info("영어 자막을 찾았습니다.")
                                    break
                                except (TranscriptsDisabled, NoTranscriptFound):
                                    logger.info("영어 자막이 없습니다. 자동 생성 자막을 시도합니다.")
                                except YouTubeRequestFailed as e:
                                    if "Too Many Requests" in str(e):
                                        # 이미 위에서 처리되었으므로 다시 루프
                                        continue
                                    else:
                                        raise
                                
                                # 한국어 자동 생성 자막 시도
                                try:
                                    transcript_list = YouTubeTranscriptApi.get_transcript(
                                        video['video_id'], 
                                        languages=['ko-KR', 'ko'],
                                        proxies=proxies
                                    )
                                    language = 'ko-auto'
                                    logger.info("한국어 자동 생성 자막을 찾았습니다.")
                                    break
                                except (TranscriptsDisabled, NoTranscriptFound):
                                    logger.info("한국어 자동 생성 자막이 없습니다. 영어 자동 생성 자막을 시도합니다.")
                                except YouTubeRequestFailed as e:
                                    if "Too Many Requests" in str(e):
                                        # 이미 위에서 처리되었으므로 다시 루프
                                        continue
                                    else:
                                        raise
                                
                                # 영어 자동 생성 자막 시도
                                try:
                                    transcript_list = YouTubeTranscriptApi.get_transcript(
                                        video['video_id'], 
                                        languages=['en-US', 'en'],
                                        proxies=proxies
                                    )
                                    language = 'en-auto'
                                    logger.info("영어 자동 생성 자막을 찾았습니다.")
                                    break
                                except (TranscriptsDisabled, NoTranscriptFound):
                                    logger.info("어떤 자막도 찾을 수 없습니다.")
                                except YouTubeRequestFailed as e:
                                    if "Too Many Requests" in str(e):
                                        # 이미 위에서 처리되었으므로 다시 루프
                                        continue
                                    else:
                                        raise
                                
                            except Exception as e:
                                if "Too Many Requests" in str(e) and attempt < max_retries - 1:
                                    # 지수 백오프 전략 적용 - 실패할 때마다 대기 시간 증가
                                    wait_time = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                                    logger.warning(f"YouTube 요청 제한에 도달했습니다. {wait_time:.1f}초 후 재시도합니다. ({attempt+1}/{max_retries})")
                                    time.sleep(wait_time)
                                else:
                                    # 다른 종류의 오류이거나 최대 재시도 횟수를 초과한 경우
                                    logger.error(f"자막 가져오기 실패: {str(e)}")
                                    break

                        if not transcript_list:
                            logger.warning(f"최대 시도 횟수({max_retries}회) 후에도 자막을 가져오지 못했습니다.")
                            continue

                        if transcript_list:
                            full_transcript = ' '.join([item['text'] for item in transcript_list])
                            logger.info(f"추출된 자막 길이: {len(full_transcript)} 글자")

                            if len(full_transcript) < 100:
                                logger.warning(f"{channel_name}: 자막이 너무 짧음 ({len(full_transcript)} 글자)")
                                continue

                            channel_transcripts.append({
                                'title': video['title'],
                                'transcript': full_transcript,
                                'url': video['url'],
                                'published_at': video['published_at'],
                                'language': language
                            })
                            
                            # 성공적으로 자막을 가져온 후 다음 비디오 처리 전 잠시 대기
                            time.sleep(random.uniform(2.0, 3.0))

                    except Exception as e:
                        logger.error(f"{channel_name} 자막 처리 중 오류: {str(e)}", exc_info=True)
                        continue
                
                if channel_transcripts:
                    transcripts[channel_name] = channel_transcripts
                    processed_channels += 1
                    logger.info(f"✅ {channel_name}: 자막 처리 완료")
                
            except Exception as e:
                logger.error(f"채널 처리 중 오류 ({channel_id}): {str(e)}", exc_info=True)
                continue
                
        logger.info(f"\n총 {processed_channels}개 채널의 영상을 처리했습니다.")
        return transcripts