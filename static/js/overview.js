// Dashboard overview functionality from dashboard.js (copied as-is)

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

// تهيئة WebSocket عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart
    setTimeout(initOrdersChart, 100);
    
    // تهيئة WebSocket
    initWebSocket();
    
    // ping كل 30 ثانية
    setInterval(keepWebSocketAlive, 30000);
});