from django.db import models
from django.core.validators import EmailValidator, URLValidator
from django.contrib.auth.hashers import make_password, check_password


class Subscription(models.Model):
    """유튜브 채널 구독 정보 모델"""
    
    name = models.CharField(
        max_length=100, 
        default="구독자", 
        verbose_name="구독자 이름"
    )
    email = models.EmailField(
        validators=[EmailValidator()],
        verbose_name="이메일",
        unique=True
    )
    password = models.CharField(
        max_length=128,
        verbose_name="비밀번호",
        help_text="구독 정보 수정 시 사용할 비밀번호",
        default="defaultpassword123"
    )
    youtube_channel_url = models.URLField(
        validators=[URLValidator()], 
        verbose_name="YouTube 채널 URL",
        default="https://www.youtube.com/@default"
    )
    channel_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        default="기본 채널",
        verbose_name="채널 이름"
    )
    notification_time = models.TimeField(
        default='09:00', 
        verbose_name="알림 시간"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="활성 상태"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="생성일"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="수정일"
    )
    last_video_check = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="마지막 영상 확인 시간"
    )
    
    def set_password(self, raw_password):
        """비밀번호를 해시화하여 저장"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """비밀번호 확인"""
        return check_password(raw_password, self.password)
    
    class Meta:
        verbose_name = "구독"
        verbose_name_plural = "구독 목록"
        ordering = ['-created_at']
    
    def __str__(self):
        channel_display = self.channel_name or self.youtube_channel_url
        return f"{self.name} - {channel_display}"


class EmailLog(models.Model):
    """이메일 발송 로그"""
    
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE, 
        verbose_name="구독",
        related_name='email_logs'
    )
    subject = models.CharField(
        max_length=200, 
        default="YouTube 알림", 
        verbose_name="제목"
    )
    content = models.TextField(
        default="새로운 영상이 업로드되었습니다.", 
        verbose_name="내용"
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="발송 시간")
    is_successful = models.BooleanField(default=True, verbose_name="발송 성공 여부")
    error_message = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="오류 메시지"
    )
    
    class Meta:
        verbose_name = "이메일 로그"
        verbose_name_plural = "이메일 로그 목록"
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"Email to {self.subscription.email} at {self.sent_at}"
