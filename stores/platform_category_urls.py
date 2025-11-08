from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlatformCategoryViewSet

# إنشاء router للتصنيفات
router = DefaultRouter()
router.register(r'', PlatformCategoryViewSet, basename='platform-category')

urlpatterns = [
    path('', include(router.urls)),
]
