from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Root redirect to promotions list
    path('', RedirectView.as_view(pattern_name='dashboard-promotions', permanent=False)),
    # Promotions URLs
    path('promotions/', views.promotions_list_view, name='dashboard-promotions'),
    path('promotions/create/', views.promotion_create_view, name='dashboard-promotion-create'),
    path('promotions/<int:promotion_id>/edit/', views.promotion_edit_view, name='dashboard-promotion-edit'),
    path('promotions/<int:promotion_id>/delete/', views.promotion_delete_view, name='dashboard-promotion-delete'),
    
    # Coupons URLs
    path('coupons/', views.coupons_list_view, name='dashboard-coupons'),
    path('coupons/create/', views.coupon_create_view, name='dashboard-coupon-create'),
    path('coupons/<int:coupon_id>/edit/', views.coupon_edit_view, name='dashboard-coupon-edit'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete_view, name='dashboard-coupon-delete'),
    
    # Offers URLs
    path('offers/', views.offers_list_view, name='dashboard-offers'),
    path('offers/create/', views.offer_create_view, name='dashboard-offer-create'),
    path('offers/<int:offer_id>/edit/', views.offer_edit_view, name='dashboard-offer-edit'),
    path('offers/<int:offer_id>/delete/', views.offer_delete_view, name='dashboard-offer-delete'),
]
