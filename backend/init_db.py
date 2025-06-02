#!/usr/bin/env python
"""
데이터베이스 초기화 스크립트
새로운 환경에서 프로젝트를 설정할 때 사용
"""
import os
import django
from django.core.management import execute_from_command_line


def init_database():
    """데이터베이스 초기화 및 기본 데이터 생성"""
    
    # Django 설정
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'youtube_mail_project.settings')
    django.setup()
    
    print("🔄 데이터베이스 초기화를 시작합니다...")
    
    # 1. 마이그레이션 파일 생성
    print("📝 마이그레이션 파일 생성 중...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    # 2. 마이그레이션 적용
    print("🔧 마이그레이션 적용 중...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # 3. 슈퍼유저 생성 (선택사항)
    print("\n👤 관리자 계정을 생성하시겠습니까? (y/n): ", end="")
    create_superuser = input().lower().strip()
    
    if create_superuser in ['y', 'yes']:
        print("🔐 관리자 계정 생성 중...")
        execute_from_command_line(['manage.py', 'createsuperuser'])
    
    print("\n✅ 데이터베이스 초기화가 완료되었습니다!")
    print("🚀 이제 서버를 시작할 수 있습니다: python manage.py runserver")


if __name__ == '__main__':
    init_database() 