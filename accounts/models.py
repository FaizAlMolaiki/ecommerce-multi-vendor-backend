from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email

class CustomUserManager(BaseUserManager):
    def _validate_email(self, email):
        """تحقق من صحة البريد الإلكتروني وتطبيع قيمته"""
        try:
            validate_email(email)
            return self.normalize_email(email)
        except ValidationError:
            raise ValidationError({'email': _('يرجى إدخال عنوان بريد إلكتروني صحيح')})

    def _validate_password(self, password):
        """تحقق من قوة كلمة المرور باستخدام معايير أمان قوية"""
        if len(password) < 8:
            raise ValidationError({'password': _('يجب أن تحتوي كلمة المرور على 8 حرفًا على الأقل')})
        


    def create_user(self, email, password=None, **extra_fields):
        """
        إنشاء مستخدم عادي مع تطبيق شروط التحقق القوية
        """
        # تحقق من البريد الإلكتروني
        email = self._validate_email(email)
        
        # التحقق من كلمة المرور
        if password:
            self._validate_password(password)
        else:
            raise ValidationError({'password': _('يجب تعيين كلمة مرور')})
        
        # إنشاء المستخدم
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        إنشاء مستخدم مع صلاحيات المشرف العام
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValidationError({'is_staff': _('يجب أن يتمتع المشرف العام بصلاحيات فريق العمل')})
        
        if extra_fields.get('is_superuser') is not True:
            raise ValidationError({'is_superuser': _('يجب أن يتمتع المشرف العام بصلاحيات المشرف العام')})

        return self.create_user(email, password, **extra_fields)



class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(
        _("الاسم الكامل"),
        max_length=50,
        blank=False,
        null=False,
        help_text=_("ادخل اسمك الكامل (اختياري)")
    )
    
    email = models.EmailField(
        _("البريد الإلكتروني"),
        unique=True,
        db_index=True,
        error_messages={
            'unique': _("هذا البريد الإلكتروني مسجل مسبقًا.")
        }
    )
    
    
    phone_number = models.CharField(
        _("رقم الهاتف"),
        max_length=15,
        unique=True,
        null=True ,
        blank=True,
        db_index=True,
        error_messages={
            'unique': _("هذا الرقم مسجل مسبقًا.")
        }
    )
    created_at= models.DateTimeField(
        _("تاريخ الانضمام"),
        auto_now_add=True
    )
    
    last_login = models.DateTimeField(
        _("آخر تسجيل دخول"),
        auto_now=True
    )
    
    is_staff = models.BooleanField(
        _("عضو فريق العمل"),
        default=False,
        help_text=_("يحدد ما إذا كان المستخدم يمكنه الوصول لوحة الإدارة.")
    )
    
    is_active = models.BooleanField(
        _("نشط"),
        default=True,
        help_text=_("يحدد ما إذا كان الحساب مفعلاً. يمكنك إلغاء التفعيل بدل الحذف.")
    )
    
    is_vendor = models.BooleanField(
        _("بائع"),
        default=False,
    )
    is_delivery = models.BooleanField(
        _("موصل"),
        default=False,
    )
    
    is_verified = models.BooleanField(
        _("تم التحقق"),
        default=False,
        help_text=_("يحدد ما إذا كان البريد الإلكتروني تم التحقق منه.")
    )
    profile_bg=models.ImageField(upload_to="accounts/profile/%Y/%m/%d/",null=True,blank=True)    
    # الحقول المطلوبة للنظام
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمون")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.name})" if self.name else self.email

    def get_full_name(self):
        return self.name.strip() or self.email

    def get_short_name(self):
        return self.name.split()[0] if self.name else self.email.split('@')[0]

    def clean(self):
        """تنظيف البيانات قبل الحفظ"""
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)






# class DeliveryProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='deliveryprofile')
#     id_card_image = models.ImageField(_("صورة البطاقة"), upload_to='delivery/ids/')
#     driver_license_image = models.ImageField(_("صورة رخصة القيادة"), upload_to='delivery/licenses/')
#     vehicle_type = models.CharField(_("نوع المركبة"), max_length=50)
    
#     class VerificationStatus(models.TextChoices):
#         PENDING = 'PENDING', 'Pending'
#         APPROVED = 'APPROVED', 'Approved'
#         REJECTED = 'REJECTED', 'Rejected'

#     verification_status = models.CharField(
#         _("حالة التحقق"),
#         max_length=20,
#         choices=VerificationStatus.choices,
#         default=VerificationStatus.PENDING,
#     )
#     suspended = models.BooleanField(_("موقوف مؤقتاً"), default=False)
#     last_seen_at = models.DateTimeField(_("آخر ظهور"), null=True, blank=True)
#     current_latitude = models.DecimalField(_("خط العرض الحالي"), max_digits=10, decimal_places=8, null=True, blank=True)
#     current_longitude = models.DecimalField(_("خط الطول الحالي"), max_digits=11, decimal_places=8, null=True, blank=True)
#     location_updated_at = models.DateTimeField(_("آخر تحديث للموقع"), null=True, blank=True)

#     class Meta:
#         verbose_name = _("موصل")
#         verbose_name_plural = _("الموصلين")

#     def __str__(self):
#         return self.user.email


class StaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='staffprofile')
    id_card_image = models.ImageField(_("صورة البطاقة"), upload_to='staff/ids/')
    resume_cv = models.FileField(_("السيرة الذاتية"), upload_to='staff/cvs/')
    job_title = models.CharField(_("المسمى الوظيفي"), max_length=100)  

    class Meta:
        verbose_name = _("موظف")
        verbose_name_plural = _("الموظفين") 
    
    def __str__(self):
        return self.user.email

class UserAddress(models.Model):
    """
    Stores multiple shipping addresses for a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=100, help_text="e.g., Home, Work")
#    // phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Contact phone number")
    city = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    landmark = models.CharField(max_length=255, blank=True, null=True, help_text="Nearest landmark")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "User Addresses"
        ordering = ['-is_default']

    def __str__(self):
        user_label = getattr(self.user, 'email', None) or str(self.user_id)
        return f"{user_label}'s {self.label} Address"