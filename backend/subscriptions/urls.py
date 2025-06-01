from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # 메인 구독 API (REST API 스타일)
    path('', views.SubscriptionListCreateView.as_view(), 
         name='subscription-list-create'),
    path('<int:pk>/', views.SubscriptionDetailView.as_view(), 
         name='subscription-detail'),
    
    # 기존 구독 관리 (호환성 유지)
    path('register/', views.SubscriptionCreateView.as_view(), 
         name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('<int:id>/update/', views.SubscriptionUpdateView.as_view(), 
         name='update'),
    path('<int:id>/delete/', views.SubscriptionDeleteView.as_view(), 
         name='delete'),
    
    # 이메일 로그
    path('email-logs/', views.EmailLogListView.as_view(), 
         name='email-logs'),
    
    # 테스트 이메일
    path('test-email/', views.TestEmailView.as_view(), 
         name='test-email'),
    
    # 헬스 체크
    path('health/', views.health_check, name='health'),
    
    # 인증
    path('auth/login/', views.login_view, name='login'),
    path('auth/admin-login/', 
         views.AdminLoginView.as_view(), 
         name='admin-login'),
    
    # 관리자 API
    path('admin/subscriptions/', 
         views.admin_subscriptions_view, 
         name='admin-subscriptions'),
    path('admin/subscriptions/<int:subscription_id>/', 
         views.admin_delete_subscription_view, 
         name='admin-delete-subscription'),
    path('admin/stats/', 
         views.admin_stats_view, 
         name='admin-stats'),
    path('admin/send-test-email/', 
         views.admin_send_test_email_view, 
         name='admin-send-test-email'),
    path('admin/process-youtube-summaries/', 
         views.admin_process_youtube_summaries, 
         name='admin_process_youtube_summaries'),
    
    # 정시 발송 테스트 API
    path('admin/test-scheduled-email/', 
         views.admin_test_scheduled_email_view, 
         name='admin-test-scheduled-email'),
    path('admin/check-cache/', 
         views.admin_check_cache_view, 
         name='admin-check-cache'),
    path('admin/create-test-subscription/', 
         views.admin_create_test_subscription_view, 
         name='admin-create-test-subscription'),
] 