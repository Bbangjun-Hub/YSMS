from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Subscription, EmailLog, User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=6, required=False
    )
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'email', 'password', 'notification_time', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """사용자 생성 시 비밀번호 해시화"""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """사용자 수정 시 비밀번호가 있으면 해시화"""
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SubscriptionSerializer(serializers.ModelSerializer):
    # User 모델에서 가져오는 필드들
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    notification_time = serializers.TimeField(
        source='user.notification_time', read_only=True
    )
    
    # 새 구독 생성 시 필요한 필드들
    user_name = serializers.CharField(write_only=True, required=False)
    user_email = serializers.EmailField(write_only=True, required=False)
    password = serializers.CharField(
        write_only=True, min_length=6, required=False
    )
    user_notification_time = serializers.TimeField(
        write_only=True, required=False
    )
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'name', 'email', 'notification_time', 'youtube_channel_url', 
            'channel_name', 'is_active', 'created_at', 'updated_at',
            'user_name', 'user_email', 'password', 'user_notification_time'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_youtube_channel_url(self, value):
        """YouTube URL 유효성 검사"""
        if not any(domain in value for domain in ['youtube.com', 'youtu.be']):
            raise serializers.ValidationError(
                "올바른 YouTube URL을 입력해주세요."
            )
        return value
    
    def create(self, validated_data):
        """구독 생성 - 사용자가 없으면 생성, 있으면 기존 사용자 사용"""
        user_email = validated_data.pop('user_email', None)
        user_name = validated_data.pop('user_name', None)
        password = validated_data.pop('password', None)
        user_notification_time = validated_data.pop(
            'user_notification_time', None
        )
        
        if not user_email:
            raise serializers.ValidationError("이메일은 필수입니다.")
        
        # 기존 사용자 확인
        user, created = User.objects.get_or_create(
            email=user_email,
            defaults={
                'name': user_name or '구독자',
                'notification_time': user_notification_time or '09:00'
            }
        )
        
        # 새 사용자인 경우 비밀번호 설정
        if created:
            if not password:
                raise serializers.ValidationError(
                    "새 사용자는 비밀번호가 필요합니다."
                )
            user.set_password(password)
            user.save()
        
        # 구독 생성
        subscription = Subscription.objects.create(
            user=user,
            **validated_data
        )
        return subscription
    
    def update(self, instance, validated_data):
        """구독 수정"""
        # 사용자 관련 필드는 제거 (별도로 관리)
        validated_data.pop('user_email', None)
        validated_data.pop('user_name', None)
        validated_data.pop('password', None)
        validated_data.pop('user_notification_time', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError(
                    "비밀번호가 올바르지 않습니다."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError("등록된 이메일이 아닙니다.")


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_superuser:
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError("관리자 권한이 필요합니다.")
            else:
                raise serializers.ValidationError("잘못된 사용자명 또는 비밀번호입니다.")
        else:
            raise serializers.ValidationError("사용자명과 비밀번호를 모두 입력해주세요.")


class EmailLogSerializer(serializers.ModelSerializer):
    subscription_email = serializers.CharField(
        source='subscription.email', 
        read_only=True
    )
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'subscription', 'subscription_email', 'subject', 'content',
            'sent_at', 'is_successful', 'error_message'
        ]
        read_only_fields = ['id', 'sent_at']


class TestEmailSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()
    
    def validate_subscription_id(self, value):
        try:
            Subscription.objects.get(id=value)
            return value
        except Subscription.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 구독입니다.") 