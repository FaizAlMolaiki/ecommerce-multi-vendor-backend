# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError
# from django.contrib.auth import get_user_model

# User = get_user_model()


# class UserForm(forms.ModelForm):
#     """نموذج إضافة وتعديل المستخدمين"""
    
#     password1 = forms.CharField(
#         label='كلمة المرور',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'أدخل كلمة المرور',
#             'autocomplete': 'new-password'
#         }),
#         help_text='يجب أن تحتوي على 8 حروف على الأقل',
#         required=False
#     )
    
#     password2 = forms.CharField(
#         label='تأكيد كلمة المرور',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'أعد إدخال كلمة المرور',
#             'autocomplete': 'new-password'
#         }),
#         required=False
#     )
    
#     class Meta:
#         model = User
#         fields = ['name', 'email', 'phone_number', 'is_active', 'is_staff', 'is_vendor', 'is_delivery', 'is_verified']
#         widgets = {
#             'name': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'أدخل الاسم الكامل'
#             }),
#             'email': forms.EmailInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'أدخل البريد الإلكتروني'
#             }),
#             'phone_number': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'أدخل رقم الهاتف'
#             }),
#             'is_active': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'is_staff': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'is_vendor': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'is_delivery': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'is_verified': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#         }
#         labels = {
#             'name': 'الاسم الكامل',
#             'email': 'البريد الإلكتروني',
#             'phone_number': 'رقم الهاتف',
#             'is_active': 'مفعل',
#             'is_staff': 'موظف',
#             'is_vendor': 'بائع',
#             'is_delivery': 'مندوب توصيل',
#             'is_verified': 'تم التحقق من البريد',
#         }
#         help_texts = {
#             'name': 'اسم المستخدم الكامل (اختياري)',
#             'email': 'عنوان البريد الإلكتروني (مطلوب وفريد)',
#             'is_active': 'هل الحساب مفعل؟',
#             'is_staff': 'هل يمكنه الوصول للوحة الإدارة؟',
#             'is_vendor': 'هل هو بائع في المنصة؟',
#             'is_delivery': 'هل هو مندوب توصيل؟',
#             'is_verified': 'هل تم التحقق من البريد الإلكتروني؟',
#         }

#     def __init__(self, *args, **kwargs):
#         self.is_edit = kwargs.pop('is_edit', False)
#         super().__init__(*args, **kwargs)
        
#         # إذا كان تعديل، اجعل كلمة المرور اختيارية
#         if self.is_edit:
#             self.fields['password1'].help_text = 'اتركه فارغاً إذا كنت لا تريد تغيير كلمة المرور'
#             self.fields['password2'].help_text = 'أعد إدخال كلمة المرور الجديدة'
#         else:
#             # إذا كان إضافة، اجعل كلمة المرور مطلوبة
#             self.fields['password1'].required = True
#             self.fields['password2'].required = True

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if email:
#             email = email.lower().strip()
#             # تحقق من عدم وجود البريد مسبقاً (إلا إذا كان نفس المستخدم في حالة التعديل)
#             existing_user = User.objects.filter(email=email).first()
#             if existing_user and existing_user != self.instance:
#                 raise ValidationError('هذا البريد الإلكتروني مسجل مسبقاً')
#         return email

#     def clean_password1(self):
#         password1 = self.cleaned_data.get('password1')
#         if password1:
#             try:
#                 validate_password(password1)
#             except ValidationError as e:
#                 raise ValidationError(e.messages)
#         elif not self.is_edit:
#             raise ValidationError('كلمة المرور مطلوبة للمستخدمين الجدد')
#         return password1

#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
        
#         if password1 and password2:
#             if password1 != password2:
#                 raise ValidationError('كلمتا المرور غير متطابقتين')
#         elif password1 and not password2:
#             raise ValidationError('يرجى تأكيد كلمة المرور')
#         elif not password1 and password2:
#             raise ValidationError('يرجى إدخال كلمة المرور أولاً')
            
#         return password2

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         password = self.cleaned_data.get('password1')
        
#         if password:
#             user.set_password(password)
        
#         if commit:
#             user.save()
#         return user


# class UserDeleteForm(forms.Form):
#     """نموذج تأكيد حذف المستخدم"""
    
#     confirm_delete = forms.BooleanField(
#         label='أؤكد أنني أريد حذف هذا المستخدم نهائياً',
#         required=True,
#         widget=forms.CheckboxInput(attrs={
#             'class': 'form-check-input'
#         }),
#         error_messages={
#             'required': 'يجب تأكيد الحذف للمتابعة'
#         }
#     )

#     def __init__(self, user, *args, **kwargs):
#         self.user = user
#         super().__init__(*args, **kwargs)

#     def clean_confirm_delete(self):
#         confirmed = self.cleaned_data.get('confirm_delete')
#         if not confirmed:
#             raise ValidationError('يجب تأكيد الحذف للمتابعة')
#         return confirmed


# class UserPasswordResetForm(forms.Form):
#     """نموذج إعادة تعيين كلمة المرور"""
    
#     new_password1 = forms.CharField(
#         label='كلمة المرور الجديدة',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'أدخل كلمة المرور الجديدة',
#             'autocomplete': 'new-password'
#         }),
#         help_text='يجب أن تحتوي على 8 حروف على الأقل'
#     )
    
#     new_password2 = forms.CharField(
#         label='تأكيد كلمة المرور الجديدة',
#         widget=forms.PasswordInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'أعد إدخال كلمة المرور الجديدة',
#             'autocomplete': 'new-password'
#         })
#     )

#     def __init__(self, user, *args, **kwargs):
#         self.user = user
#         super().__init__(*args, **kwargs)

#     def clean_new_password1(self):
#         password = self.cleaned_data.get('new_password1')
#         if password:
#             try:
#                 validate_password(password, self.user)
#             except ValidationError as e:
#                 raise ValidationError(e.messages)
#         return password

#     def clean_new_password2(self):
#         password1 = self.cleaned_data.get('new_password1')
#         password2 = self.cleaned_data.get('new_password2')
        
#         if password1 and password2:
#             if password1 != password2:
#                 raise ValidationError('كلمتا المرور غير متطابقتين')
#         return password2

#     def save(self):
#         password = self.cleaned_data['new_password1']
#         self.user.set_password(password)
#         self.user.save()
#         return self.user

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
# from accounts.models import DeliveryProfile
from accounts.models import StaffProfile

User = get_user_model()


class UserForm(forms.ModelForm):
    """نموذج إضافة وتعديل المستخدمين"""
    
    # Optional DeliveryProfile fields (used only when is_delivery is checked)
    delivery_vehicle_type = forms.CharField(
        label='نوع المركبة (للمندوب)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: دراجة/سكوتر/سيارة'
        })
    )

    delivery_id_card_image = forms.ImageField(
        label='صورة البطاقة (للمندوب)',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    delivery_driver_license_image = forms.ImageField(
        label='صورة رخصة القيادة (للمندوب)',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

    # Optional StaffProfile fields (used only when is_staff is checked)
    staff_job_title = forms.CharField(
        label='المسمى الوظيفي (للموظف)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: مدير عمليات/دعم'
        })
    )
    staff_id_card_image = forms.ImageField(
        label='صورة البطاقة (للموظف)',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    staff_resume_cv = forms.FileField(
        label='السيرة الذاتية (للموظف)',
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control'
        })
    )

    password1 = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور',
            'autocomplete': 'new-password'
        }),
        help_text='يجب أن تحتوي على 8 حروف على الأقل',
        required=False
    )
    
    password2 = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور',
            'autocomplete': 'new-password'
        }),
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'name', 'email', 'phone_number',
            'is_active', 'is_staff', 'is_vendor', 'is_delivery', 'is_verified',
            # delivery fields are not model fields but included in the form for convenience
            'delivery_vehicle_type', 'delivery_id_card_image', 'delivery_driver_license_image',
            # staff fields (not model fields on User)
            'staff_job_title', 'staff_id_card_image', 'staff_resume_cv',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل الاسم الكامل'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل البريد الإلكتروني'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل رقم الهاتف'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_staff': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_vendor': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_delivery': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_verified': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'phone_number': 'رقم الهاتف',
            'is_active': 'مفعل',
            'is_staff': 'موظف',
            'is_vendor': 'بائع',
            'is_delivery': 'مندوب توصيل',
            'is_verified': 'تم التحقق من البريد',
            'delivery_vehicle_type': 'نوع المركبة (للمندوب)',
            'delivery_id_card_image': 'صورة البطاقة (للمندوب)',
            'delivery_driver_license_image': 'صورة رخصة القيادة (للمندوب)',
            'staff_job_title': 'المسمى الوظيفي (للموظف)',
            'staff_id_card_image': 'صورة البطاقة (للموظف)',
            'staff_resume_cv': 'السيرة الذاتية (للموظف)',
        }
        help_texts = {
            'name': 'اسم المستخدم الكامل (اختياري)',
            'email': 'عنوان البريد الإلكتروني (مطلوب وفريد)',
            'is_active': 'هل الحساب مفعل؟',
            'is_staff': 'هل يمكنه الوصول للوحة الإدارة؟',
            'is_vendor': 'هل هو بائع في المنصة؟',
            'is_delivery': 'هل هو مندوب توصيل؟',
            'is_verified': 'هل تم التحقق من البريد الإلكتروني؟',
            'delivery_vehicle_type': 'يستخدم فقط إذا كان المستخدم مندوب توصيل',
            'delivery_id_card_image': 'اختياري، يمكن توفيره لاحقاً',
            'delivery_driver_license_image': 'اختياري، يمكن توفيره لاحقاً',
            'staff_job_title': 'يستخدم فقط إذا كان المستخدم موظفاً',
            'staff_id_card_image': 'اختياري، يمكن توفيره لاحقاً',
            'staff_resume_cv': 'اختياري، يمكن توفيره لاحقاً',
        }

    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        # إذا كان تعديل، اجعل كلمة المرور اختيارية
        if self.is_edit:
            self.fields['password1'].help_text = 'اتركه فارغاً إذا كنت لا تريد تغيير كلمة المرور'
            self.fields['password2'].help_text = 'أعد إدخال كلمة المرور الجديدة'
        else:
            # إذا كان إضافة، اجعل كلمة المرور مطلوبة
            self.fields['password1'].required = True
            self.fields['password2'].required = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            # تحقق من عدم وجود البريد مسبقاً (إلا إذا كان نفس المستخدم في حالة التعديل)
            existing_user = User.objects.filter(email=email).first()
            if existing_user and existing_user != self.instance:
                raise ValidationError('هذا البريد الإلكتروني مسجل مسبقاً')
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            try:
                validate_password(password1)
            except ValidationError as e:
                raise ValidationError(e.messages)
        elif not self.is_edit:
            raise ValidationError('كلمة المرور مطلوبة للمستخدمين الجدد')
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('كلمتا المرور غير متطابقتين')
        elif password1 and not password2:
            raise ValidationError('يرجى تأكيد كلمة المرور')
        elif not password1 and password2:
            raise ValidationError('يرجى إدخال كلمة المرور أولاً')
            
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class UserDeleteForm(forms.Form):
    """نموذج تأكيد حذف المستخدم"""
    
    confirm_delete = forms.BooleanField(
        label='أؤكد أنني أريد حذف هذا المستخدم نهائياً',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'يجب تأكيد الحذف للمتابعة'
        }
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_confirm_delete(self):
        confirmed = self.cleaned_data.get('confirm_delete')
        if not confirmed:
            raise ValidationError('يجب تأكيد الحذف للمتابعة')
        return confirmed


class UserPasswordResetForm(forms.Form):
    """نموذج إعادة تعيين كلمة المرور"""
    
    new_password1 = forms.CharField(
        label='كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور الجديدة',
            'autocomplete': 'new-password'
        }),
        help_text='يجب أن تحتوي على 8 حروف على الأقل'
    )
    
    new_password2 = forms.CharField(
        label='تأكيد كلمة المرور الجديدة',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور الجديدة',
            'autocomplete': 'new-password'
        })
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            try:
                validate_password(password, self.user)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('كلمتا المرور غير متطابقتين')
        return password2

    def save(self):
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user


# # ---------------------- DeliveryProfile Forms ----------------------
# class DeliveryProfileForm(forms.ModelForm):
#     class Meta:
#         model = DeliveryProfile
#         fields = [
#             'id_card_image',
#             'driver_license_image',
#             'vehicle_type',
#             'verification_status',
#             'suspended',
#         ]
#         widgets = {
#             'id_card_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
#             'driver_license_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
#             'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع المركبة'}),
#             'verification_status': forms.Select(attrs={'class': 'form-select'}),
#             'suspended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }
#         labels = {
#             'id_card_image': 'صورة البطاقة',
#             'driver_license_image': 'صورة رخصة القيادة',
#             'vehicle_type': 'نوع المركبة',
#             'verification_status': 'حالة التحقق',
#             'suspended': 'موقوف مؤقتاً',
#         }


# class DeliveryProfileDeleteForm(forms.Form):
#     confirm = forms.BooleanField(
#         label='أؤكد حذف ملف المندوب نهائياً',
#         required=True,
#         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         error_messages={'required': 'يجب تأكيد الحذف للمتابعة'}
#     )


# ---------------------- StaffProfile Forms ----------------------
class StaffProfileForm(forms.ModelForm):
    class Meta:
        model = StaffProfile
        fields = [
            'id_card_image',
            'resume_cv',
            'job_title',
        ]
        widgets = {
            'id_card_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'resume_cv': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المسمى الوظيفي'}),
        }
        labels = {
            'id_card_image': 'صورة البطاقة',
            'resume_cv': 'السيرة الذاتية',
            'job_title': 'المسمى الوظيفي',
        }


class StaffProfileDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label='أؤكد حذف ملف الموظف نهائياً',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'يجب تأكيد الحذف للمتابعة'}
    )
