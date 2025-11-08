from django import forms
from .models import PlatformCategory


class PlatformCategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل تصنيفات المتاجر"""
    
    class Meta:
        model = PlatformCategory
        fields = ['name', 'image_url']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم التصنيف (مثل: مطاعم، صيدليات، إلكترونيات)',
                'required': True
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط صورة التصنيف (اختياري)',
                'dir': 'ltr'
            })
        }
        labels = {
            'name': 'اسم التصنيف',
            'image_url': 'رابط الصورة'
        }
        help_texts = {
            'name': 'اسم التصنيف الرئيسي للمتاجر (مثل: مطاعم، صيدليات، إلكترونيات، أدوات منزلية)',
            'image_url': 'رابط صورة التصنيف (اختياري)'
        }

    def clean_name(self):
        """التحقق من صحة اسم التصنيف"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('اسم التصنيف يجب أن يكون أكثر من حرفين')
            if len(name) > 100:
                raise forms.ValidationError('اسم التصنيف يجب أن يكون أقل من 100 حرف')
        return name

    def clean_image_url(self):
        """التحقق من صحة رابط الصورة"""
        image_url = self.cleaned_data.get('image_url')
        if image_url:
            image_url = image_url.strip()
            if not image_url.startswith(('http://', 'https://')):
                raise forms.ValidationError('رابط الصورة يجب أن يبدأ بـ http:// أو https://')
        return image_url


class PlatformCategoryDeleteForm(forms.Form):
    """نموذج تأكيد حذف تصنيف المتجر"""
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirmDelete'
        }),
        label='أؤكد رغبتي في حذف هذا التصنيف نهائياً'
    )

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def clean_confirm(self):
        """التحقق من تأكيد الحذف"""
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise forms.ValidationError('يجب تأكيد الحذف للمتابعة')
        return confirm
