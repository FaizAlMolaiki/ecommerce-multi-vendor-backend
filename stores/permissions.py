# from rest_framework.permissions import BasePermission

# # صلاحية مخصصة للتحقق مما إذا كان المستخدم هو مالك المتجر
# class IsOwnerOrReadOnly(BasePermission):

#     # هذه الدالة تتحقق من صلاحيات الوصول على مستوى الكائن
#     def has_object_permission(self, request, view, obj):
#         if request.method in ['GET', 'HEAD', 'OPTIONS']:
#             return True

#         # للطلبات التي تغير البيانات (PUT, PATCH, DELETE)، نتحقق إذا كان المستخدم هو المالك
#         return obj.owner == request.user

from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        print("Checking general permissions")
        # هذه الدالة يتم استدعاؤها لكل الطلبات
        if request.method not in permissions.SAFE_METHODS:
            print("Non-safe method, checking authentication")
            # إذا كان الطلب للكتابة، تحقق من تسجيل الدخول
            return request.user and request.user.is_authenticated
            print("User authenticated")
        return True # اسمح بطلبات القراءة

    def has_object_permission(self, request, view, obj):
        # هذه الدالة يتم استدعاؤها فقط للتفاصيل/التعديل/الحذف
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user
