import os
import time
import hashlib
from datetime import datetime
from uuid import uuid4
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, parsers
from rest_framework.parsers import MultiPartParser, FormParser
import logging

logger = logging.getLogger(__name__)

class BaseImageUploadView(APIView):
    """
    Base class for image upload functionality
    نسخة من Backend السابق مع تحسينات
    """
    permission_classes = [permissions.IsAuthenticated]  # ✅ تأمين - يجب المصادقة
    parser_classes = [MultiPartParser, FormParser]
    
    def validate_image(self, file_obj, max_size=5*1024*1024):
        """التحقق من صحة الصورة"""
        if not file_obj:
            return False, "حقل 'image' مطلوب"
        
        if file_obj.size > max_size:
            return False, f'حجم الصورة يتجاوز {max_size // (1024*1024)}MB'
        
        content_type = (file_obj.content_type or '').lower()
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg', 'image/gif']
        if not any(ct in content_type for ct in allowed_types):
            return False, 'نوع الصورة غير مدعوم'
        
        return True, None
    
    def save_image(self, file_obj, folder='uploads'):
        """حفظ الصورة وإرجاع URL"""
        ext = os.path.splitext(file_obj.name)[1].lower() or '.jpg'
        today = datetime.utcnow()
        dir_path = f"{folder}/{today.year:04d}/{today.month:02d}/{today.day:02d}"
        filename = f"{uuid4().hex}{ext}"
        upload_path = f"{dir_path}/{filename}"
        
        try:
            raw = file_obj.read()
            saved_path = default_storage.save(upload_path, ContentFile(raw))
            file_hash = hashlib.sha256(raw).hexdigest()[:16]
            
            logger.info(f"Image saved: {saved_path}, hash: {file_hash}")
            return saved_path, file_hash
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise e


class UploadImageView(BaseImageUploadView):
    """
    POST /api/v1/upload/image/
    رفع صورة عامة - نسخة من Backend السابق
    """
    def post(self, request, *args, **kwargs):
        t0 = time.time()
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '-')
        
        logger.info(f"Image upload request from {client_ip}")
        
        file_obj = request.FILES.get('image')
        folder = request.data.get('folder', 'uploads')
        
        # التحقق من صحة الصورة
        is_valid, error_msg = self.validate_image(file_obj)
        if not is_valid:
            logger.warning(f"Invalid image upload: {error_msg}")
            return Response({'detail': error_msg}, status=400)
        
        try:
            # حفظ الصورة
            saved_path, file_hash = self.save_image(file_obj, folder)
            
            # إنشاء URL مطلق
            file_url = default_storage.url(saved_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            duration_ms = int((time.time() - t0) * 1000)
            user_info = getattr(request.user, 'email', 'anonymous')
            
            logger.info(
                f"Image uploaded: user={user_info}, path={saved_path}, "
                f"size={file_obj.size}, hash={file_hash}, duration={duration_ms}ms"
            )
            
            return Response({
                'success': True,
                'image_url': absolute_url, 
                'url': absolute_url,
                'file_path': saved_path,
                'file_size': file_obj.size,
                'message': 'تم رفع الصورة بنجاح'
            }, status=201)
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return Response({'detail': f'فشل رفع الصورة: {str(e)}'}, status=500)


class ProductImageUploadView(BaseImageUploadView):
    """
    POST /api/v1/products/upload/image/
    رفع صور المنتجات - نسخة من Backend السابق
    """
    def post(self, request, *args, **kwargs):
        t0 = time.time()
        client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR')
        
        logger.info(f"Product image upload from {client_ip}")
        
        file_obj = request.FILES.get('image')
        folder = request.data.get('folder', 'products')
        
        # التحقق من صحة الصورة
        is_valid, error_msg = self.validate_image(file_obj)
        if not is_valid:
            return Response({'detail': error_msg}, status=400)
        
        try:
            # حفظ الصورة
            saved_path, file_hash = self.save_image(file_obj, folder)
            
            # إنشاء URL مطلق
            file_url = default_storage.url(saved_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            duration_ms = int((time.time() - t0) * 1000)
            user_info = getattr(request.user, 'email', 'anonymous')
            
            logger.info(
                f"Product image uploaded: user={user_info}, path={saved_path}, "
                f"size={file_obj.size}, hash={file_hash}, duration={duration_ms}ms"
            )
            
            return Response({
                'success': True,
                'image_url': absolute_url,
                'url': absolute_url,
                'file_path': saved_path,
                'file_size': file_obj.size,
                'message': 'تم رفع صورة المنتج بنجاح'
            }, status=201)
            
        except Exception as e:
            logger.error(f"Product image upload failed: {e}")
            return Response({'detail': f'فشل رفع صورة المنتج: {str(e)}'}, status=500)


class StoreImageUploadView(BaseImageUploadView):
    """
    POST /api/v1/stores/upload/image/
    رفع صور المتاجر
    """
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('image')
        
        # التحقق من صحة الصورة (3MB للمتاجر)
        is_valid, error_msg = self.validate_image(file_obj, max_size=3*1024*1024)
        if not is_valid:
            return Response({'detail': error_msg}, status=400)
        
        try:
            # حفظ الصورة
            saved_path, file_hash = self.save_image(file_obj, 'stores')
            
            # إنشاء URL مطلق
            file_url = default_storage.url(saved_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            logger.info(f"Store image uploaded: {saved_path}")
            
            return Response({
                'success': True,
                'image_url': absolute_url,
                'url': absolute_url,
                'file_path': saved_path,
                'file_size': file_obj.size,
                'message': 'تم رفع صورة المتجر بنجاح'
            }, status=201)
            
        except Exception as e:
            logger.error(f"Store image upload failed: {e}")
            return Response({'detail': f'فشل رفع صورة المتجر: {str(e)}'}, status=500)


class DeleteImageAPIView(APIView):
    """
    DELETE /api/v1/upload/image/delete/
    حذف صورة - نسخة من Backend السابق
    """
    permission_classes = [permissions.IsAuthenticated]  # ✅ تأمين - يجب المصادقة

    def delete(self, request, *args, **kwargs):
        image_url = request.data.get('image_url')
        if not image_url:
            return Response({'detail': 'image_url is required'}, status=400)

        try:
            from urllib.parse import urlparse
            parsed = urlparse(image_url)
            rel_path = parsed.path
            
            if rel_path.startswith(settings.MEDIA_URL):
                rel_path = rel_path[len(settings.MEDIA_URL):]

            full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Image deleted: {full_path}")
                return Response({'deleted': True, 'message': 'تم حذف الصورة بنجاح'}, status=200)
            
            return Response({'deleted': False, 'detail': 'الملف غير موجود'}, status=404)
            
        except Exception as e:
            logger.error(f"Delete image failed: {e}")
            return Response({'deleted': False, 'detail': str(e)}, status=400)


class ReplaceImageAPIView(BaseImageUploadView):
    """
    POST /api/v1/upload/image/replace/
    استبدال صورة - نسخة من Backend السابق
    """
    def post(self, request, *args, **kwargs):
        old_url = request.data.get('old_image_url', '')
        image = request.FILES.get('image')
        folder = request.data.get('folder', 'uploads')

        if not image:
            return Response({'detail': "حقل 'image' مطلوب"}, status=400)

        # حذف الصورة القديمة إن وُجدت
        if old_url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(old_url)
                rel_path = parsed.path
                if rel_path.startswith(settings.MEDIA_URL):
                    rel_path = rel_path[len(settings.MEDIA_URL):]
                full_path = os.path.join(settings.MEDIA_ROOT, rel_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"Old image deleted: {full_path}")
            except Exception as e:
                logger.warning(f"Failed to delete old image: {e}")
                # لا نفشل العملية إذا فشل حذف القديم

        # التحقق من صحة الصورة الجديدة
        is_valid, error_msg = self.validate_image(image)
        if not is_valid:
            return Response({'detail': error_msg}, status=400)

        try:
            # حفظ الصورة الجديدة
            saved_path, file_hash = self.save_image(image, folder)
            
            # إنشاء URL مطلق
            file_url = default_storage.url(saved_path)
            absolute_url = request.build_absolute_uri(file_url)
            
            logger.info(f"Image replaced: {saved_path}")
            
            return Response({
                'success': True,
                'image_url': absolute_url,
                'url': absolute_url,
                'file_path': saved_path,
                'message': 'تم استبدال الصورة بنجاح'
            }, status=201)
            
        except Exception as e:
            logger.error(f"Replace image failed: {e}")
            return Response({'detail': f'فشل استبدال الصورة: {str(e)}'}, status=500)
