from django.db import models
from django.conf import settings
from django.utils import timezone

# كلاس تصنيف المتجر
class PlatformCategory(models.Model):
    # اسم التصنيف
    name = models.CharField(max_length=100, unique=True)
    # الصورة المرتبطة بالتصنيف
    image_url = models.URLField(max_length=500, blank=True)
    # هل التصنيف مميز للعرض في الواجهة
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Platform Categories"

    def __str__(self):
        return self.name


# ✅ نموذج موحد للمتاجر والطلبات
class Store(models.Model):
    """
    نموذج موحد للمتاجر - يدعم حالات مختلفة من الطلب إلى المتجر المعتمد
    """
    
    class StoreStatus(models.TextChoices):
        # حالات الطلب
        PENDING = 'pending', 'طلب قيد المراجعة'
        UNDER_REVIEW = 'under_review', 'تحت المراجعة'
        REJECTED = 'rejected', 'طلب مرفوض'
        
        # حالات المتجر
        APPROVED = 'approved', 'متجر معتمد'
        ACTIVE = 'active', 'متجر نشط'
        SUSPENDED = 'suspended', 'متجر موقوف'
        CLOSED = 'closed', 'متجر مغلق'
    
    # ===== البيانات الأساسية =====
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='stores',
        verbose_name="المالك"
    )
    
    # بيانات المتجر
    name = models.CharField(max_length=200, verbose_name="اسم المتجر")
    description = models.TextField(verbose_name="وصف المتجر")
    platform_category = models.ForeignKey(
        PlatformCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='stores',
        verbose_name="فئة المتجر"
    )
    
    # ===== حالة المتجر =====
    status = models.CharField(
        max_length=20,
        choices=StoreStatus.choices,
        default=StoreStatus.PENDING,
        verbose_name="حالة المتجر"
    )
    
    # ===== بيانات إضافية =====
    logo_url = models.URLField(max_length=500, blank=True, verbose_name="شعار المتجر")
    cover_image_url = models.URLField(max_length=500, blank=True, verbose_name="صورة الغلاف")
    phone_number = models.CharField(max_length=15, blank=True, verbose_name="رقم الهاتف")
    # email = models.EmailField(blank=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, verbose_name="العنوان")
    # website = models.URLField(blank=True, verbose_name="الموقع الإلكتروني")
    
    # المدينة (حقل نصي مفتوح - يستقبل من Flutter)
    city = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="المدينة",
        help_text="المدن يتم إدارتها من تطبيق Flutter"
    )
    
    # أوقات العمل
    opening_time = models.TimeField(null=True, blank=True, verbose_name="وقت الفتح")
    closing_time = models.TimeField(null=True, blank=True, verbose_name="وقت الإغلاق")
    
    # بيانات الطلب (للمتاجر في مرحلة الطلب)
    # business_license = models.CharField(
    #     max_length=100, 
    #     blank=True, 
    #     verbose_name="رقم الرخصة التجارية"
    # )
    
    # ===== ملاحظات الإدارة =====
    # admin_notes = models.TextField(
    #     blank=True, 
    #     verbose_name="ملاحظات الإدارة"
    # )
    
    # ===== التواريخ =====
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    
    # ===== إحصائيات الأداء (للمتاجر النشطة فقط) =====
    product_count = models.PositiveIntegerField(default=0, verbose_name="عدد المنتجات")
    average_rating = models.FloatField(default=0.0, verbose_name="متوسط التقييم")
    review_count = models.PositiveIntegerField(default=0, verbose_name="عدد التقييمات")
    favorites_count = models.PositiveIntegerField(default=0, verbose_name="عدد المفضلات")

    class Meta:
        verbose_name = "متجر"
        verbose_name_plural = "المتاجر"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['platform_category', 'status']),
            models.Index(fields=['status', 'approved_at']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"
    
    # ===== خصائص مساعدة =====
    @property
    def is_request(self):
        """هل هذا طلب متجر؟"""
        return self.status in [
            self.StoreStatus.PENDING, 
            self.StoreStatus.UNDER_REVIEW, 
            self.StoreStatus.REJECTED
        ]
    
    @property
    def is_active_store(self):
        """هل هذا متجر نشط؟"""
        return self.status in [
            self.StoreStatus.APPROVED, 
            self.StoreStatus.ACTIVE
        ]
    
    @property
    def can_sell(self):
        """هل يمكن للمتجر البيع؟"""
        return self.status == self.StoreStatus.ACTIVE
    
    @property
    def is_open_now(self):
        """هل المتجر مفتوح الآن؟"""
        if not self.opening_time or not self.closing_time:
            return True
        
        from django.utils import timezone
        current_time = timezone.now().time()
        
        if self.opening_time <= self.closing_time:
            return self.opening_time <= current_time <= self.closing_time
        else:
            return current_time >= self.opening_time or current_time <= self.closing_time
    
    # ===== دوال الإدارة =====
    def approve(self, admin_user=None, auto_activate=True):
        """الموافقة على طلب المتجر مع خيار التفعيل التلقائي"""
        if not self.is_request:
            raise ValueError("يمكن الموافقة على الطلبات فقط")
        
        # ✅ تفعيل تلقائي مباشرة أو موافقة فقط
        if auto_activate:
            self.status = self.StoreStatus.ACTIVE
        else:
            self.status = self.StoreStatus.APPROVED
        
        self.approved_at = timezone.now()
        self.reviewed_at = timezone.now()
        
        if admin_user:
            action = "وتم تفعيله" if auto_activate else ""
            self.admin_notes = f"تمت الموافقة {action} بواسطة: {admin_user.email}"
        
        # تحديث المستخدم ليصبح بائع
        self.owner.is_vendor = True
        self.owner.save()
        
        self.save()
        return self
    
    def reject(self, reason="", admin_user=None):
        """رفض طلب المتجر"""
        if not self.is_request:
            raise ValueError("يمكن رفض الطلبات فقط")
        
        self.status = self.StoreStatus.REJECTED
        self.reviewed_at = timezone.now()
        
        if reason:
            self.admin_notes = reason
        if admin_user:
            self.admin_notes += f"\nتم الرفض بواسطة: {admin_user.email}"
        
        self.save()
        return self
    
    def activate(self):
        """تفعيل المتجر المعتمد أو المتجر الموقوف"""
        if self.status not in [self.StoreStatus.APPROVED, self.StoreStatus.SUSPENDED]:
            raise ValueError("يمكن تفعيل المتاجر المعتمدة أو الموقوفة فقط")
        
        self.status = self.StoreStatus.ACTIVE
        self.save()
        return self
    
    def suspend(self, reason="", admin_user=None):
        """إيقاف المتجر مؤقتاً"""
        if not self.is_active_store:
            raise ValueError("يمكن إيقاف المتاجر النشطة فقط")
        
        self.status = self.StoreStatus.SUSPENDED
        
        # تحسين تسجيل سبب الإيقاف
        notes = f"تم الإيقاف في {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        if reason:
            notes += f" - السبب: {reason}"
        if admin_user:
            notes += f" - بواسطة: {admin_user.email}"
        
        self.admin_notes = notes
        self.save()
        return self
    
    def close(self, reason=""):
        """إغلاق المتجر نهائياً"""
        self.status = self.StoreStatus.CLOSED
        if reason:
            self.admin_notes = f"تم الإغلاق: {reason}"
        self.save()
        return self
    
    def toggle_status_by_owner(self):
        """
        تبديل حالة المتجر بين نشط ومغلق (للمالك فقط)
        لا يمكن للمالك تغيير حالة SUSPENDED
        """
        if self.status == self.StoreStatus.SUSPENDED:
            raise ValueError("المتجر موقوف من الإدارة. يرجى التواصل مع الدعم")
        
        if self.status == self.StoreStatus.ACTIVE:
            self.status = self.StoreStatus.CLOSED
            self.admin_notes = f"تم إغلاق المتجر بواسطة المالك في {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        elif self.status == self.StoreStatus.CLOSED:
            self.status = self.StoreStatus.ACTIVE
            self.admin_notes = f"تم إعادة فتح المتجر بواسطة المالك في {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        else:
            raise ValueError("لا يمكن تغيير حالة المتجر في الوضع الحالي")
        
        self.save()
        return self
    
    def get_status_history(self):
        """الحصول على تاريخ تغييرات حالة المتجر من admin_notes"""
        if not self.admin_notes:
            return []
        
        history = []
        lines = self.admin_notes.split('\n')
        for line in lines:
            if line.strip():
                history.append(line.strip())
        return history
    
    def can_owner_toggle(self):
        """هل يمكن للمالك تبديل حالة المتجر؟"""
        return self.status in [self.StoreStatus.ACTIVE, self.StoreStatus.CLOSED]
    
    def get_owner_actions(self):
        """الحصول على الإجراءات المتاحة للمالك"""
        actions = []
        
        if self.status == self.StoreStatus.ACTIVE:
            actions.append('close')  # إغلاق مؤقت
        elif self.status == self.StoreStatus.CLOSED:
            actions.append('reopen')  # إعادة فتح
        elif self.status == self.StoreStatus.SUSPENDED:
            actions.append('contact_support')  # التواصل مع الدعم
        
        return actions
    
    # ===== Manager مخصص =====
    @classmethod
    def get_requests(cls):
        """الحصول على طلبات المتاجر فقط"""
        return cls.objects.filter(
            status__in=[
                cls.StoreStatus.PENDING,
                cls.StoreStatus.UNDER_REVIEW,
                cls.StoreStatus.REJECTED
            ]
        )
    
    @classmethod
    def get_active_stores(cls):
        """الحصول على المتاجر النشطة فقط"""
        return cls.objects.filter(
            status__in=[
                cls.StoreStatus.APPROVED,
                cls.StoreStatus.ACTIVE
            ]
        )
    
    @classmethod
    def get_user_stores(cls, user):
        """الحصول على متاجر مستخدم معين"""
        return cls.objects.filter(owner=user)
    
    @classmethod
    def get_user_requests(cls, user):
        """الحصول على طلبات مستخدم معين"""
        return cls.get_requests().filter(owner=user)
    
    @classmethod
    def get_stores_by_city(cls, city):
        """الحصول على المتاجر حسب المدينة"""
        return cls.get_active_stores().filter(city=city)