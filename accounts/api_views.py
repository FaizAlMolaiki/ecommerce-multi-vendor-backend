from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.mail import send_mail
from accounts.models import User
from accounts.serializer import (ChangePasswordSerializer, CheckPasswordSerializer, ConfirmResetSerializer,
                                 RegisterSerializer, ResendOTPSerializer, ResetPasswordSerializer, UserSerializer, VerifyOTPSerializer,)
from .otp_manager import OTPManager
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
import secrets  # لتوليد رمز إعادة تعيين آمن
import hashlib  # لتجزئة رمز إعادة التعيين
from django.core.cache import cache  # تأكد من استيراد cache


MAX_VERIFY_ATTEMPTS = 5
# ثابت لمدة صلاحية رمز إعادة التعيين الذي سيتم إنشاؤه (مثلاً 10 دقائق)
RESET_TOKEN_TIMEOUT_SECONDS = 10 * 60


class AuthBaseView(APIView):
    def send_otp_email(self, email, otp):
        send_mail(
            subject="تأكيد حسابك",
            message=f"رمز التحقق الخاص بك هو: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email]
        )
        print(f"OTP for {email}: {otp}")


class RegisterView(AuthBaseView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        if User.objects.filter(email=email).exists():
            return Response({'email': 'البريد الإلكتروني مسجل مسبقًا'}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(**serializer.validated_data)
        otp = OTPManager.generate_otp(email)
        self.send_otp_email(email, otp)

        return Response({'message': 'تم التسجيل بنجاح، يرجى التحقق من البريد'})


class VerifyOTPView(AuthBaseView):
    def post(self, request):

        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        result = OTPManager.verify_otp(email, otp)
        if not result['valid']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=email)
        user.is_verified = True
        user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        })


class VerifyResetOTPView(AuthBaseView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        otp_cache_key = f'otp:{email}'
        cached_otp_data = cache.get(otp_cache_key)

        result = OTPManager.verify_otp(email, otp)
        if not result['valid']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        if cached_otp_data is None:
            return Response({'error': 'كود التحقق منتهي الصلاحية أو غير صحيح، يرجى طلب كود جديد.'},
                            status=status.HTTP_400_BAD_REQUEST)

        reset_token = secrets.token_urlsafe(32)

        hashed_reset_token = hashlib.sha256(reset_token.encode()).hexdigest()
        reset_token_cache_key = f'reset_token:{hashed_reset_token}'

        cache.set(reset_token_cache_key, {
                  'email': email}, RESET_TOKEN_TIMEOUT_SECONDS)
        # للتصحيح
        print(
            f"Stored hashed reset token in cache for {email} under key {reset_token_cache_key}")

        return Response({
            "message": "تم التحقق بنجاح.",
            "reset_token": reset_token
        }, status=status.HTTP_200_OK)


class ResendOTPView(AuthBaseView):
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        print(request.data)
        if not serializer.is_valid():
            print(serializer.errors)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        # حساب وقت الانتظار المتبقي
        cooldown = OTPManager.get_resend_cooldown(email)
        if cooldown > 0:
            return Response({
                'error': f'يرجى الانتظار {int(cooldown)} ثانية قبل إعادة المحاولة',
                'waiting_seconds': int(cooldown)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # توليد OTP جديد
        otp = OTPManager.generate_otp(email)
        self.send_otp_email(email, otp)

        return Response({'message': 'تم إرسال كود التحقق'})


class LoginView(AuthBaseView):
    def post(self, request):
        email = request.data.get('email', None)
        password = request.data.get('password', None)
        print(email)
        print(password)
        user = authenticate(username=email, password=password)
        if not user:
            return Response({'error': 'بيانات الاعتماد غير صحيحة'}, status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data
        })


class ResetPasswordView(AuthBaseView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        if not User.objects.filter(email=email).exists():
            return Response({'error': 'البريد الإلكتروني غير مسجل'}, status=status.HTTP_404_NOT_FOUND)

        # حساب وقت الانتظار المتبقي
        cooldown = OTPManager.get_resend_cooldown(email)
        print(cooldown)
        if cooldown > 0:
            return Response({
                'error': f'يرجى الانتظار {int(cooldown)} ثانية قبل إعادة المحاولة',
                'waiting_seconds': cooldown
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = OTPManager.generate_otp(email)
        self.send_otp_email(email, otp)
        return Response({'message': 'تم إرسال كود التحقق'})


class ConfirmResetView(AuthBaseView):
    def post(self, request):
        serializer = ConfirmResetSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        reset_token_provided = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        hashed_token_provided = hashlib.sha256(
            reset_token_provided.encode()).hexdigest()
        reset_token_cache_key = f'reset_token:{hashed_token_provided}'

        cached_data = cache.get(reset_token_cache_key)

        if cached_data is None:
            return Response(
                {'error': 'رمز إعادة التعيين غير صالح أو منتهي الصلاحية. يرجى طلب إعادة تعيين مرة أخرى.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cache.delete(reset_token_cache_key)
        # للتصحيح
        print(
            f"Deleted reset token from cache with key: {reset_token_cache_key}")

        email = cached_data.get('email')
        if not email:
            print(
                f"Error: Email not found in cached data for token key {reset_token_cache_key}")
            return Response({'error': 'حدث خطأ داخلي أثناء معالجة الطلب.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.verified = True
            user.save()
        except User.DoesNotExist:
            print(
                f"Error: User with email {email} not found during password reset.")
            return Response({'error': 'المستخدم المرتبط بهذا الطلب غير موجود.'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error saving user {email} after password reset: {e}")
            return Response({'error': 'حدث خطأ أثناء تحديث كلمة المرور.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {"message": "تم تغيير كلمة المرور بنجاح."},
            status=status.HTTP_200_OK
        )


class CheckPasswordView(AuthBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CheckPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['password']):
            return Response({'error': 'كلمة المرور الحالية غير صحيحة'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'كلمه المرور صحيحه'})


class ChangePasswordView(AuthBaseView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'كلمة المرور القديمة غير صحيحة'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'تم تغيير كلمة المرور بنجاح'})

# تأكد من استيراد هذه المكتبات في أعلى الملف


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required for logout."},
                status=status.HTTP_400_BAD_REQUEST  # 400 Bad Request أكثر ملاءمة من 401
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except TokenError as e:
            # هذا يحدث إذا كان التوكن غير صالح، منتهي الصلاحية، أو مدرج في القائمة السوداء بالفعل
            return Response(
                {"error": "Invalid or expired refresh_token.",
                    "detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # لأي أخطاء أخرى غير متوقعة
            print(f"Unexpected error during logout: {e}")
            return Response(
                {"error": "An unexpected error occurred during logout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
