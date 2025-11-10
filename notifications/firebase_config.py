"""
إعدادات Firebase Cloud Messaging
يتم تهيئة Firebase Admin SDK هنا
"""
import os
import json
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

def initialize_firebase():
    """
    تهيئة Firebase Admin SDK
    
    يدعم طريقتين:
    1. Environment Variable: FIREBASE_CREDENTIALS (JSON string)
    2. ملف JSON: serviceAccountKey.json
    
    الأولوية للـ Environment Variable (Production Best Practice)
    """
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # التحقق من عدم التهيئة المسبقة
        if firebase_admin._apps:
            logger.info("Firebase already initialized")
            return True
        
        # ============================================================
        # الطريقة 1: Environment Variable (Production Best Practice)
        # ============================================================
        firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
        
        if firebase_creds_json:
            try:
                # تحويل JSON string إلى dict
                creds_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully from environment variable")
                return True
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in FIREBASE_CREDENTIALS: {e}")
                # نواصل للطريقة الثانية
            except Exception as e:
                logger.error(f"Error initializing Firebase from env var: {e}")
                # نواصل للطريقة الثانية
        
        # ============================================================
        # الطريقة 2: ملف JSON (Development/Fallback)
        # ============================================================
        # البحث عن ملف serviceAccountKey.json
        base_dir = Path(settings.BASE_DIR)
        
        # دعم FIREBASE_CREDENTIALS_PATH من settings
        custom_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
        
        service_account_paths = []
        
        # إضافة المسار المخصص أولاً (إن وُجد)
        if custom_path:
            service_account_paths.append(Path(custom_path))
        
        # المسارات الافتراضية
        service_account_paths.extend([
            base_dir / 'firebase_credentials.json',
            base_dir / 'serviceAccountKey.json',
            base_dir / 'firebase' / 'serviceAccountKey.json',
            base_dir / 'config' / 'firebase.json',
        ])
        
        # محاولة إيجاد الملف
        credential_path = None
        for path in service_account_paths:
            if path.exists():
                credential_path = path
                break
        
        if not credential_path:
            logger.warning(
                "Firebase credentials not found. FCM notifications will be disabled.\n"
                "Setup Options:\n"
                "1. (Production) Set FIREBASE_CREDENTIALS environment variable with JSON content\n"
                "2. (Development) Add 'serviceAccountKey.json' to project root\n"
                "3. Set FIREBASE_CREDENTIALS_PATH in settings.py"
            )
            return False
        
        # تهيئة Firebase من الملف
        cred = credentials.Certificate(str(credential_path))
        
        # قراءة project_id من credentials
        try:
            with open(credential_path, 'r') as f:
                cred_data = json.load(f)
                project_id = cred_data.get('project_id')
                
            # تهيئة مع project_id صريح
            firebase_admin.initialize_app(cred, {
                'projectId': project_id,
            })
            logger.info(f"Firebase initialized successfully from file: {credential_path}")
            logger.info(f"Firebase Project ID: {project_id}")
        except Exception as e:
            # Fallback: تهيئة بدون options
            firebase_admin.initialize_app(cred)
            logger.info(f"Firebase initialized (fallback mode) from file: {credential_path}")
        
        return True
        
    except ImportError:
        logger.error(
            "firebase-admin package not installed.\n"
            "Install it: pip install firebase-admin"
        )
        return False
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}", exc_info=True)
        return False


def is_fcm_enabled():
    """
    التحقق من تفعيل FCM
    """
    config = getattr(settings, 'NOTIFICATIONS_CONFIG', {})
    return config.get('ENABLE_FCM', False)
