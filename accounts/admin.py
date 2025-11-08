from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from driver.models import DeliveryProfile

from .models import User, UserAddress, StaffProfile

class UserAddressInline(admin.TabularInline):
    model = UserAddress
    extra = 0
    fields = ('label', 'city', 'street', 'is_default')
    show_change_link = True


class UserAdmin(BaseUserAdmin):
    ordering = ('-created_at',)
    list_display = (
        'id', 'email', 'name', 'phone_number',
        'is_verified', 'is_active', 'is_staff', 'is_vendor', 'is_delivery', 'created_at'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'is_vendor', 'is_delivery', 'created_at')
    search_fields = ('email', 'name', 'phone_number')
    readonly_fields = ('last_login', 'created_at')
    inlines = [UserAddressInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'phone_number', 'profile_bg')}),
        ('Permissions', {'fields': (
            'is_active', 'is_staff', 'is_superuser',
            'is_verified', 'is_vendor', 'is_delivery',
            'groups', 'user_permissions'
        )}),
        ('Important dates', {'fields': ('last_login', 'created_at')}),
    )

    # تمكين إنشاء مستخدم جديد من لوحة الإدارة باستخدام البريد وكلمتين للمرور
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2', 'name', 'phone_number',
                'is_active', 'is_staff', 'is_superuser', 'is_verified', 'is_vendor', 'is_delivery',
                'groups', 'user_permissions'
            ),
        }),
    )


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'label', 'city', 'street', 'is_default')
    list_filter = ('is_default', 'city')
    search_fields = ('user__email', 'label', 'city', 'street')


# @admin.register(DeliveryProfile)
# class DeliveryProfileAdmin(admin.ModelAdmin):
#     list_display = (
#         'user', 'verification_status', 'suspended',
#         'vehicle_type', 'last_seen_at',
#         'current_latitude', 'current_longitude', 'location_updated_at'
#     )
#     list_filter = ('verification_status', 'suspended')
#     search_fields = ('user__email', 'user__name')


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job_title')
    search_fields = ('user__email', 'user__name', 'job_title')


admin.site.register(User, UserAdmin)