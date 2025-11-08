// Core shared functionality - Dashboard JavaScript Module

// عرض الإشعارات
function showNotification(message, type = 'info') {
    // إنشاء عنصر الإشعار
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // إزالة الإشعار بعد 3 ثوان
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

// Simple alert wrapper for legacy calls
function showAlert(message, type = 'info') {
    try {
        showNotification(message, type);
    } catch (e) {
        // Fallback
        alert(message);
    }
}

// دالة مساعدة لتنظيف النصوص من HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// CSRF helper (global)
function getCsrfToken() {
    const name = 'csrftoken=';
    const cookies = document.cookie ? document.cookie.split(';') : [];
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name)) return c.substring(name.length);
    }
    const el = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
}

// Delete confirmation functionality (global)
function setupDeleteConfirmation() {
    const confirmDeleteCheckbox = document.getElementById('confirmDelete');
    const deleteButton = document.getElementById('deleteButton');
    if (confirmDeleteCheckbox && deleteButton) {
        deleteButton.disabled = !confirmDeleteCheckbox.checked;
        confirmDeleteCheckbox.addEventListener('change', function() {
            deleteButton.disabled = !this.checked;
            if (this.checked) {
                deleteButton.classList.remove('btn-outline-danger');
                deleteButton.classList.add('btn-danger');
            } else {
                deleteButton.classList.remove('btn-danger');
                deleteButton.classList.add('btn-outline-danger');
            }
        });
    }

    const deleteCheckboxes = document.querySelectorAll('input[type="checkbox"][name="confirm"]');
    deleteCheckboxes.forEach((checkbox) => {
        const form = checkbox.closest('form');
        if (form) {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = !checkbox.checked;
                checkbox.addEventListener('change', function() {
                    submitBtn.disabled = !this.checked;
                    if (this.checked) {
                        submitBtn.classList.remove('btn-outline-danger');
                        submitBtn.classList.add('btn-danger');
                    } else {
                        submitBtn.classList.remove('btn-danger');
                        submitBtn.classList.add('btn-outline-danger');
                    }
                });
            }
        }
    });
}

// Toggle buttons by checkbox helper (global)
function initToggleButtons() {
    const toggleCheckboxes = document.querySelectorAll('input[type="checkbox"][data-toggle="button"]');
    toggleCheckboxes.forEach(checkbox => {
        const targetButton = document.querySelector(checkbox.dataset.target);
        if (targetButton) {
            checkbox.addEventListener('change', function() {
                targetButton.disabled = !this.checked;
            });
        }
    });
}

// Enhanced Sidebar Functionality
function initSidebarEnhancements() {
    // Smooth scroll to active section
    const activeLink = document.querySelector('.sidebar .nav-link.active');
    if (activeLink) {
        activeLink.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        // Alt + S to focus sidebar
        if (e.altKey && e.key === 's') {
            e.preventDefault();
            const firstLink = document.querySelector('.sidebar .nav-link');
            if (firstLink) firstLink.focus();
        }
        
        // Arrow key navigation in sidebar
        if (document.activeElement && document.activeElement.classList.contains('nav-link')) {
            const links = Array.from(document.querySelectorAll('.sidebar .nav-link'));
            const currentIndex = links.indexOf(document.activeElement);
            
            if (e.key === 'ArrowDown' && currentIndex < links.length - 1) {
                e.preventDefault();
                links[currentIndex + 1].focus();
            } else if (e.key === 'ArrowUp' && currentIndex > 0) {
                e.preventDefault();
                links[currentIndex - 1].focus();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                document.activeElement.click();
            }
        }
    });
    
    // Mobile sidebar toggle
    const sidebarToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar && window.innerWidth <= 768) {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
        
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
        });
        
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }
    
    // Add hover effects to nav sections
    const navSections = document.querySelectorAll('.nav-section');
    navSections.forEach(section => {
        section.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(2px)';
        });
        
        section.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
    
    // Enhanced loading states for navigation
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't show loading for current page
            if (this.classList.contains('active')) return;
            
            // Add loading state
            const icon = this.querySelector('i');
            const originalClass = icon.className;
            icon.className = 'fas fa-spinner fa-spin me-2';
            
            // Show page loading indicator
            showPageLoading();
            
            // Restore icon after navigation (fallback)
            setTimeout(() => {
                icon.className = originalClass;
            }, 2000);
        });
    });
}

// Enhanced Loading Indicators
function showPageLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
        loadingOverlay.style.display = 'flex';
    }
}

function hidePageLoading() {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        setTimeout(() => {
            loadingOverlay.classList.add('d-none');
            loadingOverlay.style.display = 'none';
        }, 300);
    }
}

// Enhanced Card Animations
function initCardAnimations() {
    const cards = document.querySelectorAll('.card');
    
    // Intersection Observer for scroll animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach((card, index) => {
        // Initial state for animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = `all 0.3s ease ${index * 0.05}s`;
        
        observer.observe(card);
        
        // Enhanced hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

// Enhanced Performance Monitoring
function initPerformanceMonitoring() {
    // Monitor page load time
    window.addEventListener('load', function() {
        const loadTime = performance.now();
        console.log(`Page loaded in ${Math.round(loadTime)}ms`);
        
        // Hide loading indicator
        hidePageLoading();
        
        // Show performance notification for slow loads
        if (loadTime > 3000) {
            showNotification('تم تحميل الصفحة بنجاح', 'info');
        }
    });
    
    // Monitor WebSocket connection status
    let connectionStatus = 'disconnected';
    
    function updateConnectionIndicator(status) {
        connectionStatus = status;
        const indicator = document.querySelector('.connection-indicator');
        if (indicator) {
            indicator.className = `connection-indicator ${status}`;
            indicator.title = status === 'connected' ? 'متصل' : 'غير متصل';
        }
    }
    
    // Add connection indicator to navbar
    const navbar = document.querySelector('.navbar .container-fluid');
    if (navbar) {
        const indicator = document.createElement('div');
        indicator.className = 'connection-indicator disconnected';
        indicator.innerHTML = '<i class="fas fa-circle"></i>';
        indicator.style.cssText = `
            position: absolute;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            font-size: 0.7rem;
            color: #dc2626;
            transition: color 0.15s ease;
        `;
        navbar.appendChild(indicator);
    }
    
    // Update WebSocket functions to use indicator
    const originalInitWebSocket = window.initWebSocket;
    if (originalInitWebSocket) {
        window.initWebSocket = function() {
            const result = originalInitWebSocket.apply(this, arguments);
            
            if (dashboardSocket) {
                dashboardSocket.addEventListener('open', () => updateConnectionIndicator('connected'));
                dashboardSocket.addEventListener('close', () => updateConnectionIndicator('disconnected'));
                dashboardSocket.addEventListener('error', () => updateConnectionIndicator('error'));
            }
            
            return result;
        };
    }
}

// Form validation and submission handling
function initFormValidation() {
    // Basic card animations
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.transition = 'box-shadow 0.2s ease';
    });

    // Form validation and submission handling
    const validationForms = document.querySelectorAll('.needs-validation');
    Array.from(validationForms).forEach(form => {
        form.addEventListener('submit', event => {
            // If the form is invalid according to the browser, prevent submission
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                // If the form is valid, disable the submit button to prevent multiple submissions
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.dataset.originalText = originalText;
                    submitBtn.innerHTML = 'جاري الحفظ...';
                    submitBtn.disabled = true;
                }
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Add is-invalid class to fields with errors and re-enable submit button if errors exist
    const errorFeedbacks = document.querySelectorAll('.invalid-feedback');
    if (errorFeedbacks.length > 0) {
        errorFeedbacks.forEach(error => {
            const field = error.previousElementSibling;
            if (field && (field.classList.contains('form-control') || field.classList.contains('form-select'))) {
                field.classList.add('is-invalid');
            }

            // If there are errors, find the parent form and re-enable its submit button
            const form = error.closest('form');
            if (form) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && submitBtn.disabled) {
                    const originalText = submitBtn.dataset.originalText || 'حفظ';
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            }
        });
    }

    // Mark required fields
    const requiredFields = document.querySelectorAll('input[required], select[required], textarea[required]');
    requiredFields.forEach(field => {
        const label = document.querySelector(`label[for="${field.id}"]`);
        if (label && !label.classList.contains('required-field')) {
            label.classList.add('required-field');
        }
    });

    // JSON validation for address fields
    const jsonFields = document.querySelectorAll('textarea[name*="address"], textarea[name*="snapshot"]');
    jsonFields.forEach(field => {
        field.addEventListener('blur', function() {
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
    });

    // Number validation for price fields
    const priceFields = document.querySelectorAll('input[type="number"][name*="price"], input[type="number"][name*="total"]');
    priceFields.forEach(field => {
        field.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value < 0) {
                this.setCustomValidity('المبلغ لا يمكن أن يكون سالباً');
            } else if (value > 999999.99) {
                this.setCustomValidity('المبلغ كبير جداً');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

// Initialize core functionality on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Basic form validation and UI enhancements
    initFormValidation();
    
    // Core functionality
    setupDeleteConfirmation();
    initToggleButtons();
    initCardAnimations();
    initSidebarEnhancements();
    initPerformanceMonitoring();
    
    // Add CSS for connection indicator
    const style = document.createElement('style');
    style.textContent = `
        .connection-indicator.connected { color: #059669 !important; }
        .connection-indicator.disconnected { color: #dc2626 !important; }
        .connection-indicator.error { color: #d97706 !important; }
        .connection-indicator i { animation: pulse 1.5s infinite; }
    `;
    document.head.appendChild(style);
});