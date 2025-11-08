from django.contrib import admin

from .models import DeliveryProfile
@admin.register(DeliveryProfile)
class DeliveryProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'verification_status', 'suspended',
        'vehicle_type', 'last_seen_at',
        'current_latitude', 'current_longitude', 'location_updated_at'
    )
    list_filter = ('verification_status', 'suspended')
    search_fields = ('user__email', 'user__name')
