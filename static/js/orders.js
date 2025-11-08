// Orders management functionality from dashboard.js (copied as-is)

// إدارة الطلبات
function initOrderManagement() {
    // Check if we're on the order form page
    const orderForm = document.querySelector('#order-form');
    if (!orderForm) {
        console.log('Order form not found, skipping order management initialization');
        return;
    }

    console.log('Order form found, initializing order management...');

    let variants = [];

    // Load stores on page load
    loadStores();

    // Event Listeners
    const storeSelect = document.getElementById('store_select');
    const productSelect = document.getElementById('product_select');
    const variantSelect = document.getElementById('variant_select');
    const quantityInput = document.getElementById('quantity_input');
    const addProductBtn = document.getElementById('add_product_btn');
    const formStoreSelect = document.getElementById('id_store');
    const grandTotalEl = document.getElementById('id_grand_total');
    const mismatchAlert = document.getElementById('store_mismatch_alert');

    if (storeSelect) storeSelect.addEventListener('change', handleStoreChange);
    if (productSelect) productSelect.addEventListener('change', handleProductChange);
    if (variantSelect) variantSelect.addEventListener('change', handleVariantChange);
    if (quantityInput) quantityInput.addEventListener('input', updatePrice);
    if (addProductBtn) addProductBtn.addEventListener('click', addProduct);
    if (formStoreSelect) formStoreSelect.addEventListener('change', syncStoreSelection);

    // Make grand_total readonly for UX (server recalculates anyway)
    if (grandTotalEl) grandTotalEl.setAttribute('readonly', 'readonly');

    // Initial sync between form store and products store
    syncStoreSelection();

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

    function syncStoreSelection() {
        // If form store has a value, set products store to the same and enforce match
        const currentFormStore = formStoreSelect ? String(formStoreSelect.value || '') : '';
        if (storeSelect && currentFormStore) {
            // If current selection differs, update and trigger change to reload products
            if (String(storeSelect.value || '') !== currentFormStore) {
                storeSelect.value = currentFormStore;
                // Manually trigger change to load products for this store
                if (typeof storeSelect.dispatchEvent === 'function') {
                    storeSelect.dispatchEvent(new Event('change'));
                }
            }
        }
        checkStoreMatch();
    }

    function checkStoreMatch() {
        const currentFormStore = formStoreSelect ? String(formStoreSelect.value || '') : '';
        const currentProductsStore = storeSelect ? String(storeSelect.value || '') : '';

        const matched = !currentFormStore || !currentProductsStore || currentFormStore === currentProductsStore;

        // Toggle alert visibility
        if (mismatchAlert) {
            mismatchAlert.classList.toggle('d-none', matched);
        }
        // Disable product-related controls when mismatched
        const disableControls = !matched;
        if (productSelect) productSelect.disabled = disableControls || !currentProductsStore;
        if (variantSelect) variantSelect.disabled = disableControls || !currentProductsStore;
        if (quantityInput) quantityInput.disabled = disableControls || !currentProductsStore;
        if (addProductBtn) addProductBtn.disabled = disableControls || !currentProductsStore;

        return matched;
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

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initOrderManagement();

    // Live tracking initialization (only runs on order detail page where elements exist)
    try {
        const orderHolder = document.getElementById('order-id');
        const orderId = orderHolder ? orderHolder.getAttribute('data-order-id') : null;
        if (orderId && typeof L !== 'undefined') {
            initOrderLiveTracking(orderId);
        }
    } catch (e) {
        console.warn('Live tracking init skipped:', e);
    }

    // Initialize realtime updates for orders list page when present
    try {
        const ordersTable = document.querySelector('table.table');
        const inOrdersListPage = !!ordersTable;
        if (inOrdersListPage) {
            initOrdersListRealtime();
        }
    } catch (e) {
        console.warn('Orders list realtime init skipped:', e);
    }
});

// Fetch current page and replace the orders table body without full reload
async function refreshOrdersTable(highlightOrderId) {
    try {
        const url = window.location.href;
        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!res.ok) return;
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newTbody = doc.querySelector('table.table tbody');
        const table = document.querySelector('table.table');
        if (newTbody && table) {
            const tbody = table.querySelector('tbody');
            if (tbody) {
                tbody.replaceWith(newTbody);
                // Optional: update count badge if exists
                try {
                    const newCount = doc.querySelector('.card-header .badge');
                    const countEl = document.querySelector('.card-header .badge');
                    if (newCount && countEl) countEl.replaceWith(newCount);
                } catch(_) {}
                // Highlight the newly added order row if present
                if (highlightOrderId) {
                    const row = document.querySelector(`tr[data-order-id="${highlightOrderId}"]`);
                    if (row) {
                        row.classList.add('new-order');
                        setTimeout(() => row.classList.remove('new-order'), 2000);
                    }
                }
            }
        }
    } catch (e) {
        console.warn('Failed to refresh orders table', e);
    }
}

// ===============================================
// Live driver tracking via WebSocket + Leaflet
// ===============================================
function initOrderLiveTracking(orderId) {
    const mapEl = document.getElementById('order-driver-map');
    if (!mapEl) return;

    const infoEl = document.getElementById('driver-location-text');

    // 1) Initialize Leaflet map
    const initialCenter = [24.7136, 46.6753]; // Default center (Riyadh)
    const map = L.map('order-driver-map', { zoomControl: true }).setView(initialCenter, 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(map);

    let driverMarker = null;
    // Custom driver icon (motorbike icon as example)
    const driverIcon = L.icon({
        iconUrl: 'https://cdn-icons-png.flaticon.com/512/2972/2972185.png',
        iconSize: [32, 32],
        iconAnchor: [16, 16],
        tooltipAnchor: [0, -18]
    });
    let firstFix = true;

    function updateDriverLocation(lat, lng, speed, heading, ts) {
        const latLng = [lat, lng];
        if (!driverMarker) {
            driverMarker = L.marker(latLng, { title: 'مندوب التوصيل', icon: driverIcon }).addTo(map);
            try { driverMarker.bindTooltip('مندوب التوصيل'); } catch(_) {}
        } else {
            driverMarker.setLatLng(latLng);
        }

        if (firstFix) {
            map.setView(latLng, 15);
            firstFix = false;
        }

        const timeText = ts ? new Date(ts).toLocaleString() : '';
        if (infoEl) {
            infoEl.textContent = `موقع المندوب: ${lat.toFixed(6)}, ${lng.toFixed(6)}`
                + (speed != null ? ` | السرعة: ${speed} m/s` : '')
                + (heading != null ? ` | الاتجاه: ${heading}°` : '')
                + (timeText ? ` | آخر تحديث: ${timeText}` : '');
        }

        // Rotate marker icon according to heading (basic approach without plugins)
        if (driverMarker && driverMarker._icon && typeof heading === 'number') {
            const iconEl = driverMarker._icon;
            // Leaflet sets translate3d in transform; append rotate while preserving translate
            const baseTransform = iconEl.style.transform || '';
            const noRotate = baseTransform.replace(/\s?rotate\([^)]*\)/, '');
            iconEl.style.transform = `${noRotate} rotate(${heading}deg)`;
            iconEl.style.transformOrigin = '16px 16px';
        }
    }

    // 2) WebSocket connect
    const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${scheme}://${window.location.host}/ws/order/${orderId}/`;
    let socket = null;

    function connectWS() {
        socket = new WebSocket(wsUrl);

        socket.onopen = function() {
            if (infoEl) infoEl.textContent = 'متصل... بانتظار تحديثات الموقع';
        };

        socket.onmessage = function(evt) {
            try {
                const data = JSON.parse(evt.data || '{}');
                if (data.event === 'location_update') {
                    const { lat, lng, speed, heading, ts } = data;
                    if (typeof lat === 'number' && typeof lng === 'number') {
                        updateDriverLocation(lat, lng, speed, heading, ts);
                    }
                }
            } catch (e) {
                console.error('Invalid WS message', e);
            }
        };

        socket.onclose = function() {
            if (infoEl) infoEl.textContent = 'انقطع الاتصال. إعادة المحاولة بعد ثوانٍ...';
            setTimeout(connectWS, 3000);
        };

        socket.onerror = function() {
            if (infoEl) infoEl.textContent = 'حدث خطأ في الاتصال.';
        };
    }

    connectWS();
}

// ===============================================
// Orders list realtime via WebSocket (table only)
// ===============================================
let __ORDERS_LIST_WS__ = null;

function initOrdersListRealtime() {
    if (!window.WebSocket) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;
    try {
        __ORDERS_LIST_WS__ = new WebSocket(wsUrl);
        __ORDERS_LIST_WS__.onmessage = function(evt) {
            try {
                const data = JSON.parse(evt.data || '{}');
                handleOrdersListWsMessage(data);
            } catch (e) {
                console.error('Orders list WS parse error', e);
            }
        };
    } catch (e) {
        console.error('Orders list WS init error', e);
    }
}

function handleOrdersListWsMessage(data) {
    if (!data || !data.type) return;
    if (data.type === 'order_status_changed' && data.order && data.order.id) {
        const o = data.order;
        const row = document.querySelector(`tr[data-order-id="${o.id}"]`);
        let updated = false;
        if (row) {
            const pOk = updatePaymentBadgeRow(row, o.payment_status || o.paymentStatus) === true;
            const fOk = updateFulfillmentBadgeRow(row, o.fulfillment_status || o.fulfillmentStatus || o.status) === true;
            if (o.grand_total || o.total_amount) {
                const amountCell = row.querySelector('td:nth-child(5) .fw-bold');
                if (amountCell) {
                    const val = parseFloat(o.grand_total || o.total_amount || 0).toFixed(2);
                    amountCell.textContent = val;
                    updated = true;
                }
            }
            updated = updated || pOk || fOk;
        }
        if (!row || !updated) {
            refreshOrdersTable(o.id);
        }
    } else if (data.type === 'new_order' && data.order && data.order.id) {
        // Refresh only the table body so filters and pagination remain honored
        refreshOrdersTable(data.order.id);
    }
}

function updatePaymentBadgeRow(row, status) {
    if (!status) return false;
    const container = row.querySelector('td:nth-child(6)');
    if (!container) return false;
    const map = {
        'PENDING_PAYMENT':'<span class="badge bg-warning bg-opacity-10 text-warning border border-warning"><i class="fas fa-clock me-1"></i>في انتظار الدفع</span>',
        'PAID':'<span class="badge bg-success bg-opacity-10 text-success border border-success"><i class="fas fa-check me-1"></i>مدفوع</span>',
        'CANCELLED':'<span class="badge bg-danger bg-opacity-10 text-danger border border-danger"><i class="fas fa-times me-1"></i>ملغي (دفع)</span>',
        'REFUNDED':'<span class="badge bg-secondary bg-opacity-10 text-secondary border border-secondary"><i class="fas fa-undo me-1"></i>مسترجع</span>'
    };
    const html = map[String(status).toUpperCase()] || '';
    if (html) {
        const wrappers = container.querySelectorAll('.badge');
        if (wrappers.length) {
            wrappers[0].outerHTML = html;
            return true;
        }
    }
    return false;
}

function updateFulfillmentBadgeRow(row, status) {
    if (!status) return false;
    const container = row.querySelector('td:nth-child(6)');
    if (!container) return false;
    const map = {
        'PENDING':'<span class="badge bg-info bg-opacity-10 text-info border border-info"><i class="fas fa-hourglass-half me-1"></i>قيد المراجعة</span>',
        'ACCEPTED':'<span class="badge bg-primary bg-opacity-10 text-primary border border-primary"><i class="fas fa-clipboard-check me-1"></i>تم القبول</span>',
        'PREPARING':'<span class="badge bg-primary bg-opacity-10 text-primary border border-primary"><i class="fas fa-tools me-1"></i>قيد التجهيز</span>',
        'SHIPPED':'<span class="badge bg-primary bg-opacity-10 text-primary border border-primary"><i class="fas fa-truck me-1"></i>تم الشحن</span>',
        'DELIVERED':'<span class="badge bg-success bg-opacity-10 text-success border border-success"><i class="fas fa-box-open me-1"></i>تم التوصيل</span>',
        'REJECTED':'<span class="badge bg-danger bg-opacity-10 text-danger border border-danger"><i class="fas fa-ban me-1"></i>مرفوض</span>'
    };
    const html = map[String(status).toUpperCase()] || '';
    if (html) {
        const wrappers = container.querySelectorAll('.badge');
        if (wrappers.length >= 2) {
            wrappers[1].outerHTML = html;
            return true;
        }
    }
    return false;
}