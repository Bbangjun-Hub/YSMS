import os
from celery import Celery
from celery.schedules import crontab

# Django 설정 모듈 설정
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE', 
    'youtube_mail_project.settings'
)

app = Celery('youtube_mail_project')

# Django 설정에서 Celery 설정 로드
app.config_from_object('django.conf:settings', namespace='CELERY')

# Django 앱에서 태스크 자동 발견
app.autodiscover_tasks()

# 스케줄 설정
app.conf.beat_schedule = {
    # 이메일 준비 작업 (정확한 시간에 실행)
    'prepare-emails-for-00-30': {
        'task': 'subscriptions.tasks.prepare_scheduled_emails',
        'schedule': crontab(minute=20, hour='*'),  # 매시 20분 (30분 발송 준비)
        'options': {'timezone': 'Asia/Seoul'}
    },
    'prepare-emails-for-30-00': {
        'task': 'subscriptions.tasks.prepare_scheduled_emails', 
        'schedule': crontab(minute=50, hour='*'),  # 매시 50분 (정시 발송 준비)
        'options': {'timezone': 'Asia/Seoul'}
    },
    
    # 이메일 발송 작업 (정확한 시간에 실행)
    'send-emails-at-00': {
        'task': 'subscriptions.tasks.send_scheduled_emails',
        'schedule': crontab(minute=0, hour='*'),  # 매시 정각
        'options': {'timezone': 'Asia/Seoul'}
    },
    'send-emails-at-30': {
        'task': 'subscriptions.tasks.send_scheduled_emails',
        'schedule': crontab(minute=30, hour='*'),  # 매시 30분
        'options': {'timezone': 'Asia/Seoul'}
    },
    
    # 캐시 정리 작업 (매일 새벽 2시)
    'cleanup-cache': {
        'task': 'subscriptions.tasks.cleanup_old_cache',
        'schedule': crontab(minute=0, hour=2),  # 매일 새벽 2시
        'options': {'timezone': 'Asia/Seoul'}
    },
    
    # 토큰 자동 갱신 작업 (매일 새벽 1시)
    'refresh-google-token': {
        'task': 'subscriptions.tasks.refresh_google_token',
        'schedule': crontab(minute=0, hour=1),  # 매일 새벽 1시
        'options': {'timezone': 'Asia/Seoul'}
    },
}

app.conf.timezone = 'Asia/Seoul' 