
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import DeliveryProfile
# ---------------------- DeliveryProfile Forms ----------------------
class DeliveryProfileForm(forms.ModelForm):
    class Meta:
        model = DeliveryProfile
        fields = [
            'id_card_image',
            'driver_license_image',
            'vehicle_type',
            'verification_status',
            'suspended',
        ]
        widgets = {
            'id_card_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'driver_license_image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'vehicle_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نوع المركبة'}),
            'verification_status': forms.Select(attrs={'class': 'form-select'}),
            'suspended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'id_card_image': 'صورة البطاقة',
            'driver_license_image': 'صورة رخصة القيادة',
            'vehicle_type': 'نوع المركبة',
            'verification_status': 'حالة التحقق',
            'suspended': 'موقوف مؤقتاً',
        }


class DeliveryProfileDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        label='أؤكد حذف ملف المندوب نهائياً',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'يجب تأكيد الحذف للمتابعة'}
    )

