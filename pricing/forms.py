from django import forms
from .models import Promotion, Coupon, Offer


class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = [
            'name', 'active', 'start_at', 'end_at', 'min_purchase_amount', 'priority', 'stackable',
            'required_coupon',
            'promotion_type', 'value',
            'stores', 'categories', 'products', 'variants',
        ]

    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value is not None and value < 0:
            raise forms.ValidationError("قيمة الخصم يجب أن تكون موجبة")
        return value


class PromotionDeleteForm(forms.Form):
    confirm = forms.BooleanField(label="تأكيد الحذف", required=True)


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            'code', 'active', 'start_at', 'end_at',
            'usage_limit', 'limit_per_user',
        ]

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper().strip()
        return code


class CouponDeleteForm(forms.Form):
    confirm = forms.BooleanField(label="تأكيد الحذف", required=True)


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            'name', 'active', 'start_at', 'end_at', 'min_purchase_amount', 'priority', 'stackable',
            'required_coupon',
            'offer_type', 'configuration',
            'stores', 'categories', 'products', 'variants',
        ]

    def clean_min_purchase_amount(self):
        amount = self.cleaned_data.get('min_purchase_amount')
        if amount is not None and amount < 0:
            raise forms.ValidationError("الحد الأدنى للمبلغ يجب أن يكون موجباً")
        return amount


class OfferDeleteForm(forms.Form):
    confirm = forms.BooleanField(label="تأكيد الحذف", required=True)
