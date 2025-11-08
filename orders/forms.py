from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from orders.models import Order, OrderItem
from stores.models import Store

User = get_user_model()


class OrderForm(forms.ModelForm):
    """نموذج إضافة وتعديل الطلبات"""
    
    class Meta:
        model = Order
        fields = ['store', 'user', 'delivery_agent', 'grand_total', 'delivery_fee', 'shipping_address_snapshot', 'payment_status', 'fulfillment_status']
        widgets = {
            'store': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'user': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'delivery_agent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'grand_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'إجمالي المبلغ'
            }),
            'delivery_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'رسوم التوصيل (اختياري)'
            }),
            'shipping_address_snapshot': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'عنوان الشحن (JSON)'
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fulfillment_status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'store': 'المتجر',
            'user': 'العميل',
            'delivery_agent': 'مندوب التوصيل (اختياري)',
            'grand_total': 'إجمالي المبلغ',
            'delivery_fee': 'رسوم التوصيل',
            'shipping_address_snapshot': 'عنوان الشحن',
            'payment_status': 'حالة الدفع',
            'fulfillment_status': 'حالة التجهيز/التسليم'
        }
        help_texts = {
            'store': 'اختر المتجر المرتبط بهذا الطلب',
            'user': 'اختر العميل صاحب الطلب',
            'delivery_agent': 'يمكن تعيين المندوب لاحقاً من لوحة التحكم (اختياري عند الإنشاء)',
            'grand_total': 'إجمالي قيمة الطلب بالعملة المحلية',
            'delivery_fee': 'رسوم التوصيل الافتراضية 0.00 ويمكن تعديلها هنا',
            'shipping_address_snapshot': 'عنوان الشحن بصيغة JSON',
            'payment_status': 'حالة الدفع الحالية',
            'fulfillment_status': 'حالة تجهيز/تسليم الطلب'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المتاجر
        self.fields['store'].queryset = Store.objects.order_by('name')
        self.fields['store'].empty_label = "-- اختر المتجر --"

        # تحديد خيارات العملاء
        self.fields['user'].queryset = User.objects.filter(
            is_active=True
        ).order_by('email')
        
        # إضافة خيار فارغ للعميل
        self.fields['user'].empty_label = "-- اختر العميل --"

        # تحديد خيارات مندوبي التوصيل (اختياري)
        if 'delivery_agent' in self.fields:
            self.fields['delivery_agent'].queryset = User.objects.filter(
                is_active=True,
                is_delivery=True
            ).order_by('email')
            self.fields['delivery_agent'].required = False
            self.fields['delivery_agent'].empty_label = "-- بدون مندوب حالياً --"

    def clean_grand_total(self):
        """التحقق من إجمالي المبلغ"""
        grand_total = self.cleaned_data.get('grand_total')
        if grand_total is not None:
            if grand_total < 0:
                raise ValidationError('إجمالي المبلغ لا يمكن أن يكون سالباً')
            if grand_total > 999999.99:
                raise ValidationError('إجمالي المبلغ كبير جداً')
        return grand_total

    def clean_shipping_address_snapshot(self):
        """التحقق من عنوان الشحن JSON"""
        address = self.cleaned_data.get('shipping_address_snapshot')
        if address:
            try:
                import json
                if isinstance(address, str):
                    json.loads(address)
            except json.JSONDecodeError:
                raise ValidationError('عنوان الشحن يجب أن يكون بصيغة JSON صحيحة')
        return address


class OrderStatusForm(forms.Form):
    """نموذج تغيير حالة الطلب"""
    
    payment_status = forms.ChoiceField(
        choices=Order.PaymentStatus.choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='حالة الدفع الجديدة',
        help_text='اختر حالة الدفع الجديدة للطلب'
    )
    fulfillment_status = forms.ChoiceField(
        choices=Order.FulfillmentStatus.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='حالة التجهيز/التسليم الجديدة',
        help_text='اختر حالة التجهيز/التسليم الجديدة'
    )

    def __init__(self, order, *args, **kwargs):
        self.order = order
        super().__init__(*args, **kwargs)
        
        # تعيين الحالة الحالية كقيمة افتراضية
        self.fields['payment_status'].initial = order.payment_status
        self.fields['fulfillment_status'].initial = order.fulfillment_status


## تم الاستغناء عن نموذج حالة طلب المتجر بعد توحيد نموذج الطلب


class OrderDeleteForm(forms.Form):
    """نموذج تأكيد حذف الطلب"""
    
    confirm_delete = forms.BooleanField(
        label='أؤكد أنني أريد حذف هذا الطلب نهائياً',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        error_messages={
            'required': 'يجب تأكيد الحذف للمتابعة'
        }
    )

    def __init__(self, order, *args, **kwargs):
        self.order = order
        super().__init__(*args, **kwargs)

    def clean_confirm_delete(self):
        confirmed = self.cleaned_data.get('confirm_delete')
        if not confirmed:
            raise ValidationError('يجب تأكيد الحذف للمتابعة')
        return confirmed


class OrderItemForm(forms.ModelForm):
    """نموذج إضافة وتعديل عناصر الطلب"""
    
    class Meta:
        model = OrderItem
        fields = ['order', 'variant', 'quantity', 'price_at_purchase', 
                 'product_name_snapshot', 'variant_options_snapshot', 'status']
        widgets = {
            'order': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'variant': forms.Select(attrs={
                'class': 'form-select'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'الكمية'
            }),
            'price_at_purchase': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'السعر وقت الشراء'
            }),
            'product_name_snapshot': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المنتج'
            }),
            'variant_options_snapshot': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'خيارات المتغير (JSON)'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'order': 'الطلب',
            'variant': 'متغير المنتج',
            'quantity': 'الكمية',
            'price_at_purchase': 'السعر وقت الشراء',
            'product_name_snapshot': 'اسم المنتج',
            'variant_options_snapshot': 'خيارات المتغير',
            'status': 'حالة العنصر'
        }

    def clean_quantity(self):
        """التحقق من الكمية"""
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            if quantity < 1:
                raise ValidationError('الكمية يجب أن تكون 1 على الأقل')
            if quantity > 9999:
                raise ValidationError('الكمية كبيرة جداً')
        return quantity

    def clean_price_at_purchase(self):
        """التحقق من السعر"""
        price = self.cleaned_data.get('price_at_purchase')
        if price is not None:
            if price < 0:
                raise ValidationError('السعر لا يمكن أن يكون سالباً')
            if price > 99999.99:
                raise ValidationError('السعر كبير جداً')
        return price

    def clean_variant_options_snapshot(self):
        """التحقق من خيارات المتغير JSON"""
        options = self.cleaned_data.get('variant_options_snapshot')
        if options:
            try:
                import json
                if isinstance(options, str):
                    json.loads(options)
            except json.JSONDecodeError:
                raise ValidationError('خيارات المتغير يجب أن تكون بصيغة JSON صحيحة')
        return options
