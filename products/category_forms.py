from django import forms
from .models import ProductCategory
from stores.models import Store


class ProductCategoryForm(forms.ModelForm):
    """نموذج إنشاء وتعديل تصنيفات المنتجات"""
    
    class Meta:
        model = ProductCategory
        fields = ['store', 'name', 'parent']
        widgets = {
            'store': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم القسم (مثل: المشويات، المقبلات، الهواتف الذكية)',
                'required': True
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'store': 'المتجر',
            'name': 'اسم القسم',
            'parent': 'القسم الأب (اختياري)'
        }
        help_texts = {
            'store': 'اختر المتجر الذي ينتمي إليه هذا القسم',
            'name': 'اسم القسم أو التصنيف الفرعي داخل المتجر',
            'parent': 'اختر القسم الأب إذا كان هذا قسم فرعي'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تحديد خيارات المتاجر النشطة فقط
        self.fields['store'].queryset = Store.objects.filter(status=Store.StoreStatus.ACTIVE).order_by('name')
        
        # تحديد خيارات الأقسام الأب بناءً على المتجر المحدد
        if 'store' in self.data:
            try:
                store_id = int(self.data.get('store'))
                self.fields['parent'].queryset = ProductCategory.objects.filter(
                    store_id=store_id
                ).order_by('name')
            except (ValueError, TypeError):
                self.fields['parent'].queryset = ProductCategory.objects.none()
        elif self.instance.pk and self.instance.store:
            self.fields['parent'].queryset = ProductCategory.objects.filter(
                store=self.instance.store
            ).exclude(pk=self.instance.pk).order_by('name')
        else:
            self.fields['parent'].queryset = ProductCategory.objects.none()

    def clean_name(self):
        """التحقق من صحة اسم القسم"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('اسم القسم يجب أن يكون أكثر من حرفين')
            if len(name) > 200:
                raise forms.ValidationError('اسم القسم يجب أن يكون أقل من 200 حرف')
        return name

    def clean(self):
        """التحقق من صحة البيانات المترابطة"""
        cleaned_data = super().clean()
        store = cleaned_data.get('store')
        parent = cleaned_data.get('parent')
        name = cleaned_data.get('name')

        # التحقق من أن القسم الأب ينتمي لنفس المتجر
        if parent and store and parent.store != store:
            raise forms.ValidationError('القسم الأب يجب أن ينتمي لنفس المتجر المحدد')

        # التحقق من عدم تكرار اسم القسم في نفس المتجر ونفس المستوى
        if store and name:
            existing = ProductCategory.objects.filter(
                store=store,
                name=name,
                parent=parent
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise forms.ValidationError('يوجد قسم بنفس الاسم في هذا المتجر والمستوى')

        return cleaned_data


class ProductCategoryDeleteForm(forms.Form):
    """نموذج تأكيد حذف تصنيف المنتج"""
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'confirmDelete'
        }),
        label='أؤكد رغبتي في حذف هذا القسم وجميع الأقسام الفرعية والمنتجات المرتبطة به نهائياً'
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
