from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email
from django.utils import timezone
from accounts.models import User


class DeliveryProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='deliveryprofile')
    id_card_image = models.ImageField(_("صورة البطاقة"), upload_to='delivery/ids/')
    driver_license_image = models.ImageField(_("صورة رخصة القيادة"), upload_to='delivery/licenses/')
    vehicle_type = models.CharField(_("نوع المركبة"), max_length=50)
    # new
    city = models.CharField(_("المدينة"), max_length=50,default='إب')
    class DeliveryState(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'available'
        UNAVAILABLE = 'UNAVAILABLE', 'unavailable'
        INTASK= 'INTASK', 'inTask'
        # SUSPENDED = 'SUSPENDED', 'suspended'
    delivery_state = models.CharField(
        _("حالة الموصل"),
        max_length=20,
        choices=DeliveryState.choices,
        default=DeliveryState.UNAVAILABLE,
    )
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    verification_status = models.CharField(
        _("حالة التحقق"),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    suspended = models.BooleanField(_("موقوف مؤقتاً"), default=False)
    last_seen_at = models.DateTimeField(_("آخر ظهور"), null=True, blank=True)
    current_latitude = models.DecimalField(_("خط العرض الحالي"), max_digits=10, decimal_places=8, null=True, blank=True)
    current_longitude = models.DecimalField(_("خط الطول الحالي"), max_digits=11, decimal_places=8, null=True, blank=True)
    location_updated_at = models.DateTimeField(_("آخر تحديث للموقع"), null=True, blank=True)

    class Meta:
        verbose_name = _("موصل")
        verbose_name_plural = _("الموصلين")

    def __str__(self):
        return self.user.email


