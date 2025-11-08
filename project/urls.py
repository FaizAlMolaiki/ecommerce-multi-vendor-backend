from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from .admin_views import metrics_view
from .dashboard_views import dashboard_view
from orders.dashboard_orders import orders_list_view, order_detail_view, order_create_view, order_edit_view, order_delete_view, order_status_change_view
from orders.api_views import get_stores_api, get_products_by_store_api, get_product_variants_api
from products.dashboard_products import products_list_view, product_detail_view, product_create_view, product_edit_view, product_delete_view
from products.dashboard_categories import product_categories_list_view, product_category_create_view, product_category_edit_view, product_category_delete_view, product_category_detail_view, get_categories_by_store
from stores.dashboard_stores import stores_list_view, store_detail_view, store_create_view, store_edit_view, store_delete_view
from stores.dashboard_categories import platform_categories_list_view, platform_category_create_view, platform_category_edit_view, platform_category_delete_view, platform_category_detail_view
from accounts.dashboard_users import users_list_view, user_detail_view, user_create_view, user_edit_view, user_delete_view, user_password_reset_view
from reviews.dashboard_reviews import reviews_list_view
from wishlist.dashboard_wishlist import wishlist_list_view, product_favorite_create_view, store_favorite_create_view, product_favorite_delete_view, store_favorite_delete_view

# //
from driver.dashboard_delivery import (
    delivery_profiles_list_view,
    delivery_profile_create_view,
    delivery_profile_edit_view,
    delivery_profile_delete_view,
)
from accounts.dashboard_staff import (
    staff_profiles_list_view,
    staff_profile_create_view,
    staff_profile_edit_view,
    staff_profile_delete_view,
)
urlpatterns = [
    # Root redirect to dashboard
    path("", lambda request: redirect("dashboard")),
    
    # Put the specific metrics route BEFORE the admin catch-all route
    path('admin/metrics/', admin.site.admin_view(metrics_view), name='admin-metrics'),
    path('admin/', admin.site.urls),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/orders/', orders_list_view, name='dashboard-orders'),
    path('dashboard/orders/<int:order_id>/', order_detail_view, name='dashboard-order-detail'),
    path('dashboard/stores/', stores_list_view, name='dashboard-stores'),
    path('dashboard/stores/create/', store_create_view, name='dashboard-store-create'),
    path('dashboard/stores/<int:store_id>/', store_detail_view, name='dashboard-store-detail'),
    path('dashboard/stores/<int:store_id>/edit/', store_edit_view, name='dashboard-store-edit'),
    path('dashboard/stores/<int:store_id>/delete/', store_delete_view, name='dashboard-store-delete'),
    # Product CRUD URLs
    path('dashboard/products/create/', product_create_view, name='dashboard-product-create'),
    path('dashboard/products/<int:product_id>/edit/', product_edit_view, name='dashboard-product-edit'),
    path('dashboard/products/<int:product_id>/delete/', product_delete_view, name='dashboard-product-delete'),
    
    # User CRUD URLs
    path('dashboard/users/create/', user_create_view, name='dashboard-user-create'),
    path('dashboard/users/<int:user_id>/edit/', user_edit_view, name='dashboard-user-edit'),
    path('dashboard/users/<int:user_id>/delete/', user_delete_view, name='dashboard-user-delete'),
    path('dashboard/users/<int:user_id>/reset-password/', user_password_reset_view, name='dashboard-user-password-reset'),
    
    # Order CRUD URLs
    path('dashboard/orders/create/', order_create_view, name='dashboard-order-create'),
    path('dashboard/orders/<int:order_id>/edit/', order_edit_view, name='dashboard-order-edit'),
    path('dashboard/orders/<int:order_id>/delete/', order_delete_view, name='dashboard-order-delete'),
    path('dashboard/orders/<int:order_id>/status/', order_status_change_view, name='dashboard-order-status'),
    path('dashboard/products/', products_list_view, name='dashboard-products'),
    path('dashboard/products/<int:product_id>/', product_detail_view, name='dashboard-product-detail'),
    path('dashboard/users/', users_list_view, name='dashboard-users'),
    path('dashboard/users/<int:user_id>/', user_detail_view, name='dashboard-user-detail'),
    path('dashboard/reviews/', reviews_list_view, name='dashboard-reviews'),
    path('dashboard/wishlist/', wishlist_list_view, name='dashboard-wishlist'),
    path('dashboard/wishlist/product/create/', product_favorite_create_view, name='dashboard-product-favorite-create'),
    path('dashboard/wishlist/store/create/', store_favorite_create_view, name='dashboard-store-favorite-create'),
    path('dashboard/wishlist/product/<int:favorite_id>/delete/', product_favorite_delete_view, name='dashboard-product-favorite-delete'),
    path('dashboard/wishlist/store/<int:favorite_id>/delete/', store_favorite_delete_view, name='dashboard-store-favorite-delete'),
    # //
    # Delivery Profiles URLs
    path('dashboard/delivery-profiles/', delivery_profiles_list_view, name='dashboard-delivery-profiles'),
    path('dashboard/delivery-profiles/<int:user_id>/create/', delivery_profile_create_view, name='dashboard-delivery-profile-create'),
    path('dashboard/delivery-profiles/<int:user_id>/edit/', delivery_profile_edit_view, name='dashboard-delivery-profile-edit'),
    path('dashboard/delivery-profiles/<int:user_id>/delete/', delivery_profile_delete_view, name='dashboard-delivery-profile-delete'),
    
     # Staff Profiles URLs
    path('dashboard/staff-profiles/', staff_profiles_list_view, name='dashboard-staff-profiles'),
    path('dashboard/staff-profiles/<int:user_id>/create/', staff_profile_create_view, name='dashboard-staff-profile-create'),
    path('dashboard/staff-profiles/<int:user_id>/edit/', staff_profile_edit_view, name='dashboard-staff-profile-edit'),
    path('dashboard/staff-profiles/<int:user_id>/delete/', staff_profile_delete_view, name='dashboard-staff-profile-delete'),
    
    # Pricing URLs
    path('dashboard/pricing/', include('pricing.urls')),
    
    # Platform Categories URLs
    path('dashboard/platform-categories/', platform_categories_list_view, name='dashboard-platform-categories'),
    path('dashboard/platform-categories/create/', platform_category_create_view, name='dashboard-platform-category-create'),
    path('dashboard/platform-categories/<int:category_id>/', platform_category_detail_view, name='dashboard-platform-category-detail'),
    path('dashboard/platform-categories/<int:category_id>/edit/', platform_category_edit_view, name='dashboard-platform-category-edit'),
    path('dashboard/platform-categories/<int:category_id>/delete/', platform_category_delete_view, name='dashboard-platform-category-delete'),
    
    # Product Categories URLs
    path('dashboard/product-categories/', product_categories_list_view, name='dashboard-product-categories'),
    path('dashboard/product-categories/create/', product_category_create_view, name='dashboard-product-category-create'),
    path('dashboard/product-categories/<int:category_id>/', product_category_detail_view, name='dashboard-product-category-detail'),
    path('dashboard/product-categories/<int:category_id>/edit/', product_category_edit_view, name='dashboard-product-category-edit'),
    path('dashboard/product-categories/<int:category_id>/delete/', product_category_delete_view, name='dashboard-product-category-delete'),
    path('dashboard/api/categories-by-store/', get_categories_by_store, name='dashboard-categories-by-store'),
    
    # Dashboard API endpoints for order management
    path('dashboard/api/stores/', get_stores_api, name='dashboard-api-stores'),
    path('dashboard/api/products-by-store/', get_products_by_store_api, name='dashboard-api-products-by-store'),
    path('dashboard/api/product-variants/', get_product_variants_api, name='dashboard-api-product-variants'),
    
    # api
    path('api/v1/auth/', include('accounts.api_urls')),
    path('api/v1/stores/', include('stores.urls')),
    path('api/v1/products/', include('products.api_urls')),
    path('api/v1/', include('reviews.urls')),
    path('api/v1/orders/', include('orders.urls')),
    path('api/v1/wishlist/', include('wishlist.urls')),
    path('api/v1/pricing/', include('pricing.api_urls')),  # نظام التسعير الجديد
    path('api/v1/notifications/', include('notifications.api_urls')),  # نظام الإشعارات
     path('api/v1/driver/',include('driver.api_urls')),
    # مسار مباشر للتصنيفات المميزة
    path('api/v1/platform-categories/', include('stores.platform_category_urls')),
    
    # Image upload endpoints - نسخة من Backend السابق
    path('api/v1/upload/', include('core.image_urls')),
]


if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
    # Serve app static files (e.g., debug_toolbar) during development under Uvicorn/ASGI
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



    





 