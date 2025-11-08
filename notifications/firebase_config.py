"""
إعدادات Firebase Cloud Messaging
يتم تهيئة Firebase Admin SDK هنا
"""
import os
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    تهيئة Firebase Admin SDK
    """
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # التحقق من عدم التهيئة المسبقة
        if firebase_admin._apps:
            logger.info("Firebase already initialized")
            return True
        
        # البحث عن ملف serviceAccountKey.json
        base_dir = Path(settings.BASE_DIR)
        service_account_paths = [
            base_dir / 'firebase_credentials.json',
            base_dir / 'serviceAccountKey.json',
            base_dir / 'firebase' / 'serviceAccountKey.json',
        ]
        
        # محاولة إيجاد الملف
        credential_path = None
        for path in service_account_paths:
            if path.exists():
                credential_path = path
                break
        
        if not credential_path:
            logger.warning(
                "Firebase credentials file not found. "
                "FCM notifications will be disabled. "
                "Please add 'serviceAccountKey.json' to the project root."
            )
            return False
        
        # تهيئة Firebase
        cred = credentials.Certificate(str(credential_path))
        firebase_admin.initialize_app(cred)
        
        logger.info(f"Firebase initialized successfully from {credential_path}")
        return True
        
    except ImportError:
        logger.error("firebase-admin package not installed. Run: pip install firebase-admin")
        return False
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        return False


def is_fcm_enabled():
    """
    التحقق من تفعيل FCM
    """
    config = getattr(settings, 'NOTIFICATIONS_CONFIG', {})
    return config.get('ENABLE_FCM', False)
