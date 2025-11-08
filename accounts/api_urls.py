from django.urls import path, include
from .api_views import *
from .address_views import UserAddressViewSet
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,

)

# Router للـ Addresses API
router = DefaultRouter()
router.register(r'addresses', UserAddressViewSet, basename='address')

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyOTPView.as_view(), name='verify-email'),
    path('verify-reset-password-otp/', VerifyResetOTPView.as_view(),
         name='verify-reset-password-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('confirm-reset-password/', ConfirmResetView.as_view(),
         name='confirm-reset-password'),
    path('check-password/', CheckPasswordView.as_view(), name='check-password'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', TokenRefreshView.as_view(), name='refresh_token'),
    
    # Addresses API endpoints
    path('', include(router.urls)),
]