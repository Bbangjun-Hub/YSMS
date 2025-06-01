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
    # 10분 전 준비 작업 (매분 실행하여 10분 전 시점 체크)
    'prepare-emails-10min-before': {
        'task': 'subscriptions.tasks.prepare_scheduled_emails',
        'schedule': 60.0,  # 1분마다 실행하여 10분 전 시점 체크
    },
    
    # 정시 이메일 발송 (30분 단위로만 실행: 매시 0분, 30분)
    'send-scheduled-emails': {
        'task': 'subscriptions.tasks.send_scheduled_emails',
        'schedule': 60.0,  # 1분마다 실행하되 태스크 내에서 30분 단위만 처리
    },
    
    # 캐시 정리 (매일 새벽 2시)
    'cleanup-old-cache': {
        'task': 'subscriptions.tasks.cleanup_old_cache',
        'schedule': crontab(hour=2, minute=0),
    },
}

app.conf.timezone = 'Asia/Seoul' 