# from datetime import timedelta
# from collections import OrderedDict

# from django.utils import timezone
# from django.contrib.admin.views.decorators import staff_member_required
# from django.shortcuts import render
# from django.db.models import Count, Sum

# from orders.models import Order
# from products.models import Product
# from accounts.models import User
# from stores.models import Store


# @staff_member_required
# def dashboard_view(request):
#     today = timezone.now().date()

#     # Date range filters
#     start = request.GET.get('start')  # YYYY-MM-DD
#     end = request.GET.get('end')      # YYYY-MM-DD

#     # Default range: last 14 days (inclusive)
#     if start and end:
#         try:
#             start_date = timezone.datetime.strptime(start, '%Y-%m-%d').date()
#             end_date = timezone.datetime.strptime(end, '%Y-%m-%d').date()
#             if end_date < start_date:
#                 start_date, end_date = end_date, start_date
#         except ValueError:
#             start_date = today - timedelta(days=13)
#             end_date = today
#     else:
#         start_date = today - timedelta(days=13)
#         end_date = today

#     # Clamp range to max 60 days to avoid heavy queries
#     if (end_date - start_date).days > 60:
#         start_date = end_date - timedelta(days=60)

#     # Cards (computed for the chosen end_date as "today" semantics)
#     orders_today = Order.objects.filter(created_at__date=end_date).count()
#     revenue_today = (
#         Order.objects.filter(created_at__date=end_date)
#         .aggregate(total=Sum('grand_total'))['total'] or 0
#     )
#     # Unified order statuses
#     so_pending = Order.objects.filter(created_at__date__gte=start_date,
#                                       created_at__date__lte=end_date,
#                                       fulfillment_status=Order.FulfillmentStatus.PENDING).count()
#     so_in_delivery = Order.objects.filter(created_at__date__gte=start_date,
#                                           created_at__date__lte=end_date,
#                                           fulfillment_status=Order.FulfillmentStatus.SHIPPED).count()
#     new_users_7d = User.objects.filter(created_at__date__gte=end_date - timedelta(days=7)).count()
    
#     # ✅ إحصائيات المتاجر المحدثة
#     active_stores = Store.get_active_stores().count()
#     pending_store_requests = Store.get_requests().filter(status=Store.StoreStatus.PENDING).count()
#     total_stores = Store.objects.count()

#     # Daily series within range
#     days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
#     orders_by_day = OrderedDict((d.strftime('%Y-%m-%d'), 0) for d in days)
#     qs = (
#         Order.objects.filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
#         .extra(select={'day': "date(created_at)"})
#         .values('day')
#         .annotate(c=Count('id'))
#         .order_by('day')
#     )
#     for row in qs:
#         key = row['day'] if isinstance(row['day'], str) else row['day'].strftime('%Y-%m-%d')
#         orders_by_day[key] = row['c']

#     top_products = Product.objects.order_by('-selling_count')[:5].values('id', 'name', 'selling_count')
#     recent_orders = (
#         Order.objects.select_related('user', 'store')
#         .filter(created_at__date__gte=start_date, created_at__date__lte=end_date)
#         .order_by('-created_at')[:10]
#         .values('id', 'grand_total', 'payment_status', 'fulfillment_status', 'created_at', 'user__email', 'store__name')
#     )

#     context = {
#         'cards': {
#             'orders_today': orders_today,
#             'revenue_today': revenue_today,
#             'so_pending': so_pending,
#             'so_in_delivery': so_in_delivery,
#             'new_users_7d': new_users_7d,
#             'active_stores': active_stores,
#             'pending_store_requests': pending_store_requests,
#             'total_stores': total_stores,
#         },
#         'orders_by_day_labels': list(orders_by_day.keys()),
#         'orders_by_day_values': list(orders_by_day.values()),
#         'top_products': list(top_products),
#         'recent_orders': list(recent_orders),
#         'filters': {
#             'start': start or start_date.strftime('%Y-%m-%d'),
#             'end': end or end_date.strftime('%Y-%m-%d'),
#         },
#         'nav_active': 'overview',
#     }
#     return render(request, 'dashboard/pages/dashboard/index.html', context)

from datetime import timedelta
from collections import OrderedDict

from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate

from orders.models import Order
from products.models import Product
from accounts.models import User


@staff_member_required
def dashboard_view(request):
    today = timezone.now().date()

    # Date range filters
    start = request.GET.get('start')  # YYYY-MM-DD
    end = request.GET.get('end')      # YYYY-MM-DD

    # Default range: last 14 days (inclusive)
    if start and end:
        try:
            start_date = timezone.datetime.strptime(start, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end, '%Y-%m-%d').date()
            if end_date < start_date:
                start_date, end_date = end_date, start_date
        except ValueError:
            start_date = today - timedelta(days=13)
            end_date = today
    else:
        start_date = today - timedelta(days=13)
        end_date = today

    # Clamp range to max 60 days to avoid heavy queries
    if (end_date - start_date).days > 60:
        start_date = end_date - timedelta(days=60)

    # Build aware datetime ranges to avoid __date casts and use indexes
    def day_range(d):
        start_dt = timezone.make_aware(timezone.datetime.combine(d, timezone.datetime.min.time()))
        end_dt = start_dt + timedelta(days=1)
        return start_dt, end_dt

    # Today range (based on end_date)
    today_start, today_end = day_range(end_date)

    # Global selected range [start_date, end_date] inclusive of end_date's day
    range_start, _ = day_range(start_date)
    _, range_end = day_range(end_date)  # exclusive upper bound

    # Cards (computed for the chosen end_date as "today" semantics) in a single aggregate
    today_agg = Order.objects.filter(created_at__gte=today_start, created_at__lt=today_end).aggregate(
        orders_today=Count('id'),
        revenue_today=Sum('grand_total'),
    )
    orders_today = today_agg['orders_today'] or 0
    revenue_today = today_agg['revenue_today'] or 0

    # Unified order statuses within selected range using conditional counts in one query
    status_agg = Order.objects.filter(created_at__gte=range_start, created_at__lt=range_end).aggregate(
        so_pending=Count('id', filter=Q(fulfillment_status=Order.FulfillmentStatus.PENDING)),
        so_in_delivery=Count('id', filter=Q(fulfillment_status=Order.FulfillmentStatus.SHIPPED)),
    )
    so_pending = status_agg['so_pending'] or 0
    so_in_delivery = status_agg['so_in_delivery'] or 0

    # New users in last 7 days (rolling window ending on end_date)
    last7_start = today_end - timedelta(days=7)
    new_users_7d = User.objects.filter(created_at__gte=last7_start).count()

    # Daily series within range
    days = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    orders_by_day = OrderedDict((d.strftime('%Y-%m-%d'), 0) for d in days)
    qs = (
        Order.objects.filter(created_at__gte=range_start, created_at__lt=range_end)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    for row in qs:
        d = row['day']
        key = d if isinstance(d, str) else d.strftime('%Y-%m-%d')
        orders_by_day[key] = row['c']

    top_products = Product.objects.order_by('-selling_count')[:5].values('id', 'name', 'selling_count')
    recent_orders = (
        Order.objects.select_related('user', 'store')
        .filter(created_at__gte=range_start, created_at__lt=range_end)
        .order_by('-created_at')[:10]
        .values('id', 'grand_total', 'payment_status', 'fulfillment_status', 'created_at', 'user__email', 'store__name')
    )

    context = {
        'cards': {
            'orders_today': orders_today,
            'revenue_today': revenue_today,
            'so_pending': so_pending,
            'so_in_delivery': so_in_delivery,
            'new_users_7d': new_users_7d,
        },
        'orders_by_day_labels': list(orders_by_day.keys()),
        'orders_by_day_values': list(orders_by_day.values()),
        'top_products': list(top_products),
        'recent_orders': list(recent_orders),
        'filters': {
            'start': start or start_date.strftime('%Y-%m-%d'),
            'end': end or end_date.strftime('%Y-%m-%d'),
        },
        'nav_active': 'overview',
    }
    return render(request, 'dashboard/pages/dashboard/index.html', context)


