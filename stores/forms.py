from django import forms
from django.contrib.auth import get_user_model
from stores.models import Store, PlatformCategory

User = get_user_model()

class StoreForm(forms.ModelForm):
    """نموذج إضافة وتعديل المتاجر"""
    
    class Meta:
        model = Store
        fields = ['owner', 'platform_category', 'name', 'description', 'logo_url', 'city', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المتجر',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'وصف المتجر (اختياري)'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط شعار المتجر (اختياري)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'المدينة'
            }),
            'owner': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'platform_category': forms.Select(attrs={
                'class': 'form-select',
                'required': False
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'owner': 'مالك المتجر',
            'platform_category': 'التصنيف',
            'name': 'اسم المتجر',
            'description': 'الوصف',
            'logo_url': 'رابط الشعار',
            'city': 'المدينة',
            'status': 'حالة المتجر'
        }
        help_texts = {
            'owner': 'اختر المستخدم الذي سيملك هذا المتجر',
            'platform_category': 'اختر تصنيف المتجر (اختياري)',
            'name': 'اسم المتجر كما سيظهر للعملاء',
            'description': 'وصف مختصر عن المتجر ومنتجاته',
            'logo_url': 'رابط مباشر لشعار المتجر',
            'city': 'المدينة التي يقع فيها المتجر',
            'status': 'حالة المتجر (pending, active, suspended, etc.)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المالكين (البائعين فقط)
        self.fields['owner'].queryset = User.objects.filter(
            is_vendor=True, 
            is_active=True
        ).order_by('email')
        
        # تحديد خيارات التصنيفات
        self.fields['platform_category'].queryset = PlatformCategory.objects.all().order_by('name')
        
        # إضافة خيار فارغ للتصنيف
        self.fields['platform_category'].empty_label = "-- اختر التصنيف --"
        
        # إضافة خيار فارغ للمالك
        self.fields['owner'].empty_label = "-- اختر المالك --"

    def clean_name(self):
        """التحقق من اسم المتجر"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('اسم المتجر يجب أن يكون حرفين على الأقل')
            if len(name) > 200:
                raise forms.ValidationError('اسم المتجر طويل جداً (الحد الأقصى 200 حرف)')
        return name

    def clean_logo_url(self):
        """التحقق من رابط الشعار"""
        logo_url = self.cleaned_data.get('logo_url')
        if logo_url:
            logo_url = logo_url.strip()
            if not logo_url.startswith(('http://', 'https://')):
                raise forms.ValidationError('رابط الشعار يجب أن يبدأ بـ http:// أو https://')
        return logo_url

    def clean(self):
        """التحقق العام من النموذج"""
        cleaned_data = super().clean()
        owner = cleaned_data.get('owner')
        name = cleaned_data.get('name')
        
        # التحقق من عدم وجود متجر بنفس الاسم لنفس المالك
        if owner and name and not self.instance.pk:
            existing_store = Store.objects.filter(owner=owner, name=name).first()
            if existing_store:
                raise forms.ValidationError(
                    f'يوجد متجر بنفس الاسم "{name}" لنفس المالك "{owner.email}"'
                )
        
        return cleaned_data


class StoreDeleteForm(forms.Form):
    """نموذج تأكيد حذف المتجر"""
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='أؤكد رغبتي في حذف هذا المتجر نهائياً',
        help_text='تحذير: هذا الإجراء لا يمكن التراجع عنه'
    )
    
    def __init__(self, store, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        
    def clean_confirm(self):
        """التحقق من التأكيد"""
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise forms.ValidationError('يجب تأكيد الحذف')
        return confirm
