// Pricing functionality for promotion and offer forms

// JSON validation for offer configuration field
function initOfferConfigurationValidation() {
    const configField = document.querySelector('textarea[name="configuration"]');
    if (configField) {
        configField.addEventListener('blur', function() {
            const value = this.value.trim();
            if (value) {
                try {
                    JSON.parse(value);
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } catch (e) {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            }
        });
    }
}

// Promotion type and value field interaction
function initPromotionTypeValueInteraction() {
    const promotionTypeField = document.getElementById('id_promotion_type');
    const valueField = document.getElementById('id_value');
    
    if (promotionTypeField && valueField) {
        function updateValueFieldHelp() {
            const selectedType = promotionTypeField.value;
            const helpText = valueField.parentNode.querySelector('.form-text');
            
            if (selectedType.includes('PERCENTAGE')) {
                if (helpText) {
                    helpText.textContent = 'أدخل نسبة مئوية بين 0 و 100';
                }
                valueField.setAttribute('max', '100');
                valueField.setAttribute('step', '0.01');
            } else if (selectedType.includes('FIXED')) {
                if (helpText) {
                    helpText.textContent = 'أدخل المبلغ بالريال السعودي';
                }
                valueField.removeAttribute('max');
                valueField.setAttribute('step', '0.01');
            }
        }
        
        promotionTypeField.addEventListener('change', updateValueFieldHelp);
        // Initialize on page load
        updateValueFieldHelp();
    }
}

// Coupon code validation
function initCouponCodeValidation() {
    const codeField = document.getElementById('id_code');
    if (codeField) {
        codeField.addEventListener('input', function() {
            // Convert to uppercase and remove spaces
            this.value = this.value.toUpperCase().replace(/\s/g, '');
            
            // Validate format (letters and numbers only)
            const isValid = /^[A-Z0-9]*$/.test(this.value);
            if (!isValid && this.value.length > 0) {
                this.setCustomValidity('يجب أن يحتوي الكود على أحرف إنجليزية وأرقام فقط');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Usage limit validation
function initUsageLimitValidation() {
    const usageLimitField = document.getElementById('id_usage_limit');
    const limitPerUserField = document.getElementById('id_limit_per_user');
    
    if (usageLimitField) {
        usageLimitField.addEventListener('input', function() {
            const value = parseInt(this.value);
            if (value < 0) {
                this.setCustomValidity('الحد الأقصى للاستخدام لا يمكن أن يكون سالباً');
            } else {
                this.setCustomValidity('');
            }
        });
    }
    
    if (limitPerUserField) {
        limitPerUserField.addEventListener('input', function() {
            const value = parseInt(this.value);
            const totalLimit = usageLimitField ? parseInt(usageLimitField.value) : null;
            
            if (value < 0) {
                this.setCustomValidity('الحد الأقصى لكل مستخدم لا يمكن أن يكون سالباً');
            } else if (totalLimit && value > totalLimit) {
                this.setCustomValidity('الحد الأقصى لكل مستخدم لا يمكن أن يكون أكبر من الحد الأقصى الإجمالي');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Date validation for start and end dates
function initDateValidation() {
    const startDateField = document.getElementById('id_start_at');
    const endDateField = document.getElementById('id_end_at');
    
    if (startDateField && endDateField) {
        function validateDates() {
            const startDate = new Date(startDateField.value);
            const endDate = new Date(endDateField.value);
            
            if (startDateField.value && endDateField.value) {
                if (endDate <= startDate) {
                    endDateField.setCustomValidity('تاريخ النهاية يجب أن يكون بعد تاريخ البداية');
                } else {
                    endDateField.setCustomValidity('');
                }
            }
        }
        
        startDateField.addEventListener('change', validateDates);
        endDateField.addEventListener('change', validateDates);
    }
}

// Priority field validation
function initPriorityValidation() {
    const priorityField = document.getElementById('id_priority');
    if (priorityField) {
        priorityField.addEventListener('input', function() {
            const value = parseInt(this.value);
            if (value < 0) {
                this.setCustomValidity('الأولوية لا يمكن أن تكون سالبة');
            } else if (value > 999) {
                this.setCustomValidity('الأولوية لا يمكن أن تكون أكبر من 999');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Minimum purchase amount validation
function initMinPurchaseAmountValidation() {
    const minAmountField = document.getElementById('id_min_purchase_amount');
    if (minAmountField) {
        minAmountField.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value < 0) {
                this.setCustomValidity('الحد الأدنى للمبلغ لا يمكن أن يكون سالباً');
            } else if (value > 999999.99) {
                this.setCustomValidity('الحد الأدنى للمبلغ كبير جداً');
            } else {
                this.setCustomValidity('');
            }
        });
    }
}

// Initialize all pricing validations
function initPricingValidations() {
    initOfferConfigurationValidation();
    initPromotionTypeValueInteraction();
    initCouponCodeValidation();
    initUsageLimitValidation();
    initDateValidation();
    initPriorityValidation();
    initMinPurchaseAmountValidation();
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initPricingValidations();
});