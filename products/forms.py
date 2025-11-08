from django import forms
from django.core.exceptions import ValidationError
import json

from .models import Product, ProductCategory, ProductVariant
from stores.models import Store

class ProductForm(forms.ModelForm):
    """نموذج إضافة وتعديل المنتجات"""
    
    # حقل إضافي للمواصفات كنص
    specifications_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'مثال:\nالشاشة: 6.1 بوصة\nالذاكرة: 8 جيجا\nالتخزين: 256 جيجا'
        }),
        label='المواصفات',
        help_text='أدخل المواصفات كل واحدة في سطر منفصل بالصيغة: اسم المواصفة: القيمة'
    )
    
    class Meta:
        model = Product
        fields = ['store', 'category', 'name', 'description', 'cover_image_url', 'average_rating', 'review_count', 'selling_count']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المنتج',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'وصف المنتج (اختياري)'
            }),
            'cover_image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'رابط صورة المنتج (اختياري)'
            }),
            'store': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'required': False
            }),
            'average_rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5',
                'step': '0.1',
                'placeholder': '0.0'
            }),
            'review_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'selling_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            })
        }
        labels = {
            'store': 'المتجر',
            'category': 'التصنيف',
            'name': 'اسم المنتج',
            'description': 'الوصف',
            'cover_image_url': 'رابط صورة الغلاف',
            'average_rating': 'متوسط التقييم',
            'review_count': 'عدد التقييمات',
            'selling_count': 'عدد المبيعات'
        }
        help_texts = {
            'store': 'اختر المتجر الذي سيحتوي على هذا المنتج',
            'category': 'اختر تصنيف المنتج (اختياري)',
            'name': 'اسم المنتج كما سيظهر للعملاء',
            'description': 'وصف تفصيلي عن المنتج وميزاته',
            'cover_image_url': 'رابط مباشر لصورة المنتج الرئيسية',
            'average_rating': 'متوسط تقييم المنتج من 0 إلى 5',
            'review_count': 'عدد التقييمات التي حصل عليها المنتج',
            'selling_count': 'عدد المرات التي تم بيع المنتج فيها'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المتاجر (المتاجر النشطة فقط)
        self.fields['store'].queryset = Store.objects.filter(
            status=Store.StoreStatus.ACTIVE
        ).select_related('owner').order_by('name')
        
        # إضافة خيار فارغ للمتجر
        self.fields['store'].empty_label = "-- اختر المتجر --"
        
        # تحديد خيارات التصنيفات مع دعم MPTT
        if self.instance.pk and self.instance.store:
            # في حالة التعديل، عرض تصنيفات المتجر الحالي فقط
            self.fields['category'].queryset = ProductCategory.objects.filter(
                store=self.instance.store
            ).order_by('tree_id', 'lft')  # ترتيب شجري
        else:
            # في حالة الإضافة، لا نعرض أي تصنيفات حتى يتم اختيار المتجر
            self.fields['category'].queryset = ProductCategory.objects.none()
        
        # إضافة خيار فارغ للتصنيف
        self.fields['category'].empty_label = "-- اختر التصنيف --"
        
        # تحسين عرض التصنيفات الشجرية
        category_choices = []
        if self.fields['category'].queryset.exists():
            for category in self.fields['category'].queryset:
                # إضافة مسافات للمستويات الفرعية
                indent = "—" * category.level
                display_name = f"{indent} {category.name}" if category.level > 0 else category.name
                category_choices.append((category.id, display_name))
            
            # تحديث الخيارات مع التنسيق الشجري
            self.fields['category'].widget.choices = [('', '-- اختر التصنيف --')] + category_choices
        
        # تحميل المواصفات الحالية في حقل النص
        if self.instance.pk and self.instance.specifications:
            specs_text = []
            for key, value in self.instance.specifications.items():
                specs_text.append(f"{key}: {value}")
            self.fields['specifications_text'].initial = '\n'.join(specs_text)

    def clean_name(self):
        """التحقق من اسم المنتج"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('اسم المنتج يجب أن يكون حرفين على الأقل')
            if len(name) > 255:
                raise forms.ValidationError('اسم المنتج طويل جداً (الحد الأقصى 255 حرف)')
        return name

    def clean_cover_image_url(self):
        """التحقق من رابط الصورة"""
        cover_image_url = self.cleaned_data.get('cover_image_url')
        if cover_image_url:
            cover_image_url = cover_image_url.strip()
            if not cover_image_url.startswith(('http://', 'https://')):
                raise forms.ValidationError('رابط الصورة يجب أن يبدأ بـ http:// أو https://')
        return cover_image_url

    def clean_specifications_text(self):
        """تحويل نص المواصفات إلى JSON"""
        specs_text = self.cleaned_data.get('specifications_text', '').strip()
        specifications = {}
        
        if specs_text:
            lines = specs_text.split('\n')
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                if ':' not in line:
                    raise forms.ValidationError(
                        f'السطر {line_num}: يجب أن تكون المواصفة بالصيغة "اسم المواصفة: القيمة"'
                    )
                
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if not key or not value:
                    raise forms.ValidationError(
                        f'السطر {line_num}: اسم المواصفة والقيمة مطلوبان'
                    )
                
                specifications[key] = value
        
        return specifications

    def clean(self):
        """التحقق العام من النموذج"""
        cleaned_data = super().clean()
        store = cleaned_data.get('store')
        category = cleaned_data.get('category')
        name = cleaned_data.get('name')
        
        # التحقق من أن التصنيف ينتمي للمتجر المختار
        if store and category and category.store != store:
            raise forms.ValidationError(
                f'التصنيف "{category.name}" لا ينتمي للمتجر "{store.name}"'
            )
        
        # التحقق من عدم وجود منتج بنفس الاسم في نفس المتجر
        if store and name and not self.instance.pk:
            existing_product = Product.objects.filter(store=store, name=name).first()
            if existing_product:
                raise forms.ValidationError(
                    f'يوجد منتج بنفس الاسم "{name}" في المتجر "{store.name}"'
                )
        
        return cleaned_data

    def save(self, commit=True):
        """حفظ المنتج مع المواصفات"""
        instance = super().save(commit=False)
        
        # حفظ المواصفات من النص المحول
        specifications = self.cleaned_data.get('specifications_text', {})
        instance.specifications = specifications
        
        if commit:
            instance.save()
        
        return instance


class ProductDeleteForm(forms.Form):
    """نموذج تأكيد حذف المنتج"""
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='أؤكد رغبتي في حذف هذا المنتج نهائياً',
        help_text='تحذير: هذا الإجراء لا يمكن التراجع عنه'
    )
    
    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        
    def clean_confirm(self):
        """التحقق من التأكيد"""
        confirm = self.cleaned_data.get('confirm')
        if not confirm:
            raise forms.ValidationError('يجب تأكيد الحذف')
        return confirm


class ProductVariantForm(forms.ModelForm):
    """نموذج إضافة وتعديل متغيرات المنتج"""
    
    # حقل إضافي للخيارات كنص
    options_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'مثال:\nاللون: أسود\nالحجم: كبير\nالذاكرة: 256GB'
        }),
        label='خيارات المتغير',
        help_text='أدخل خيارات المتغير، كل خيار في سطر منفصل بصيغة: المفتاح: القيمة'
    )
    
    class Meta:
        model = ProductVariant
        fields = ['price', 'sku', 'cover_image_url']
        
        widgets = {
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'كود المنتج (اختياري)'
            }),
            'cover_image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/image.jpg'
            }),
        }
        
        labels = {
            'price': 'السعر',
            'sku': 'كود المنتج (SKU)',
            'cover_image_url': 'رابط صورة المتغير',
        }
        
        help_texts = {
            'price': 'سعر هذا المتغير بالريال السعودي',
            'sku': 'كود فريد للمنتج (اختياري)',
            'cover_image_url': 'رابط مباشر لصورة هذا المتغير (اختياري)',
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('السعر يجب أن يكون أكبر من أو يساوي صفر')
        return price

    def clean_options_text(self):
        """تحويل نص الخيارات إلى قاموس JSON"""
        options_text = self.cleaned_data.get('options_text', '').strip()
        
        if not options_text:
            return {}
        
        options = {}
        lines = options_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                options[key.strip()] = value.strip()
            elif line:  # إذا كان السطر غير فارغ ولا يحتوي على :
                raise ValidationError(f'تنسيق غير صحيح في السطر: "{line}". استخدم تنسيق "المفتاح: القيمة"')
        
        return options

    def save(self, commit=True):
        variant = super().save(commit=False)
        
        # تحويل نص الخيارات إلى JSON
        options_text = self.cleaned_data.get('options_text', '')
        if options_text:
            variant.options = self.clean_options_text()
        else:
            variant.options = {}
        
        if commit:
            variant.save()
        
        return variant
