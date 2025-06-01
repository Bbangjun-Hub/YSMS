# Celery 앱이 Django와 함께 로드되도록 설정
from .celery import app as celery_app

__all__ = ('celery_app',)
