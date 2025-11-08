from django.urls import path
from .image_upload_views import (
    UploadImageView,
    DeleteImageAPIView,
    ReplaceImageAPIView
)

urlpatterns = [
    # مسارات الصور العامة - نسخة من Backend السابق
    path('image/', UploadImageView.as_view(), name='upload-image'),
    path('image/delete/', DeleteImageAPIView.as_view(), name='delete-image'),
    path('image/replace/', ReplaceImageAPIView.as_view(), name='replace-image'),
]
