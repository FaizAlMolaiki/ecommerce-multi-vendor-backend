
from django.core.cache import cache
import pyotp
from datetime import datetime, timedelta
import math
OTP_TIMEOUT = 300  # 5 دقائق للصلاحية
MAX_VERIFY_ATTEMPTS = 5
MAX_RESEND_ATTEMPTS = 5

class OTPManager:
    @staticmethod
    def generate_otp(email):
        secret = pyotp.random_base32()
        otp = pyotp.TOTP(secret, interval=OTP_TIMEOUT).now()
        
        # تخزين السر مع الوقت وعدد المحاولات
        cache_data = {
            'secret': secret,
            'verify_attempts': 0,
        }
        # زيادة عداد الإرسال
        OTPManager.increment_resend_count(email)
        
        cache.set(f'otp:{email}', cache_data, OTP_TIMEOUT)
       
        return otp

    @staticmethod
    def verify_otp(email, otp):
        cache_key = f'otp:{email}'
        data = cache.get(cache_key)
        
        if not data:
            return {'valid': False, 'error': 'OTP منتهي الصلاحية او غير صحيح'}
        
        # التحقق من عدد محاولات التحقق
        if data['verify_attempts'] >= MAX_VERIFY_ATTEMPTS:
            return {'valid': False, 'error': 'تم تجاوز الحد الأقصى للمحاولات'}
        
        # زيادة عداد المحاولات
        data['verify_attempts'] += 1
        cache.set(cache_key, data, OTP_TIMEOUT)
        
        totp = pyotp.TOTP(data['secret'], interval=OTP_TIMEOUT)
        if totp.verify(otp):
            
            cache.delete(cache_key)
            OTPManager.reset_resend_count(email)
            return {'valid': True}
        return {'valid': False,'error':"رمز التحقق غير صحيح"}

    @staticmethod
    def get_resend_cooldown(email):
        resend_count = cache.get(f'resend_count:{email}', 0)
        if resend_count < MAX_RESEND_ATTEMPTS:
            return 0
        
        # معادلة زيادة وقت الانتظار (أسية)
        wait_minutes = math.pow(2, resend_count - MAX_RESEND_ATTEMPTS)
        last_resend_time = cache.get(f'last_resend:{email}')
        
        if last_resend_time:
            elapsed = datetime.now() - last_resend_time
            remaining = timedelta(minutes=wait_minutes) - elapsed
            return max(remaining.total_seconds(), 0)
        
        return wait_minutes * 60

    @staticmethod
    def increment_resend_count(email):
        count = cache.get(f'resend_count:{email}', 0) + 1
        cache.set(f'resend_count:{email}', count)
        cache.set(f'last_resend:{email}', datetime.now())
        return count
    @staticmethod
    def reset_resend_count(email):
        cache.delete(f'resend_count:{email}')
        cache.delete(f'last_resend:{email}')