# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .api_views import (
#     PromotionViewSet,
#     CouponViewSet, 
#     OfferViewSet,
#     ApplyCouponView,
#     GetActivePromotionsView
# )

# router = DefaultRouter()
# router.register(r'promotions', PromotionViewSet, basename='promotion')
# router.register(r'coupons', CouponViewSet, basename='coupon')
# router.register(r'offers', OfferViewSet, basename='offer')

# urlpatterns = [
#     path('', include(router.urls)),
    
#     # Custom endpoints for pricing logic
#     path('apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
#     path('active-promotions/', GetActivePromotionsView.as_view(), name='active-promotions'),
# ]

# NEW: Updated API URLs for the new pricing system
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    PromotionViewSet,
    CouponViewSet, 
    OfferViewSet,
    CalculateCartView,  # NEW
    MyPromotionsView,  # NEW: Vendor management
    MyCouponsView,  # NEW: Vendor management
    MyOffersView,  # NEW: Vendor management
    CreatePromotionView,  # NEW: Create promotion
    CreateCouponView,  # NEW: Create coupon
    CreateOfferView,  # NEW: Create offer
    # OLD: ApplyCouponView,  # Removed - was broken
    # OLD: GetActivePromotionsView,  # Removed - functionality in PromotionViewSet
)

router = DefaultRouter()
router.register(r'promotions', PromotionViewSet, basename='promotion')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'offers', OfferViewSet, basename='offer')

urlpatterns = [
    # ⚠️ IMPORTANT: وضع الـ URLs المخصصة قبل router.urls لتجنب التعارض
    
    # NEW: Complete cart calculation with discounts
    path('calculate-cart/', CalculateCartView.as_view(), name='calculate-cart'),
    
    # NEW: Vendor Management - إدارة العروض والكوبونات للبائع
    # يجب أن تكون قبل router.urls لأن router يلتقط promotions/* و coupons/*
    path('promotions/my/', MyPromotionsView.as_view(), name='my-promotions'),
    path('promotions/create/', CreatePromotionView.as_view(), name='create-promotion'),
    path('coupons/my/', MyCouponsView.as_view(), name='my-coupons'),
    path('coupons/create/', CreateCouponView.as_view(), name='create-coupon'),
    path('offers/my/', MyOffersView.as_view(), name='my-offers'),
    path('offers/create/', CreateOfferView.as_view(), name='create-offer'),
    
    # Router URLs (يجب أن يكون بعد الـ URLs المخصصة)
    path('', include(router.urls)),
    
    # OLD: Broken endpoints (removed)
    # path('apply-coupon/', ApplyCouponView.as_view(), name='apply-coupon'),
    # path('active-promotions/', GetActivePromotionsView.as_view(), name='active-promotions'),
    
    # NOTE: Coupon validation is now at: /api/pricing/coupons/validate/
]
