from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth import login
from .models import Subscription, EmailLog, User
from .serializers import (
    SubscriptionSerializer, 
    LoginSerializer, 
    EmailLogSerializer,
    TestEmailSerializer,
    AdminLoginSerializer,
    UserSerializer
)
from .tasks import send_test_email_task
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string
from .youtube_mail_service import YouTubeMailService


class SubscriptionCreateView(generics.CreateAPIView):
    """구독 정보 생성"""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # 사용자 이메일과 채널 URL 조합 중복 체크
            user_email = serializer.validated_data.get('user_email')
            youtube_channel_url = serializer.validated_data.get('youtube_channel_url')
            
            try:
                user = User.objects.get(email=user_email)
                if Subscription.objects.filter(
                    user=user, 
                    youtube_channel_url=youtube_channel_url
                ).exists():
                    return Response(
                        {'error': '이미 해당 채널을 구독하고 있습니다.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except User.DoesNotExist:
                pass  # 새 사용자인 경우 중복 체크 불필요
            
            subscription = serializer.save()
            return Response(
                {
                    'message': '구독 정보가 성공적으로 등록되었습니다.',
                    'data': SubscriptionSerializer(subscription).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """로그인 (구독 정보 조회)"""
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            # 해당 사용자의 모든 구독 정보를 반환
            all_subscriptions = Subscription.objects.filter(user=user)
            return Response(
                {
                    'message': '로그인 성공',
                    'user': UserSerializer(user).data,
                    'subscriptions': SubscriptionSerializer(all_subscriptions, many=True).data,
                    'subscription_count': all_subscriptions.count()
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminLoginView(APIView):
    """관리자 로그인"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            return Response(
                {
                    'message': '관리자 로그인 성공',
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'is_superuser': user.is_superuser
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionUpdateView(generics.UpdateAPIView):
    """구독 정보 수정"""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            subscription = serializer.save()
            return Response(
                {
                    'message': '구독 정보가 성공적으로 수정되었습니다.',
                    'data': SubscriptionSerializer(subscription).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubscriptionDeleteView(generics.DestroyAPIView):
    """구독 정보 삭제"""
    queryset = Subscription.objects.all()
    lookup_field = 'id'
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {'message': '구독 정보가 성공적으로 삭제되었습니다.'},
            status=status.HTTP_200_OK
        )


class EmailLogListView(generics.ListAPIView):
    """이메일 로그 목록"""
    serializer_class = EmailLogSerializer
    
    def get_queryset(self):
        subscription_id = self.request.query_params.get('subscription_id')
        if subscription_id:
            return EmailLog.objects.filter(subscription_id=subscription_id)
        return EmailLog.objects.all()


class TestEmailView(APIView):
    """테스트 이메일 발송"""
    
    def post(self, request):
        serializer = TestEmailSerializer(data=request.data)
        if serializer.is_valid():
            subscription_id = serializer.validated_data['subscription_id']
            subscription = get_object_or_404(Subscription, id=subscription_id)
            
            # Celery 태스크로 테스트 이메일 발송
            task = send_test_email_task.delay(subscription_id)
            
            return Response(
                {
                    'message': '테스트 이메일 발송이 시작되었습니다.',
                    'task_id': task.id,
                    'subscription_email': subscription.email
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def health_check(request):
    """헬스 체크"""
    return Response(
        {
            'status': 'healthy',
            'message': 'YouTube Mail Service is running'
        },
        status=status.HTTP_200_OK
    )


class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        email = self.request.query_params.get('email', None)
        if email:
            try:
                user = User.objects.get(email=email)
                return Subscription.objects.filter(user=user)
            except User.DoesNotExist:
                return Subscription.objects.none()
        return Subscription.objects.all()
    
    def perform_create(self, serializer):
        subscription = serializer.save()
        
        # 확인 이메일 발송
        try:
            send_mail(
                subject='YouTube 메일링 구독 확인',
                message=f'''
안녕하세요 {subscription.user.name}님,

YouTube 메일링 서비스에 구독해주셔서 감사합니다.

구독 정보:
- 채널: {subscription.youtube_channel_url}
- 알림 시간: {subscription.user.notification_time}

새로운 영상이 업로드되면 설정하신 시간에 이메일로 알려드리겠습니다.

감사합니다.
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"이메일 발송 실패: {e}")


class SubscriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]


@api_view(['POST'])
def login_view(request):
    """간단한 이메일 기반 로그인"""
    email = request.data.get('email')
    
    if not email:
        return Response(
            {'detail': '이메일을 입력해주세요.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        subscription = Subscription.objects.get(email=email)
        # 간단한 토큰 생성 (실제 프로덕션에서는 JWT 등을 사용)
        token = ''.join(secrets.choice(
            string.ascii_letters + string.digits
        ) for _ in range(32))
        
        return Response(
            {
                'token': token,
                'subscription': SubscriptionSerializer(subscription).data
            },
            status=status.HTTP_200_OK
        )
    except Subscription.DoesNotExist:
        return Response(
            {'detail': '등록된 이메일이 아닙니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )


def is_superuser(user):
    return user.is_authenticated and user.is_superuser


@api_view(['GET'])
@permission_classes([AllowAny])
def admin_subscriptions_view(request):
    """관리자용 구독 목록"""
    subscriptions = Subscription.objects.all()
    serializer = SubscriptionSerializer(subscriptions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def admin_users_view(request):
    """관리자용 사용자 목록"""
    users = User.objects.all()
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def admin_stats_view(request):
    """관리자용 통계"""
    total_subscriptions = Subscription.objects.count()
    active_subscriptions = Subscription.objects.filter(is_active=True).count()
    total_emails_sent = EmailLog.objects.count()
    total_users = User.objects.count()
    
    return Response({
        'total_subscriptions': total_subscriptions,
        'active_subscriptions': active_subscriptions,
        'total_emails_sent': total_emails_sent,
        'total_users': total_users
    })


@api_view(['DELETE'])
@permission_classes([AllowAny])
def admin_delete_subscription_view(request, subscription_id):
    """관리자용 구독 삭제"""
    try:
        subscription = Subscription.objects.get(id=subscription_id)
        subscription.delete()
        return Response(
            {'message': '구독이 성공적으로 삭제되었습니다.'}, 
            status=status.HTTP_200_OK
        )
    except Subscription.DoesNotExist:
        return Response(
            {'error': '구독을 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def admin_delete_user_view(request, user_id):
    """관리자용 사용자 삭제 (연관된 모든 구독도 함께 삭제)"""
    try:
        user = User.objects.get(id=user_id)
        user_email = user.email
        subscription_count = user.subscriptions.count()
        user.delete()  # CASCADE로 인해 연관된 구독들도 자동 삭제
        return Response(
            {
                'message': f'사용자 {user_email}과 연관된 {subscription_count}개의 구독이 성공적으로 삭제되었습니다.'
            }, 
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {'error': '사용자를 찾을 수 없습니다.'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_send_test_email_view(request):
    """관리자용 테스트 이메일 발송"""
    email = request.data.get('email')
    subject = request.data.get('subject', '테스트 이메일')
    message = request.data.get('message', '이것은 테스트 이메일입니다.')
    
    if not email:
        return Response(
            {'error': '이메일 주소가 필요합니다.'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response(
            {'message': '테스트 이메일이 성공적으로 발송되었습니다.'}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': f'이메일 발송 실패: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_test_scheduled_email_view(request):
    """관리자용 정시 발송 테스트"""
    from .tasks import prepare_scheduled_emails, send_scheduled_emails
    
    test_type = request.data.get('test_type', 'prepare')  # 'prepare' 또는 'send'
    
    try:
        if test_type == 'prepare':
            # 30분 전 준비 작업 테스트
            result = prepare_scheduled_emails.delay()
            return Response({
                'message': '이메일 준비 작업이 시작되었습니다.',
                'task_id': result.id,
                'test_type': 'prepare'
            }, status=status.HTTP_200_OK)
            
        elif test_type == 'send':
            # 정시 발송 테스트
            result = send_scheduled_emails.delay()
            return Response({
                'message': '정시 이메일 발송이 시작되었습니다.',
                'task_id': result.id,
                'test_type': 'send'
            }, status=status.HTTP_200_OK)
            
        else:
            return Response({
                'error': 'test_type은 "prepare" 또는 "send"여야 합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'error': f'테스트 실행 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def admin_check_cache_view(request):
    """관리자용 캐시 상태 확인"""
    from django.core.cache import cache
    import pytz
    from datetime import datetime
    
    try:
        kst = pytz.timezone('Asia/Seoul')
        current_time = datetime.now(kst)
        
        cache_status = {}
        
        # 현재 시간 기준으로 앞뒤 2시간의 캐시 상태 확인
        for hour_offset in range(-2, 3):
            check_time = current_time.replace(
                hour=(current_time.hour + hour_offset) % 24,
                minute=0,
                second=0,
                microsecond=0
            )
            
            cache_key = f"prepared_content_{check_time.strftime('%H_%M')}"
            cached_data = cache.get(cache_key)
            
            cache_status[check_time.strftime('%H:%M')] = {
                'cache_key': cache_key,
                'exists': cached_data is not None,
                'data': cached_data if cached_data else None
            }
        
        return Response({
            'current_time': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'cache_status': cache_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'캐시 확인 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_create_test_subscription_view(request):
    """관리자용 테스트 구독 생성"""
    email = request.data.get('email')
    notification_time = request.data.get('notification_time')
    name = request.data.get('name', '테스트 사용자')
    
    if not email or not notification_time:
        return Response({
            'error': '이메일과 알림 시간이 필요합니다.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 기존 구독이 있으면 업데이트, 없으면 생성
        subscription, created = Subscription.objects.update_or_create(
            email=email,
            defaults={
                'name': name,
                'notification_time': notification_time,
                'youtube_channel_url': 'https://www.youtube.com/@bbyonggeul',
                'channel_name': '뿅글이',
                'is_active': True
            }
        )
        
        action = '생성' if created else '업데이트'
        
        return Response({
            'message': f'테스트 구독이 {action}되었습니다.',
            'subscription': {
                'id': subscription.id,
                'email': subscription.email,
                'name': subscription.name,
                'notification_time': subscription.notification_time.strftime('%H:%M'),
                'channel_name': subscription.channel_name,
                'is_active': subscription.is_active
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'테스트 구독 생성 실패: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_process_youtube_summaries(request):
    """관리자용 YouTube 요약 처리 API"""
    try:
        youtube_service = YouTubeMailService()
        result = youtube_service.process_daily_summaries()
        
        return Response({
            'success': result['success'],
            'message': result['message'],
            'processed_count': result['processed_count'],
            'channels_found': result.get('channels_found', 0)
        })
    except Exception as e:
        return Response({
            'success': False,
            'message': f'YouTube 요약 처리 중 오류: {str(e)}'
        }, status=500)


class UserUpdateView(generics.UpdateAPIView):
    """사용자 정보 수정 (알림 시간 등)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'email'
    
    def update(self, request, *args, **kwargs):
        try:
            user = User.objects.get(email=kwargs['email'])
        except User.DoesNotExist:
            return Response(
                {'error': '사용자를 찾을 수 없습니다.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': '사용자 정보가 성공적으로 수정되었습니다.',
                    'data': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)