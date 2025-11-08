// Products functionality from dashboard.js (copied as-is)

// Product form category loading functionality
function initProductFormCategoryLoader() {
    const storeSelect = document.getElementById('id_store');
    const categorySelect = document.getElementById('id_category');
    
    if (storeSelect && categorySelect) {
        storeSelect.addEventListener('change', function() {
            const storeId = this.value;
            
            // مسح التصنيفات الحالية
            categorySelect.innerHTML = '<option value="">-- اختر التصنيف --</option>';
            categorySelect.disabled = true;
            
            if (storeId) {
                // جلب التصنيفات للمتجر المختار
                fetch(`/dashboard/api/categories-by-store/?store_id=${storeId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.categories && data.categories.length > 0) {
                            data.categories.forEach(category => {
                                const option = document.createElement('option');
                                option.value = category.id;
                                option.textContent = category.name;
                                categorySelect.appendChild(option);
                            });
                            categorySelect.disabled = false;
                        }
                    })
                    .catch(error => {
                        console.error('خطأ في جلب التصنيفات:', error);
                    });
            }
        });
    }
}

// إدارة متغيرات المنتج
function initProductVariants() {
    const toggleBtns = document.querySelectorAll('.js-toggle-variant-form');
    const variantFormCollapse = document.getElementById('variantFormCollapse');
    const cancelBtn = document.getElementById('cancelVariantBtn');

    if (toggleBtns.length > 0 && variantFormCollapse) {
        let collapse = null;
        try {
            if (window.bootstrap && bootstrap.Collapse) {
                collapse = bootstrap.Collapse.getOrCreateInstance(variantFormCollapse, { toggle: false });
            }
        } catch (e) {
            console.error('Bootstrap Collapse not available:', e);
            collapse = null;
        }

        // ربط الحدث بكل الأزرار
        toggleBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                if (collapse) {
                    collapse.toggle();
                }
            });
        });

        // تحديث نص الأزرار بناءً على حالة الـ collapse
        variantFormCollapse.addEventListener('show.bs.collapse', () => {
            toggleBtns.forEach(btn => {
                btn.innerHTML = '<i class="fas fa-minus me-1"></i>إلغاء';
            });
        });

        variantFormCollapse.addEventListener('hide.bs.collapse', () => {
            toggleBtns.forEach(btn => {
                btn.innerHTML = '<i class="fas fa-plus me-1"></i>إضافة متغير';
            });
        });

        // زر الإلغاء
        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                if (collapse) {
                    collapse.hide();
                }
                const vf = document.getElementById('variantForm');
                if (vf) vf.reset();
            });
        }
    }
    
    // التعامل مع نموذج إضافة المتغير
    const variantFormContainer = document.getElementById('variantForm');
    const submitBtn = document.getElementById('submitVariantBtn');

    if (variantFormContainer && submitBtn) {
        console.log('[Variants] Variant form components found, initializing listeners');

        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('[Variants] submitVariantBtn clicked');

            const productSection = document.querySelector('[data-product-id]');
            const productId = productSection ? productSection.dataset.productId : null;
            if (!productId) {
                showAlert('لم يتم العثور على معرف المنتج', 'danger');
                console.error('[Variants] Missing data-product-id on container');
                return;
            }

            // إظهار حالة التحميل
            const buttonText = submitBtn.querySelector('.button-text');
            const spinner = submitBtn.querySelector('.spinner-border');
            
            if (buttonText && spinner) {
                submitBtn.disabled = true;
                buttonText.textContent = 'جاري الحفظ...';
                spinner.classList.remove('d-none');
            }

            // جمع البيانات يدويًا من الحقول داخل الـ div
            const rawPrice = variantFormContainer.querySelector('#price')?.value;
            const rawSku = variantFormContainer.querySelector('#sku')?.value;
            const rawOptionsText = variantFormContainer.querySelector('#options_text')?.value;
            const rawCover = variantFormContainer.querySelector('input[name="cover_image_url"]')?.value;

            const data = {
                price: rawPrice ? parseFloat(rawPrice) : 0,
                sku: rawSku && rawSku.trim() ? rawSku.trim() : null,
                options_text: rawOptionsText || '',
                cover_image_url: rawCover && rawCover.trim() ? rawCover.trim() : ''
            };

            console.log('Submitting variant data:', data);

            fetch(`/api/products/${productId}/variants/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify(data)
            })
            .then(response => {
                console.log('Response status:', response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);
                if (data.success && data.data) {
                    // إشعار مرئي صغير بجانب زر الحفظ
                    if (submitBtn) {
                        const note = document.createElement('span');
                        note.className = 'ms-2 text-success small';
                        note.textContent = 'تم الحفظ';
                        submitBtn.parentNode.insertBefore(note, submitBtn.nextSibling);
                        setTimeout(() => note.remove(), 1500);
                    }

                    // إغلاق النموذج وإعادة تعيينه
                    try {
                        const variantFormCollapse = document.getElementById('variantFormCollapse');
                        if (variantFormCollapse && window.bootstrap && bootstrap.Collapse) {
                            const c = bootstrap.Collapse.getOrCreateInstance(variantFormCollapse, { toggle: false });
                            c.hide();
                        }
                    } catch (e) {
                        console.error('Error hiding collapse:', e);
                    }

                    // تحديث جميع أزرار التبديل
                    const toggleBtns = document.querySelectorAll('.js-toggle-variant-form');
                    toggleBtns.forEach(btn => {
                        btn.innerHTML = '<i class="fas fa-plus me-1"></i>إضافة متغير';
                    });

                    // إعادة تعيين حقول النموذج
                    const variantFormContainer = document.getElementById('variantForm');
                    if (variantFormContainer) {
                        const inputs = variantFormContainer.querySelectorAll('input, textarea');
                        inputs.forEach(input => input.value = '');
                    }

                    // تحديث جدول المتغيرات ديناميكياً
                    const section = document.querySelector('[data-product-id]');
                    const tbody = section ? section.querySelector('table.table.table-sm.table-hover tbody') : null;
                    if (tbody) {
                        // إزالة رسالة لا توجد متغيرات إن وجدت
                        const noMsg = document.getElementById('noVariantsMessage');
                        if (noMsg) noMsg.remove();

                        const v = data.data; // من السيريلآيزر
                        const tr = document.createElement('tr');
                        // بناء شارة الخيارات
                        let optionsHtml = '';
                        if (v.options && typeof v.options === 'object') {
                            Object.keys(v.options).forEach(key => {
                                const value = v.options[key];
                                optionsHtml += `<span class="badge bg-light text-dark me-1">${escapeHtml(key)}: ${escapeHtml(String(value))}</span>`;
                            });
                        } else {
                            optionsHtml = '<span class="text-muted">المتغير الأساسي</span>';
                        }

                        tr.innerHTML = `
                            <td>${optionsHtml}</td>
                            <td><strong class="text-success">${parseFloat(v.price).toFixed(2)} ريال</strong></td>
                            <td><code class="text-muted">${escapeHtml(v.sku || '-')}</code></td>
                            <td>
                                <div class="btn-group btn-group-sm" role="group">
                                    <button type="button" class="btn btn-outline-primary" title="تعديل" data-variant-id="${v.id}"><i class="fas fa-edit"></i></button>
                                    <button type="button" class="btn btn-outline-danger" title="حذف" data-variant-id="${v.id}" data-action="delete"><i class="fas fa-trash"></i></button>
                                </div>
                            </td>`;
                        tbody.prepend(tr);
                    }
                } else {
                    // عرض أخطاء DRF بشكل أوضح إن توفرت
                    if (data.errors && typeof data.errors === 'object') {
                        const messages = [];
                        Object.keys(data.errors).forEach(k => {
                            const v = data.errors[k];
                            if (Array.isArray(v)) {
                                v.forEach(msg => messages.push(`${k}: ${msg}`));
                            } else if (typeof v === 'string') {
                                messages.push(`${k}: ${v}`);
                            }
                        });
                        showAlert(messages.join('\n') || 'حدث خطأ غير معروف', 'danger');
                    } else {
                        showAlert('حدث خطأ: ' + (data.error || 'خطأ غير معروف'), 'danger');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('حدث خطأ في الاتصال: ' + error.message, 'danger');
            })
            .finally(() => {
                // إعادة تعيين حالة الزر
                if (submitBtn && buttonText && spinner) {
                    submitBtn.disabled = false;
                    buttonText.textContent = 'حفظ المتغير';
                    spinner.classList.add('d-none');
                }
            });
        });
    }
    
    // التعامل مع أزرار حذف المتغيرات
    document.addEventListener('click', function(e) {
        if (e.target.closest('[data-action="delete"]')) {
            const button = e.target.closest('[data-action="delete"]');
            const variantId = button.dataset.variantId;
            const productId = document.querySelector('[data-product-id]')?.dataset.productId;
            
            if (confirm('هل أنت متأكد من حذف هذا المتغير؟')) {
                deleteVariant(productId, variantId);
            }
        }
    });
}

function deleteVariant(productId, variantId) {
    console.log('Deleting variant:', variantId, 'for product:', productId);
    
    fetch(`/api/products/variants/${variantId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('Delete response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Delete response data:', data);
        if (data.success) {
            showAlert('تم حذف المتغير بنجاح', 'success');
            // إزالة الصف ديناميكياً
            const section = document.querySelector('[data-product-id]');
            const btn = document.querySelector(`[data-action="delete"][data-variant-id="${variantId}"]`);
            const row = btn ? btn.closest('tr') : null;
            if (row) row.remove();
        } else {
            showAlert('حدث خطأ: ' + (data.error || 'خطأ غير معروف'), 'danger');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showAlert('حدث خطأ في الاتصال: ' + error.message, 'danger');
    });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initProductFormCategoryLoader();
    initProductVariants();
});