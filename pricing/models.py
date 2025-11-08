from django.db import models
from django.conf import settings
from django.utils import timezone

# استيراد العلاقات مع كينات المشروع
from stores.models import Store
from products.models import Product, ProductCategory, ProductVariant  # Category هي MPTT لديك

# ✅ =======================تعريف مشترك لحالات الموافقة=======================
class ApprovalStatus(models.TextChoices):
    """حالات الموافقة المشتركة لجميع العروض والكوبونات"""
    PENDING = "PENDING", "قيد المراجعة"
    APPROVED = "APPROVED", "موافق عليه"
    REJECTED = "REJECTED", "مرفوض"
# ============================================================================

class DiscountRuleBase(models.Model):
    """
    قاعدة مجردة تحتوي الحقول المشتركة لأي قاعدة تسعير (Promotion/Offer).
    ملاحظة: لا نضع حقول ManyToMany هنا (قيّد Django).
    """
    # اسم القاعدة (يظهر في الواجهات والتقارير)
    name = models.CharField(max_length=150)
    # NEW: Description and image for displaying in UI (matches Flutter OfferModel)
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='offers/', null=True, blank=True)
    
    # NEW: نظام الموافقة - الحالة الافتراضية هي "قيد المراجعة"
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        help_text="حالة الموافقة على العرض من قبل الإدارة"
    )
    
    # تاريخ الموافقة أو الرفض
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="تاريخ المراجعة")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_reviewed',
        help_text="المستخدم الذي قام بالمراجعة"
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        help_text="سبب الرفض (اختياري)"
    )
    active = models.BooleanField(default=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    # NEW: Timestamps for tracking creation and updates
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    min_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # أولوية التطبيق (الأصغر = أعلى أولوية)
    priority = models.PositiveIntegerField(default=100)

    # هل يمكن التكديس مع قواعد أخرى؟
    stackable = models.BooleanField(default=True)
    
    # ربط اختياري بكوبون محدد (إن وجد، تصبح القاعدة مشروطة بالكوبون)
    required_coupon = models.ForeignKey(
        'pricing.Coupon', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_rules'
    )

    class Meta:
        abstract = True
        ordering = ["priority", "id"]

    def is_within_time_window(self, when=None):
        now = when or timezone.now()
        if self.start_at and now < self.start_at:
            return False
        if self.end_at and now > self.end_at:
            return False
        return True


# الجزء الأول: موديل Coupon (كيان مستقل)

class Coupon(models.Model):
    """كوبون بسيط قابل لإعادة الاستخدام عبر قواعد متعددة."""
    code = models.CharField(max_length=64, unique=True)
     # NEW: نظام الموافقة
    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
        help_text="حالة الموافقة على الكوبون من قبل الإدارة"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="تاريخ المراجعة")
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coupon_reviewed',
        help_text="المستخدم الذي قام بالمراجعة"
    )
    rejection_reason = models.TextField(
        blank=True,
        default='',
        help_text="سبب الرفض (اختياري)"
    )
    # حالة وصلاحية الكوبون
    active = models.BooleanField(default=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)

    # حدود الاستخدام
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    limit_per_user = models.PositiveIntegerField(null=True, blank=True)
    
    # NEW: Timestamps for tracking creation and updates
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    # NEW: Many-to-many with stores for vendor-specific coupons
    stores = models.ManyToManyField(Store, blank=True, related_name="coupons")

    def __str__(self):
        return f"Coupon: {self.code}"


# الجزء الثاني: موديل Promotion

class Promotion(DiscountRuleBase):
    """خصومات تلقائية أو مشروطة بكوبون."""
    
    class PromotionType(models.TextChoices):
        PRODUCT_PERCENTAGE = "PRODUCT_PERCENTAGE", "نسبة مئوية على المنتجات"
        PRODUCT_FIXED_AMOUNT = "PRODUCT_FIXED_AMOUNT", "مبلغ ثابت على المنتجات"
        CART_PERCENTAGE = "CART_PERCENTAGE", "نسبة مئوية على السلة"
        CART_FIXED_AMOUNT = "CART_FIXED_AMOUNT", "مبلغ ثابت على السلة"

    promotion_type = models.CharField(max_length=25, choices=PromotionType.choices)
    value = models.DecimalField(max_digits=10, decimal_places=2)

    # نطاق التطبيق (فارغ = جميع المنصة)
    stores = models.ManyToManyField(Store, blank=True, related_name="promotions")
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name="promotions")
    products = models.ManyToManyField(Product, blank=True, related_name="promotions")
    variants = models.ManyToManyField(ProductVariant, blank=True, related_name="promotions")

    def __str__(self):
        return f"Promotion: {self.name}"


# الجزء الثالث: موديل Offer

class Offer(DiscountRuleBase):
    """عروض مشروطة مع منطق معقد."""
    
    class OfferType(models.TextChoices):
        BUY_X_GET_Y = "BUY_X_GET_Y", "اشتر X واحصل على Y"
        BUNDLE_FIXED_PRICE = "BUNDLE_FIXED_PRICE", "باقة بسعر ثابت"
        THRESHOLD_GIFT = "THRESHOLD_GIFT", "هدية عند مبلغ معين"
        THRESHOLD_FREE_SHIPPING = "THRESHOLD_FREE_SHIPPING", "شحن مجاني عند مبلغ معين"

    offer_type = models.CharField(max_length=32, choices=OfferType.choices)
    
    # إعدادات العرض بصيغة JSON
    configuration = models.JSONField(
        default=dict,
        help_text="إعدادات العرض حسب النوع، مثال: {'buy_quantity': 2, 'get_quantity': 1}"
    )

    # نطاق التطبيق
    stores = models.ManyToManyField(Store, blank=True, related_name="offers")
    categories = models.ManyToManyField(ProductCategory, blank=True, related_name="offers")
    products = models.ManyToManyField(Product, blank=True, related_name="offers")
    variants = models.ManyToManyField(ProductVariant, blank=True, related_name="offers")

    def __str__(self):
        return f"Offer: {self.name}"


# الجزء الرابع: موديل CouponRedemption

class CouponRedemption(models.Model):
    """تتبع استخدام الكوبونات لضمان حدود الاستخدام."""
    
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # منع استخدام نفس الكوبون أكثر من مرة في نفس الطلب
        unique_together = [('coupon', 'order')]
        ordering = ['-redeemed_at']

    def __str__(self):
        return f"{self.coupon.code} used by {self.user} on order #{self.order.id}"
