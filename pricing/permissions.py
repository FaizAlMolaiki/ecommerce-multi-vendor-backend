"""
Custom Permissions for Pricing Application
===========================================
يحتوي هذا الملف على جميع الصلاحيات المخصصة لتطبيق التسعير.
"""

from rest_framework.permissions import BasePermission
from stores.models import Store


class IsVendor(BasePermission):
    """
    صلاحية مخصصة للتحقق من أن المستخدم هو بائع (لديه متجر).
    
    يُستخدم في:
    - إنشاء عروض/كوبونات جديدة
    - تعديل العروض الخاصة بالبائع
    """
    
    def has_permission(self, request, view):
        """التحقق من أن المستخدم لديه متجر واحد على الأقل"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # التحقق من أن المستخدم لديه متجر
        return Store.objects.filter(owner=request.user).exists()


class IsObjectOwner(BasePermission):
    """
    صلاحية مخصصة للتحقق من أن المستخدم يملك الكائن.
    
    يعمل مع أي كائن له علاقة ManyToMany مع Store عبر حقل 'stores'.
    مناسب لـ: Promotion, Coupon, Offer
    
    يُستخدم في:
    - تعديل عرض/كوبون موجود
    - حذف عرض/كوبون
    - تفعيل/تعطيل عرض/كوبون
    """
    
    def has_object_permission(self, request, view, obj):
        """
        التحقق من أن الكائن مرتبط بأحد متاجر المستخدم.
        
        Args:
            request: HTTP request object
            view: ViewSet instance
            obj: الكائن المراد التحقق من ملكيته (Promotion/Coupon/Offer)
        
        Returns:
            bool: True إذا كان المستخدم يملك الكائن
        """
        # الحصول على كل المتاجر التي يملكها المستخدم
        user_stores = Store.objects.filter(owner=request.user)
        
        # التحقق مما إذا كان الكائن له حقل 'stores' (علاقة ManyToMany)
        if hasattr(obj, 'stores'):
            # التحقق مما إذا كان الكائن مرتبطاً بأي من متاجر المستخدم
            return obj.stores.filter(id__in=user_stores).exists()
        
        # إذا لم يكن للكائن حقل 'stores'، لا تسمح بالوصول كإجراء احترازي
        return False
