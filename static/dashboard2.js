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

// Simple alert wrapper for legacy calls
function showAlert(message, type = 'info') {
    try {
        showNotification(message, type);
    } catch (e) {
        // Fallback
        alert(message);
    }
}

// تأكد من تحميل Chart.js قبل تشغيل الكود
function initOrdersChart() {
  const el = document.getElementById('ordersByDayChart');
  if (!el || !window.DASHBOARD_DATA || typeof Chart === 'undefined') {
    console.log('Chart.js not loaded or missing data');
    return;
  }
  const { labels, values } = window.DASHBOARD_DATA;

  // Destroy previous instance if it exists to avoid cumulative resizing
  if (window.__ORDERS_CHART__) {
    try { window.__ORDERS_CHART__.destroy(); } catch (e) {}
  }

  // Clean chart styling
  const ctx = el.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, 'rgba(37, 99, 235, 0.2)');
  gradient.addColorStop(1, 'rgba(37, 99, 235, 0.05)');

  try {
    window.__ORDERS_CHART__ = new Chart(el, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'الطلبات',
          data: values,
          borderColor: '#2563eb',
          backgroundColor: gradient,
          borderWidth: 2,
          tension: 0.3,
          fill: true,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: '#1d4ed8',
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2
        }]
      },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: { 
        legend: { 
          display: false 
        },
        tooltip: {
          backgroundColor: 'rgba(255, 255, 255, 0.98)',
          titleColor: '#1e293b',
          bodyColor: '#64748b',
          borderColor: '#2563eb',
          borderWidth: 1,
          cornerRadius: 6,
          displayColors: false,
          titleFont: {
            size: 13,
            weight: '600'
          },
          bodyFont: {
            size: 12
          },
          padding: 8,
          callbacks: {
            title: function(context) {
              return 'التاريخ: ' + context[0].label;
            },
            label: function(context) {
              return 'عدد الطلبات: ' + context.parsed.y;
            }
          }
        }
      },
      scales: {
        x: { 
          display: true,
          grid: {
            display: false
          },
          ticks: {
            color: '#718096',
            font: {
              size: 11,
              weight: '500'
            },
            maxTicksLimit: 8
          }
        },
        y: { 
          display: true,
          beginAtZero: true,
          grid: {
            color: 'rgba(226, 232, 240, 0.5)',
            borderDash: [5, 5]
          },
          ticks: {
            color: '#718096',
            font: {
              size: 11,
              weight: '500'
            },
            callback: function(value) {
              return value + ' طلب';
            }
          }
        }
      },
      elements: {
        line: {
          borderJoinStyle: 'round'
        }
      },
      animation: {
        duration: 2000,
        easing: 'easeInOutQuart'
      }
    }
    });
    console.log('Orders chart initialized successfully');
  } catch (error) {
    console.error('Error initializing orders chart:', error);
  }
}

// تشغيل الرسم البياني عند تحميل الصفحة
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initOrdersChart, 100);
  });
} else {
  setTimeout(initOrdersChart, 100);
}

// Minimal card animations
document.addEventListener('DOMContentLoaded', function() {
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


    // Delete confirmation, dynamic categories, and toggle buttons are initialized in global scope on DOMContentLoaded

    // Remove duplicate delete confirmation code
    // (Already handled above in enhanced checkbox functionality)
});

// WebSocket functionality for real-time updates
let dashboardSocket = null;

// WebSocket connection for real-time updates
function initWebSocket() {
    // التحقق من دعم WebSocket
    if (!window.WebSocket) {
        console.warn('WebSocket not supported');
        return;
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;
    
    try {
        dashboardSocket = new WebSocket(wsUrl);
        
        dashboardSocket.onopen = function(event) {
            console.log('WebSocket connected successfully');
            showNotification('متصل بنجاح مع التحديثات الفورية', 'success');
        };
        
        dashboardSocket.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };
        
        dashboardSocket.onclose = function(event) {
            console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
            
            if (event.code === 4001) {
                showNotification('يجب تسجيل الدخول للحصول على التحديثات الفورية', 'warning');
                return;
            }
            
            showNotification('انقطع الاتصال مع التحديثات الفورية', 'warning');
            
            // إعادة المحاولة بعد 5 ثوان إذا لم يكن الإغلاق مقصوداً
            if (event.code !== 1000) {
                setTimeout(initWebSocket, 5000);
            }
        };
        
        dashboardSocket.onerror = function(error) {
            console.error('WebSocket error:', error);
            showNotification('خطأ في الاتصال مع التحديثات الفورية', 'danger');
        };
        
    } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
        showNotification('فشل في إنشاء اتصال التحديثات الفورية', 'danger');
    }
}

// معالجة رسائل WebSocket
function handleWebSocketMessage(data) {
    if (!data || typeof data !== 'object') {
        console.warn('Invalid WebSocket message format:', data);
        return;
    }
    
    try {
        switch(data.type) {
            case 'connection_established':
                console.log('Dashboard WebSocket established');
                break;
                
            case 'new_order':
                if (data.order && data.order.id) {
                    handleNewOrder(data.order);
                    showNotification(data.message || 'طلب جديد', 'info');
                }
                break;
                
            case 'order_status_changed':
                if (data.order && data.order.id) {
                    handleOrderStatusChange(data.order);
                    showNotification(data.message || 'تم تحديث الطلب', 'info');
                }
                break;
                
            case 'stats_update':
                if (data.stats && typeof data.stats === 'object') {
                    updateDashboardStats(data.stats);
                }
                break;
                
            case 'pong':
                // استجابة ping للحفاظ على الاتصال
                break;
                
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    } catch (error) {
        console.error('Error handling WebSocket message:', error, data);
    }
}

// معالجة طلب جديد
function handleNewOrder(order) {
    if (!order || !order.id) {
        console.warn('Invalid order data:', order);
        return;
    }
    
    try {
        // تحديث عداد الطلبات
        const ordersCountElement = document.querySelector('[data-stat="orders"] .stat-number');
        if (ordersCountElement) {
            const currentCount = parseInt(ordersCountElement.textContent) || 0;
            ordersCountElement.textContent = currentCount + 1;
            
            // إضافة تأثير بصري
            ordersCountElement.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                ordersCountElement.classList.remove('animate__animated', 'animate__pulse');
            }, 500);
        }
        
        // إضافة الطلب إلى جدول الطلبات الحديثة إذا كان موجوداً
        addOrderToRecentTable(order);
        
        // تحديث الرسم البياني إذا كان موجوداً
        updateOrdersChart();
        
    } catch (error) {
        console.error('Error handling new order:', error, order);
    }
}

// معالجة تغيير حالة الطلب
function handleOrderStatusChange(order) {
    // البحث عن الطلب في الجدول وتحديث حالته
    const orderRow = document.querySelector(`tr[data-order-id="${order.id}"]`);
    if (orderRow) {
        const statusCell = orderRow.querySelector('.order-status');
        if (statusCell) {
            statusCell.innerHTML = getStatusBadge(order.status);
        }
    }
}

// إضافة طلب جديد إلى جدول الطلبات الحديثة
function addOrderToRecentTable(order) {
    if (!order || !order.id) {
        console.warn('Invalid order for table:', order);
        return;
    }
    
    try {
        const recentOrdersTable = document.querySelector('#recent-orders-table tbody');
        if (!recentOrdersTable) {
            console.log('Recent orders table not found on this page');
            return;
        }
        
        // التحقق من عدم وجود الطلب مسبقاً
        const existingRow = recentOrdersTable.querySelector(`tr[data-order-id="${order.id}"]`);
        if (existingRow) {
            console.log('Order already exists in table:', order.id);
            return;
        }
        
        const newRow = document.createElement('tr');
        newRow.setAttribute('data-order-id', order.id);
        newRow.innerHTML = `
            <td>#${order.id}</td>
            <td>${escapeHtml(order.user_name || 'غير محدد')}</td>
            <td>${escapeHtml(order.store_name || 'غير محدد')}</td>
            <td>${parseFloat(order.total_amount || 0).toFixed(2)} ريال</td>
            <td class="order-status">${getStatusBadge(order.status)}</td>
            <td>${formatDate(order.created_at)}</td>
            <td>
                <a href="/dashboard/orders/${order.id}/" class="btn btn-sm btn-outline-primary">
                    <i class="fas fa-eye"></i>
                </a>
            </td>
        `;
        
        // إضافة الصف الجديد في المقدمة
        recentOrdersTable.insertBefore(newRow, recentOrdersTable.firstChild);
        
        // إزالة الصف الأخير إذا كان هناك أكثر من 10 صفوف
        const rows = recentOrdersTable.querySelectorAll('tr');
        if (rows.length > 10) {
            recentOrdersTable.removeChild(rows[rows.length - 1]);
        }
        
        // إضافة تأثير بصري للصف الجديد
        newRow.classList.add('animate__animated', 'animate__fadeInDown', 'new-order');
        
        // إزالة التأثير بعد انتهائه
        setTimeout(() => {
            newRow.classList.remove('animate__animated', 'animate__fadeInDown', 'new-order');
        }, 800);
        
    } catch (error) {
        console.error('Error adding order to table:', error, order);
    }
}

// تحديث إحصائيات لوحة التحكم
function updateDashboardStats(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"] .stat-number`);
        if (element) {
            element.textContent = stats[key];
            element.classList.add('animate__animated', 'animate__pulse');
            setTimeout(() => {
                element.classList.remove('animate__animated', 'animate__pulse');
            }, 500);
        }
    });
}

// الحصول على badge حالة الطلب
function getStatusBadge(status) {
    const statusMap = {
        'pending_payment': '<span class="badge bg-warning">في انتظار الدفع</span>',
        'paid': '<span class="badge bg-success">مدفوع</span>',
        'cancelled': '<span class="badge bg-danger">ملغي</span>',
        'processing': '<span class="badge bg-info">قيد المعالجة</span>',
        'shipped': '<span class="badge bg-primary">تم الشحن</span>',
        'delivered': '<span class="badge bg-success">تم التسليم</span>'
    };
    return statusMap[status] || `<span class="badge bg-secondary">${status}</span>`;
}

// تنسيق التاريخ
function formatDate(dateString) {
    if (!dateString) return 'غير محدد';
    
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return 'تاريخ غير صحيح';
        }
        
        return date.toLocaleDateString('ar-SA', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting date:', error, dateString);
        return 'خطأ في التاريخ';
    }
}

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

// Simple alert wrapper for legacy calls (global scope)
function showAlert(message, type = 'info') {
    try {
        showNotification(message, type);
    } catch (e) {
        // Fallback
        alert(message);
    }
}

// تحديث الرسم البياني
function updateOrdersChart() {
    if (window.__ORDERS_CHART__) {
        // يمكن إضافة منطق تحديث البيانات هنا
        // مثل جلب البيانات الجديدة من API
        console.log('Updating orders chart...');
    }
}

// ping دوري للحفاظ على الاتصال
function keepWebSocketAlive() {
    try {
        if (dashboardSocket && dashboardSocket.readyState === WebSocket.OPEN) {
            dashboardSocket.send(JSON.stringify({
                type: 'ping',
                timestamp: Date.now()
            }));
        }
    } catch (error) {
        console.error('Error sending ping:', error);
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

// إدارة الطلبات
function initOrderManagement() {
    // Check if we're on the order form page
    const orderForm = document.querySelector('#order-form');
    if (!orderForm) {
        console.log('Order form not found, skipping order management initialization');
        return;
    }
    console.log('Order form found, initializing order management...');

    let selectedProducts = [];
    let stores = [];
    let products = [];
    let variants = [];

    // Load stores on page load
    loadStores();

    // Event Listeners
    const storeSelect = document.getElementById('store_select');
    const productSelect = document.getElementById('product_select');
    const variantSelect = document.getElementById('variant_select');
    const quantityInput = document.getElementById('quantity_input');
    const addProductBtn = document.getElementById('add_product_btn');

    if (storeSelect) storeSelect.addEventListener('change', handleStoreChange);
    if (productSelect) productSelect.addEventListener('change', handleProductChange);
    if (variantSelect) variantSelect.addEventListener('change', handleVariantChange);
    if (quantityInput) quantityInput.addEventListener('input', updatePrice);
    if (addProductBtn) addProductBtn.addEventListener('click', addProduct);

    // Update shipping address JSON
    const addressFields = ['shipping_name', 'shipping_phone', 'shipping_city', 'shipping_district', 'shipping_postal', 'shipping_address'];
    addressFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('input', updateShippingAddress);
        }
    });

    async function loadStores() {
        console.log('Starting to load stores...');
        try {
            const response = await fetch('/dashboard/api/stores/');
            console.log('Response status:', response.status);
            const data = await response.json();
            console.log('API Response data:', data);
            stores = data.stores || [];
            console.log('Stores array:', stores);
            if (storeSelect) {
                storeSelect.innerHTML = '<option value="">-- اختر المتجر --</option>';
                stores.forEach(store => {
                    console.log('Adding store:', store);
                    storeSelect.innerHTML += `<option value="${store.id}">${store.name}</option>`;
                });
                console.log('Store select HTML:', storeSelect.innerHTML);
            } else {
                console.error('Store select element not found!');
            }
        } catch (error) {
            console.error('خطأ في تحميل المتاجر:', error);
        }
    }

    async function handleStoreChange() {
        const storeId = this.value;
        
        // Reset products and variants
        if (productSelect) {
            productSelect.innerHTML = '<option value="">-- اختر المنتج --</option>';
            productSelect.disabled = !storeId;
        }
        if (variantSelect) {
            variantSelect.innerHTML = '<option value="">-- اختر المتغير --</option>';
            variantSelect.disabled = true;
        }
        if (quantityInput) quantityInput.disabled = true;
        if (addProductBtn) addProductBtn.disabled = true;

        if (storeId) {
            try {
                console.log('Loading products for store:', storeId);
                const response = await fetch(`/dashboard/api/products-by-store/?store_id=${storeId}`);
                console.log('Products response status:', response.status);
                const data = await response.json();
                console.log('Products API response:', data);
                products = data.products || [];
                console.log('Products array:', products);
                if (productSelect) {
                    if (products.length > 0) {
                        products.forEach(product => {
                            console.log('Adding product:', product);
                            productSelect.innerHTML += `<option value="${product.id}">${product.name}</option>`;
                        });
                    } else {
                        console.log('No products found for this store');
                        productSelect.innerHTML += '<option value="" disabled>لا توجد منتجات في هذا المتجر</option>';
                    }
                    console.log('Product select HTML:', productSelect.innerHTML);
                }
            } catch (error) {
                console.error('خطأ في تحميل المنتجات:', error);
            }
        }
    }

    async function handleProductChange() {
        const productId = this.value;
        
        if (variantSelect) {
            variantSelect.innerHTML = '<option value="">-- اختر المتغير --</option>';
            variantSelect.disabled = !productId;
        }
        if (quantityInput) quantityInput.disabled = !productId;
        if (addProductBtn) addProductBtn.disabled = true;

        if (productId) {
            try {
                const response = await fetch(`/dashboard/api/product-variants/?product_id=${productId}`);
                const data = await response.json();
                variants = data.variants || [];
                if (variantSelect) {
                    variants.forEach(variant => {
                        const optionsText = variant.options_display || 'افتراضي';
                        variantSelect.innerHTML += `<option value="${variant.id}" data-price="${variant.price}">${optionsText} - ${variant.price} ر.س</option>`;
                    });
                }
            } catch (error) {
                console.error('خطأ في تحميل المتغيرات:', error);
            }
        }
    }

    function handleVariantChange() {
        const variantId = this.value;
        if (addProductBtn) addProductBtn.disabled = !variantId;
        updatePrice();
    }

    function updatePrice() {
        const priceDisplay = document.getElementById('price_display');
        if (!variantSelect || !quantityInput || !priceDisplay) return;
        
        const selectedOption = variantSelect.options[variantSelect.selectedIndex];
        if (selectedOption && selectedOption.dataset.price) {
            const price = parseFloat(selectedOption.dataset.price);
            const quantity = parseInt(quantityInput.value) || 1;
            const total = price * quantity;
            priceDisplay.value = `${total.toFixed(2)} ر.س`;
        } else {
            priceDisplay.value = '0.00 ر.س';
        }
    }

    function addProduct() {
        if (!storeSelect || !productSelect || !variantSelect || !quantityInput) return;
        
        const storeId = storeSelect.value;
        const productId = productSelect.value;
        const variantId = variantSelect.value;
        const quantity = parseInt(quantityInput.value);
        
        const selectedOption = variantSelect.options[variantSelect.selectedIndex];
        const price = parseFloat(selectedOption.dataset.price);
        
        const product = {
            storeId: storeId,
            storeName: storeSelect.options[storeSelect.selectedIndex].text,
            productId: productId,
            productName: productSelect.options[productSelect.selectedIndex].text,
            variantId: variantId,
            variantName: selectedOption.text,
            quantity: quantity,
            price: price,
            total: price * quantity
        };

        selectedProducts.push(product);
        updateSelectedProductsDisplay();
        updateTotals();
        resetProductForm();
    }

    function removeProduct(index) {
        selectedProducts.splice(index, 1);
        updateSelectedProductsDisplay();
        updateTotals();
    }

    function updateSelectedProductsDisplay() {
        const container = document.getElementById('selected_products_container');
        if (!container) return;
        
        if (selectedProducts.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-shopping-cart fa-2x mb-2 d-block opacity-50"></i>
                    <p>لم يتم اختيار أي منتجات بعد</p>
                </div>
            `;
            return;
        }

        // Group products by store
        const storeGroups = {};
        selectedProducts.forEach((product, index) => {
            if (!storeGroups[product.storeId]) {
                storeGroups[product.storeId] = {
                    storeName: product.storeName,
                    products: [],
                    total: 0
                };
            }
            storeGroups[product.storeId].products.push({...product, index});
            storeGroups[product.storeId].total += product.total;
        });

        let html = '';
        Object.values(storeGroups).forEach(store => {
            html += `
                <div class="store-group mb-3">
                    <div class="d-flex justify-content-between align-items-center bg-light p-2 rounded">
                        <h6 class="mb-0"><i class="fas fa-store me-2"></i>${store.storeName}</h6>
                        <span class="fw-bold text-success">${store.total.toFixed(2)} ر.س</span>
                    </div>
                    <div class="products-list mt-2">
            `;
            
            store.products.forEach(product => {
                html += `
                    <div class="d-flex justify-content-between align-items-center border-bottom py-2">
                        <div class="flex-grow-1">
                            <div class="fw-medium">${product.productName}</div>
                            <small class="text-muted">${product.variantName}</small>
                        </div>
                        <div class="text-center mx-3">
                            <span class="badge bg-info">${product.quantity}</span>
                        </div>
                        <div class="text-end me-3">
                            <span class="fw-bold">${product.total.toFixed(2)} ر.س</span>
                        </div>
                        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeProduct(${product.index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    function updateTotals() {
        const totalItems = selectedProducts.reduce((sum, product) => sum + product.quantity, 0);
        const grandTotal = selectedProducts.reduce((sum, product) => sum + product.total, 0);
        
        const totalItemsEl = document.getElementById('total_items');
        const grandTotalEl = document.getElementById('id_grand_total');
        const selectedProductsJsonEl = document.getElementById('selected_products_json');
        
        if (totalItemsEl) totalItemsEl.textContent = `${totalItems} عنصر`;
        if (grandTotalEl) grandTotalEl.value = grandTotal.toFixed(2);
        if (selectedProductsJsonEl) selectedProductsJsonEl.value = JSON.stringify(selectedProducts);
    }

    function resetProductForm() {
        if (storeSelect) storeSelect.value = '';
        if (productSelect) {
            productSelect.innerHTML = '<option value="">-- اختر المنتج أولاً --</option>';
            productSelect.disabled = true;
        }
        if (variantSelect) {
            variantSelect.innerHTML = '<option value="">-- اختر المتغير --</option>';
            variantSelect.disabled = true;
        }
        if (quantityInput) {
            quantityInput.value = '1';
            quantityInput.disabled = true;
        }
        if (addProductBtn) addProductBtn.disabled = true;
        
        const priceDisplay = document.getElementById('price_display');
        if (priceDisplay) priceDisplay.value = '0.00 ر.س';
    }

    function updateShippingAddress() {
        const address = {
            name: document.getElementById('shipping_name')?.value || '',
            phone: document.getElementById('shipping_phone')?.value || '',
            city: document.getElementById('shipping_city')?.value || '',
            district: document.getElementById('shipping_district')?.value || '',
            postal_code: document.getElementById('shipping_postal')?.value || '',
            address: document.getElementById('shipping_address')?.value || ''
        };
        
        const shippingAddressEl = document.getElementById('id_shipping_address_snapshot');
        if (shippingAddressEl) {
            shippingAddressEl.value = JSON.stringify(address);
        }
    }

    // Make removeProduct available globally
    window.removeProduct = removeProduct;
    
    // Debug form submission
    const orderFormElement = document.getElementById('order-form');
    if (orderFormElement) {
        orderFormElement.addEventListener('submit', function(e) {
            console.log('Form submission started');
            console.log('Selected products JSON:', document.getElementById('selected_products_json')?.value);
            console.log('Form data:', new FormData(this));
        });
    }
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

// تهيئة WebSocket عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all functions when DOM is ready
    setupDeleteConfirmation();
    initToggleButtons();
    initOrderManagement();
    initCardAnimations();
    initProductVariants();
    initProductFormCategoryLoader();
    
    // تهيئة WebSocket
    initWebSocket();
    
    // ping كل 30 ثانية
    setInterval(keepWebSocketAlive, 30000);
    
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
