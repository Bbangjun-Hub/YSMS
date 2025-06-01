from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Subscription, EmailLog


class SubscriptionSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=6, required=False
    )
    email = serializers.EmailField(required=False)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'name', 'email', 'password', 'youtube_channel_url', 
            'channel_name', 'notification_time', 'is_active', 
            'created_at', 'updated_at'
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
        """구독 생성 시 비밀번호 해시화"""
        # 생성 시에는 email과 password가 필수
        if 'email' not in validated_data:
            raise serializers.ValidationError("이메일은 필수입니다.")
        if 'password' not in validated_data:
            raise serializers.ValidationError("비밀번호는 필수입니다.")
            
        password = validated_data.pop('password')
        subscription = Subscription(**validated_data)
        subscription.set_password(password)
        subscription.save()
        return subscription
    
    def update(self, instance, validated_data):
        """구독 수정 시 비밀번호가 있으면 해시화"""
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        # email 필드는 수정하지 않음 (보안상 이유)
        validated_data.pop('email', None)
        
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
            subscription = Subscription.objects.get(email=email)
            if subscription.check_password(password):
                attrs['subscription'] = subscription
                return attrs
            else:
                raise serializers.ValidationError("비밀번호가 올바르지 않습니다.")
        except Subscription.DoesNotExist:
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