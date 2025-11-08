from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from wishlist.models import UserProductFavorite, UserStoreFavorite
from products.models import Product
from stores.models import Store

User = get_user_model()


class UserProductFavoriteForm(forms.ModelForm):
    """نموذج إضافة المنتجات المفضلة"""
    
    class Meta:
        model = UserProductFavorite
        fields = ['user', 'product']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'product': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
        labels = {
            'user': 'المستخدم',
            'product': 'المنتج'
        }
        help_texts = {
            'user': 'اختر المستخدم',
            'product': 'اختر المنتج المراد إضافته للمفضلة'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المستخدمين النشطين
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('email')
        
        # تحديد خيارات المنتجات
        self.fields['product'].queryset = Product.objects.select_related('store').order_by('name')
        
        # إضافة خيارات فارغة
        self.fields['user'].empty_label = "-- اختر المستخدم --"
        self.fields['product'].empty_label = "-- اختر المنتج --"

    def clean(self):
        """التحقق من عدم وجود تكرار"""
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        product = cleaned_data.get('product')
        
        if user and product:
            # التحقق من عدم وجود المنتج في مفضلة المستخدم مسبقاً
            if UserProductFavorite.objects.filter(user=user, product=product).exists():
                raise ValidationError('هذا المنتج موجود بالفعل في مفضلة هذا المستخدم')
        
        return cleaned_data


class UserStoreFavoriteForm(forms.ModelForm):
    """نموذج إضافة المتاجر المفضلة"""
    
    class Meta:
        model = UserStoreFavorite
        fields = ['user', 'store']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'store': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
        }
        labels = {
            'user': 'المستخدم',
            'store': 'المتجر'
        }
        help_texts = {
            'user': 'اختر المستخدم',
            'store': 'اختر المتجر المراد إضافته للمفضلة'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المستخدمين النشطين
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('email')
        
        # تحديد خيارات المتاجر النشطة
        self.fields['store'].queryset = Store.objects.filter(
            is_active=True
        ).order_by('name')
        
        # إضافة خيارات فارغة
        self.fields['user'].empty_label = "-- اختر المستخدم --"
        self.fields['store'].empty_label = "-- اختر المتجر --"

    def clean(self):
        """التحقق من عدم وجود تكرار"""
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        store = cleaned_data.get('store')
        
        if user and store:
            # التحقق من عدم وجود المتجر في مفضلة المستخدم مسبقاً
            if UserStoreFavorite.objects.filter(user=user, store=store).exists():
                raise ValidationError('هذا المتجر موجود بالفعل في مفضلة هذا المستخدم')
        
        return cleaned_data


class ProductFavoriteDeleteForm(forms.Form):
    """نموذج تأكيد حذف منتج من المفضلة"""
    confirm_delete = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='أؤكد رغبتي في حذف هذا المنتج من المفضلة'
    )


class StoreFavoriteDeleteForm(forms.Form):
    """نموذج تأكيد حذف متجر من المفضلة"""
    confirm_delete = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='أؤكد رغبتي في حذف هذا المتجر من المفضلة'
    )
