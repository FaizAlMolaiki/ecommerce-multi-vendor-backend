# from django.contrib.admin.views.decorators import staff_member_required
# from django.contrib import messages
# from django.core.paginator import Paginator
# from django.db.models import Q
# from django.db import transaction
# from django.http import HttpResponse
# from django.shortcuts import get_object_or_404, redirect, render
# import json
# from decimal import Decimal

# from orders.models import Order, OrderItem
# from orders.forms import OrderForm, OrderDeleteForm, OrderStatusForm
# from products.models import ProductVariant
# from stores.models import Store
# from accounts.models import User


# @staff_member_required
# def orders_list_view(request):
#     """List orders with filters and pagination, and optional CSV export via ?export=1"""
#     qs = Order.objects.select_related('user', 'store').order_by('-created_at')

#     # Filters
#     payment_status = request.GET.get('payment_status')
#     fulfillment_status = request.GET.get('fulfillment_status')
#     email = request.GET.get('user_email')  # تصحيح اسم المعامل
#     start = request.GET.get('start_date')  # تصحيح اسم المعامل
#     end = request.GET.get('end_date')      # تصحيح اسم المعامل

#     if payment_status:
#         qs = qs.filter(payment_status=payment_status)
#     if fulfillment_status:
#         qs = qs.filter(fulfillment_status=fulfillment_status)
#     if email:
#         qs = qs.filter(Q(user__email__icontains=email))
#     if start:
#         qs = qs.filter(created_at__date__gte=start)
#     if end:
#         qs = qs.filter(created_at__date__lte=end)

#     # Export CSV
#     if request.GET.get('export') == '1':
#         import csv
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
#         writer = csv.writer(response)
#         writer.writerow(['ID', 'Store', 'User Email', 'Grand Total', 'Payment Status', 'Fulfillment Status', 'Created At'])
#         for o in qs:
#             writer.writerow([o.id, getattr(o.store, 'name', ''), getattr(o.user, 'email', ''), o.grand_total, o.payment_status, o.fulfillment_status, o.created_at.isoformat()])
#         return response

#     # Pagination
#     page_number = request.GET.get('page') or 1
#     paginator = Paginator(qs, 20)
#     page_obj = paginator.get_page(page_number)

#     context = {
#         'page_obj': page_obj,
#         'filters': {
#             'payment_status': payment_status or '',
#             'fulfillment_status': fulfillment_status or '',
#             'user_email': email or '',
#             'start_date': start or '',
#             'end_date': end or '',
#         },
#         'payment_status_choices': [s for s, _ in Order.PaymentStatus.choices],
#         'fulfillment_status_choices': [s for s, _ in Order.FulfillmentStatus.choices],
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/list.html', context)


# @staff_member_required
# def order_create_view(request):
#     """إنشاء طلب جديد"""
#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # إنشاء الطلب (موحَّد ومربوط بمتجر واحد)
#                     order = form.save()
                    
#                     # معالجة المنتجات المختارة: سيتم قبول عناصر من نفس متجر الطلب فقط
#                     success = process_selected_products(request, order)
                    
#                     if success:
#                         messages.success(request, f'تم إنشاء الطلب #{order.id} بنجاح')
#                         return redirect('dashboard-order-detail', order_id=order.id)
#                     else:
#                         messages.error(request, 'فشل في معالجة المنتجات المختارة')
#             except Exception as e:
#                 messages.error(request, f'حدث خطأ أثناء إنشاء الطلب: {str(e)}')
#         else:
#             messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
#     else:
#         form = OrderForm()
    
#     context = {
#         'form': form,
#         'title': 'إنشاء طلب جديد',
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/form.html', context)


# @staff_member_required
# def order_detail_view(request, order_id: int):
#     order = get_object_or_404(
#         Order.objects.select_related('user', 'store').prefetch_related('items'),
#         pk=order_id,
#     )

#     # Handle actions: mark paid, change store order status
#     if request.method == 'POST':
#         action = request.POST.get('action')
#         if action == 'mark_paid':
#             if order.payment_status != Order.PaymentStatus.PAID:
#                 order.payment_status = Order.PaymentStatus.PAID
#                 order.save(update_fields=['payment_status'])
#                 messages.success(request, 'تم وسم الطلب كمدفوع')
#             else:
#                 messages.info(request, 'هذا الطلب موسوم مسبقاً كمدفوع')
#             return redirect('dashboard-order-detail', order_id=order.id)
#         elif action == 'change_status':
#             new_payment_status = request.POST.get('payment_status')
#             new_fulfillment_status = request.POST.get('fulfillment_status')
#             changed = False
#             if new_payment_status in {s for s, _ in Order.PaymentStatus.choices}:
#                 order.payment_status = new_payment_status
#                 changed = True
#             if new_fulfillment_status in {s for s, _ in Order.FulfillmentStatus.choices}:
#                 order.fulfillment_status = new_fulfillment_status
#                 changed = True
#             if changed:
#                 order.save(update_fields=['payment_status', 'fulfillment_status'])
#                 messages.success(request, 'تم تحديث حالات الطلب')
#             else:
#                 messages.error(request, 'حالات غير صالحة')
#             return redirect('dashboard-order-detail', order_id=order.id)

#     context = {
#         'order': order,
#         'items': order.items.all(),
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/detail.html', context)




# @staff_member_required
# def order_edit_view(request, order_id: int):
#     """تعديل بيانات الطلب"""
#     order = get_object_or_404(Order, pk=order_id)
    
#     if request.method == 'POST':
#         form = OrderForm(request.POST, instance=order)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # تحديث الطلب الرئيسي
#                     order = form.save()

#                     # قراءة المنتجات المختارة من الطلب
#                     products_json = request.POST.get('selected_products', '[]')

#                     # إذا قام المستخدم بإرسال منتجات مختارة، نقوم باستبدال العناصر
#                     # أما إذا كانت فارغة (لم يفتح/يستخدم إدارة العناصر)، نترك العناصر كما هي
#                     try:
#                         submitted_products = json.loads(products_json)
#                     except Exception:
#                         submitted_products = []

#                     if submitted_products:
#                         # حذف العناصر الموجودة وإعادة إنشائها من المدخلات الجديدة
#                         OrderItem.objects.filter(order=order).delete()
#                         success = process_selected_products(request, order)
#                         if not success:
#                             raise Exception('فشل في معالجة المنتجات المختارة عند التعديل')
#                     else:
#                         messages.info(request, 'لم يتم تعديل عناصر الطلب. تم الاحتفاظ بالعناصر الحالية كما هي.')

#                     messages.success(request, f'تم تحديث الطلب #{order.id} بنجاح')
#                     return redirect('dashboard-order-detail', order_id=order.id)
#             except Exception as e:
#                 messages.error(request, f'حدث خطأ أثناء تحديث الطلب: {str(e)}')
#         else:
#             messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
#     else:
#         form = OrderForm(instance=order)
    
#     context = {
#         'form': form,
#         'order': order,
#         'title': f'تعديل الطلب #{order.id}',
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/form.html', context)


# @staff_member_required
# def order_delete_view(request, order_id: int):
#     """حذف الطلب"""
#     order = get_object_or_404(Order, pk=order_id)
    
#     # التحقق من وجود بيانات مرتبطة
#     store_orders_count = 0
#     total_items_count = order.items.count()
    
#     if request.method == 'POST':
#         form = OrderDeleteForm(order, request.POST)
#         if form.is_valid():
#             order_id_display = order.id
#             user_email = getattr(order.user, 'email', 'عميل غير محدد')
            
#             # حذف الطلب مع جميع البيانات المرتبطة
#             with transaction.atomic():
#                 # حذف عناصر الطلب ثم الطلب
#                 OrderItem.objects.filter(order=order).delete()
#                 order.delete()
            
#             messages.success(request, f'تم حذف الطلب #{order_id_display} للعميل "{user_email}" بنجاح')
#             return redirect('dashboard-orders')
#         else:
#             messages.error(request, 'يرجى تأكيد الحذف')
#     else:
#         form = OrderDeleteForm(order)
    
#     context = {
#         'form': form,
#         'order': order,
#         'object': order,
#         'store_orders_count': store_orders_count,
#         'total_items_count': total_items_count,
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/delete.html', context)


# @staff_member_required
# def order_status_change_view(request, order_id: int):
#     """تغيير حالة الطلب"""
#     order = get_object_or_404(Order, pk=order_id)
    
#     if request.method == 'POST':
#         form = OrderStatusForm(order, request.POST)
#         if form.is_valid():
#             old_payment, old_full = order.payment_status, order.fulfillment_status
#             order.payment_status = form.cleaned_data['payment_status']
#             order.fulfillment_status = form.cleaned_data['fulfillment_status']
#             order.save(update_fields=['payment_status', 'fulfillment_status'])
#             messages.success(request, f'تم تغيير حالة الطلب (الدفع: {old_payment} → {order.payment_status}) (التجهيز: {old_full} → {order.fulfillment_status})')
#             return redirect('dashboard-order-detail', order_id=order.id)
#         else:
#             messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
#     else:
#         form = OrderStatusForm(order)
    
#     context = {
#         'form': form,
#         'order': order,
#         'title': f'تغيير حالة الطلب #{order.id}',
#         'nav_active': 'orders',
#     }
#     return render(request, 'dashboard/pages/orders/status_form.html', context)


# def process_selected_products(request, order):
#     """معالجة المنتجات المختارة وإنشاء عناصر للطلب الموحَّد (لنفس متجر الطلب فقط)"""
#     try:
#         # جلب بيانات المنتجات من النموذج
#         products_json = request.POST.get('selected_products', '[]')
#         products_data = json.loads(products_json)
        
#         if not products_data:
#             return True
        
#         # إنشاء عناصر مرتبطة بالطلب فقط إن كانت من نفس متجر الطلب
#         total = Decimal('0')
#         added_count = 0
#         skipped_count = 0
#         for product in products_data:
#             try:
#                 variant = ProductVariant.objects.get(id=product.get('variantId'))
#             except ProductVariant.DoesNotExist:
#                 continue
#             # تخطّي منتجات لا تنتمي لمتجر الطلب
#             if variant.product.store_id != order.store_id:
#                 skipped_count += 1
#                 continue
#             quantity = int(product.get('quantity', 1))
#             price = Decimal(str(product.get('price', 0)))
#             OrderItem.objects.create(
#                 order=order,
#                 variant=variant,
#                 quantity=quantity,
#                 price_at_purchase=price,
#                 product_name_snapshot=variant.product.name,
#                 variant_options_snapshot=variant.options or {}
#             )
#             total += price * quantity
#             added_count += 1
        
#         # تحديث الإجمالي للطلب
#         order.grand_total = total
#         order.save(update_fields=['grand_total'])
#         # تنبيهات للمستخدم حسب النتائج
#         if added_count == 0 and products_data:
#             messages.error(request, 'لم يتم إضافة أي عناصر للطلب لأن جميع المنتجات المختارة لا تنتمي لنفس متجر الطلب. يرجى التأكد من تطابق المتجر في أعلى النموذج مع المتجر المختار في قسم المنتجات.')
#             return False
#         if skipped_count > 0:
#             messages.warning(request, f'تم تجاهل {skipped_count} منتج/منتجات لأنها لا تنتمي لنفس متجر الطلب.')
#         return True
#     except Exception as e:
#         print(f"Error in process_selected_products: {str(e)}")
#         return False
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import json
from decimal import Decimal

from orders.models import Order, OrderItem
from orders.forms import OrderForm, OrderDeleteForm, OrderStatusForm
from products.models import ProductVariant
from stores.models import Store
from accounts.models import User
from orders.services.pricing_utils import (
    build_cart_items_from_variants,
    compute_order_totals,
)
from project.websocket_utils import notify_new_order, notify_order_status_change


@staff_member_required
def orders_list_view(request):
    """List orders with filters and pagination, and optional CSV export via ?export=1"""
    qs = (
        Order.objects.select_related('user', 'store')
        .annotate(items_count=Count('items'))
        .order_by('-created_at')
    )

    # Filters
    payment_status = request.GET.get('payment_status')
    fulfillment_status = request.GET.get('fulfillment_status')
    email = request.GET.get('user_email')  # تصحيح اسم المعامل
    start = request.GET.get('start_date')  # تصحيح اسم المعامل
    end = request.GET.get('end_date')      # تصحيح اسم المعامل
    amount_range = request.GET.get('amount_range')  # نطاق المبلغ (اختياري)

    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    if fulfillment_status:
        qs = qs.filter(fulfillment_status=fulfillment_status)
    if email:
        qs = qs.filter(Q(user__email__icontains=email))
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    # Amount range filter
    if amount_range:
        try:
            if amount_range == '0-100':
                qs = qs.filter(grand_total__lt=100)
            elif amount_range == '100-500':
                qs = qs.filter(grand_total__gte=100, grand_total__lt=500)
            elif amount_range == '500-1000':
                qs = qs.filter(grand_total__gte=500, grand_total__lt=1000)
            elif amount_range == '1000+':
                qs = qs.filter(grand_total__gte=1000)
        except Exception:
            pass

    # Export CSV
    if request.GET.get('export') == '1':
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Store', 'User Email', 'Grand Total', 'Payment Status', 'Fulfillment Status', 'Created At'])
        for o in qs:
            writer.writerow([o.id, getattr(o.store, 'name', ''), getattr(o.user, 'email', ''), o.grand_total, o.payment_status, o.fulfillment_status, o.created_at.isoformat()])
        return response

    # Pagination
    page_number = request.GET.get('page') or 1
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(page_number)

    # Stats cards (global overview)
    today = timezone.now().date()
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__date=today).count()
    pending_orders = Order.objects.filter(fulfillment_status=Order.FulfillmentStatus.PENDING).count()
    completed_orders = Order.objects.filter(fulfillment_status=Order.FulfillmentStatus.DELIVERED).count()

    context = {
        'page_obj': page_obj,
        'filters': {
            'payment_status': payment_status or '',
            'fulfillment_status': fulfillment_status or '',
            'user_email': email or '',
            'start_date': start or '',
            'end_date': end or '',
            'amount_range': amount_range or '',
        },
        'payment_status_choices': [s for s, _ in Order.PaymentStatus.choices],
        'fulfillment_status_choices': [s for s, _ in Order.FulfillmentStatus.choices],
        'nav_active': 'orders',
        # Stats for header cards
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
    }
    return render(request, 'dashboard/pages/orders/list.html', context)


@staff_member_required
def order_create_view(request):
    """إنشاء طلب جديد"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # إنشاء الطلب (موحَّد ومربوط بمتجر واحد)
                    order = form.save()
                    
                    # معالجة المنتجات المختارة: سيتم قبول عناصر من نفس متجر الطلب فقط
                    success = process_selected_products(request, order)
                    
                    if success:
                        messages.success(request, f'تم إنشاء الطلب #{order.id} بنجاح')
                        try:
                            notify_new_order(order)
                        except Exception as _e:
                            print(f"Failed to send order notification: {_e}")
                        return redirect('dashboard-order-detail', order_id=order.id)
                    else:
                        messages.error(request, 'فشل في معالجة المنتجات المختارة')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إنشاء الطلب: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = OrderForm()
    
    context = {
        'form': form,
        'title': 'إنشاء طلب جديد',
        'nav_active': 'orders',
    }
    return render(request, 'dashboard/pages/orders/form.html', context)


@staff_member_required
def order_detail_view(request, order_id: int):
    order = get_object_or_404(
        Order.objects.select_related('user', 'store').prefetch_related('items'),
        pk=order_id,
    )

    # Handle actions: mark paid, change store order status
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_paid':
            if order.payment_status != Order.PaymentStatus.PAID:
                order.payment_status = Order.PaymentStatus.PAID
                order.save(update_fields=['payment_status'])
                try:
                    notify_order_status_change(order)
                except Exception as _e:
                    print(f"Failed to send order status notification: {_e}")
                messages.success(request, 'تم وسم الطلب كمدفوع')
            else:
                messages.info(request, 'هذا الطلب موسوم مسبقاً كمدفوع')
            return redirect('dashboard-order-detail', order_id=order.id)
        elif action == 'change_status':
            new_payment_status = request.POST.get('payment_status')
            new_fulfillment_status = request.POST.get('fulfillment_status')
            changed = False
            if new_payment_status in {s for s, _ in Order.PaymentStatus.choices}:
                order.payment_status = new_payment_status
                changed = True
            if new_fulfillment_status in {s for s, _ in Order.FulfillmentStatus.choices}:
                order.fulfillment_status = new_fulfillment_status
                changed = True
            if changed:
                order.save(update_fields=['payment_status', 'fulfillment_status'])
                messages.success(request, 'تم تحديث حالات الطلب')
                try:
                    notify_order_status_change(order)
                except Exception as _e:
                    print(f"Failed to send order status notification: {_e}")
            else:
                messages.error(request, 'حالات غير صالحة')
            return redirect('dashboard-order-detail', order_id=order.id)

    # Compute pricing snapshot for display (supports optional coupon via GET ?coupon=CODE)
    items_qs = order.items.all()
    variant_qty_list = []
    for oi in items_qs:
        if oi.variant_id and oi.quantity:
            variant_qty_list.append((oi.variant, oi.quantity))
    cart_items = build_cart_items_from_variants(variant_qty_list)
    coupon_code = request.GET.get('coupon')
    subtotal, computed_grand, pricing = compute_order_totals(
        order.user_id,
        cart_items,
        delivery_fee=order.delivery_fee or Decimal('0'),
        currency='SAR',
        coupon_code=coupon_code,
    )

    context = {
        'order': order,
        'items': items_qs,
        'nav_active': 'orders',
        'pricing': pricing,
        'subtotal': subtotal,
        'computed_grand_total': computed_grand,
        'coupon_code': coupon_code or '',
    }
    return render(request, 'dashboard/pages/orders/detail.html', context)




@staff_member_required
def order_edit_view(request, order_id: int):
    """تعديل بيانات الطلب"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # تحديث الطلب الرئيسي
                    order = form.save()

                    # قراءة المنتجات المختارة من الطلب
                    products_json = request.POST.get('selected_products', '[]')

                    # إذا قام المستخدم بإرسال منتجات مختارة، نقوم باستبدال العناصر
                    # أما إذا كانت فارغة (لم يفتح/يستخدم إدارة العناصر)، نترك العناصر كما هي
                    try:
                        submitted_products = json.loads(products_json)
                    except Exception:
                        submitted_products = []

                    if submitted_products:
                        # حذف العناصر الموجودة وإعادة إنشائها من المدخلات الجديدة
                        OrderItem.objects.filter(order=order).delete()
                        success = process_selected_products(request, order)
                        if not success:
                            raise Exception('فشل في معالجة المنتجات المختارة عند التعديل')
                    else:
                        messages.info(request, 'لم يتم تعديل عناصر الطلب. تم الاحتفاظ بالعناصر الحالية كما هي.')

                    messages.success(request, f'تم تحديث الطلب #{order.id} بنجاح')
                    return redirect('dashboard-order-detail', order_id=order.id)
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء تحديث الطلب: {str(e)}')
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = OrderForm(instance=order)
    
    context = {
        'form': form,
        'order': order,
        'title': f'تعديل الطلب #{order.id}',
        'nav_active': 'orders',
    }
    return render(request, 'dashboard/pages/orders/form.html', context)


@staff_member_required
def order_delete_view(request, order_id: int):
    """حذف الطلب"""
    order = get_object_or_404(Order, pk=order_id)
    
    # التحقق من وجود بيانات مرتبطة
    store_orders_count = 0
    total_items_count = order.items.count()
    
    if request.method == 'POST':
        form = OrderDeleteForm(order, request.POST)
        if form.is_valid():
            order_id_display = order.id
            user_email = getattr(order.user, 'email', 'عميل غير محدد')
            
            # حذف الطلب مع جميع البيانات المرتبطة
            with transaction.atomic():
                # حذف عناصر الطلب ثم الطلب
                OrderItem.objects.filter(order=order).delete()
                order.delete()
            
            messages.success(request, f'تم حذف الطلب #{order_id_display} للعميل "{user_email}" بنجاح')
            return redirect('dashboard-orders')
        else:
            messages.error(request, 'يرجى تأكيد الحذف')
    else:
        form = OrderDeleteForm(order)
    
    context = {
        'form': form,
        'order': order,
        'object': order,
        'store_orders_count': store_orders_count,
        'total_items_count': total_items_count,
        'nav_active': 'orders',
    }
    return render(request, 'dashboard/pages/orders/delete.html', context)


@staff_member_required
def order_status_change_view(request, order_id: int):
    """تغيير حالة الطلب"""
    order = get_object_or_404(Order, pk=order_id)
    
    if request.method == 'POST':
        form = OrderStatusForm(order, request.POST)
        if form.is_valid():
            old_payment, old_full = order.payment_status, order.fulfillment_status
            order.payment_status = form.cleaned_data['payment_status']
            order.fulfillment_status = form.cleaned_data['fulfillment_status']
            order.save(update_fields=['payment_status', 'fulfillment_status'])
            messages.success(request, f'تم تغيير حالة الطلب (الدفع: {old_payment} → {order.payment_status}) (التجهيز: {old_full} → {order.fulfillment_status})')
            return redirect('dashboard-order-detail', order_id=order.id)
        else:
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')
    else:
        form = OrderStatusForm(order)
    
    context = {
        'form': form,
        'order': order,
        'object': order,
        'title': f'تغيير حالة الطلب #{order.id}',
        'nav_active': 'orders',
    }
    return render(request, 'dashboard/pages/orders/status_form.html', context)


def process_selected_products(request, order):
    """معالجة المنتجات المختارة وإنشاء عناصر للطلب الموحَّد (لنفس متجر الطلب فقط)"""
    try:
        # جلب بيانات المنتجات من النموذج
        products_json = request.POST.get('selected_products', '[]')
        products_data = json.loads(products_json)
        
        if not products_data:
            return True
        
        # إنشاء عناصر مرتبطة بالطلب فقط إن كانت من نفس متجر الطلب
        added_count = 0
        skipped_count = 0
        variant_qty_list = []
        for product in products_data:
            try:
                variant = ProductVariant.objects.select_related('product', 'product__store').get(id=product.get('variantId'))
            except ProductVariant.DoesNotExist:
                continue
            # تخطّي منتجات لا تنتمي لمتجر الطلب
            if variant.product.store_id != order.store_id:
                skipped_count += 1
                continue
            quantity = int(product.get('quantity', 1))
            unit_price = variant.price  # السعر من قاعدة البيانات، لا من POST

            # إنشاء عنصر الطلب بسعر اللقطة من قاعدة البيانات
            OrderItem.objects.create(
                order=order,
                variant=variant,
                quantity=quantity,
                price_at_purchase=unit_price,
                product_name_snapshot=variant.product.name,
                variant_options_snapshot=variant.options or {}
            )

            # جمع القائمة لبناء عناصر التسعير لاحقاً عبر الخدمة المشتركة
            variant_qty_list.append((variant, quantity))

            added_count += 1

        # استخدام الخدمة الموحدة لبناء عناصر السلة والحساب
        cart_items = build_cart_items_from_variants(variant_qty_list)
        coupon_code = request.POST.get('coupon_code')
        subtotal, grand_total, pricing = compute_order_totals(
            order.user_id,
            cart_items,
            delivery_fee=order.delivery_fee or Decimal('0'),
            currency='SAR',
            coupon_code=coupon_code,
        )
        order.grand_total = grand_total
        order.save(update_fields=['grand_total'])
        # Informational message about applied discount if any
        try:
            disc = pricing.get('discounts_total')
            rules = pricing.get('applied_rules') or []
            if disc and str(disc) != '0':
                if rules:
                    messages.success(request, f"تم تطبيق خصم بقيمة {disc} ر.س عبر '{rules[0].get('name')}'")
                else:
                    messages.success(request, f"تم تطبيق خصم بقيمة {disc} ر.س")
        except Exception:
            pass
        # تنبيهات للمستخدم حسب النتائج
        if added_count == 0 and products_data:
            messages.error(request, 'لم يتم إضافة أي عناصر للطلب لأن جميع المنتجات المختارة لا تنتمي لنفس متجر الطلب. يرجى التأكد من تطابق المتجر في أعلى النموذج مع المتجر المختار في قسم المنتجات.')
            return False
        if skipped_count > 0:
            messages.warning(request, f'تم تجاهل {skipped_count} منتج/منتجات لأنها لا تنتمي لنفس متجر الطلب.')
        return True
    except Exception as e:
        print(f"Error in process_selected_products: {str(e)}")
        return False
