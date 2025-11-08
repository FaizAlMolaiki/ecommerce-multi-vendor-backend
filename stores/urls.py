from django.urls import path, include
from rest_framework.routers import DefaultRouter # استيراد DefaultRouter من Django REST framework
from .views import StoreViewSet, PlatformCategoryViewSet
from core.image_upload_views import StoreImageUploadView, UploadImageView, DeleteImageAPIView, ReplaceImageAPIView

router = DefaultRouter() # إنشاء راوتر جديد ، من أجل توجيه الطلبات إلى ال ViewSets المناسبة
router.register(r'stores', StoreViewSet, basename='store') # تسجيل ال ViewSet الخاص بالمتاجر
router.register(r'platform-categories', PlatformCategoryViewSet, basename='platform-category') # تسجيل ال ViewSet الخاص بتصنيفات المتاجر

# تعريف مسارات URL
urlpatterns = [
    path('', include(router.urls)), # تضمين مسارات الراوتر في المسارات العامة للتطبيق
    
    # Image upload endpoints - نسخة من Backend السابق
    path('upload/image/', StoreImageUploadView.as_view(), name='store-upload-image'),
] 
