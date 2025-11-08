from datetime import timedelta
from django.utils import timezone
from django.contrib.admin import site as admin_site
from django.shortcuts import render
from django.db.models import Count, Sum

from orders.models import Order
from products.models import Product
from accounts.models import User


def metrics_view(request):
    # Ensure only staff via admin_view wrapper in urls
    today = timezone.now().date()
    start_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))
    end_today = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.max.time()))

    # Cards
    orders_today = Order.objects.filter(created_at__date=today).count()
    revenue_today = (
        Order.objects.filter(created_at__date=today)
        .aggregate(total=Sum('grand_total'))['total'] or 0
    )

    # Unified order statuses
    so_pending = Order.objects.filter(created_at__date=today, fulfillment_status=Order.FulfillmentStatus.PENDING).count()
    so_in_delivery = Order.objects.filter(created_at__date=today, fulfillment_status=Order.FulfillmentStatus.SHIPPED).count()

    seven_days_ago = today - timedelta(days=7)
    new_users_7d = User.objects.filter(created_at__date__gte=seven_days_ago).count()

    # Last 14 days orders count
    from collections import OrderedDict
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    orders_by_day = OrderedDict()
    for d in days:
        orders_by_day[d.strftime('%Y-%m-%d')] = 0
    qs = (
        Order.objects.filter(created_at__date__gte=today - timedelta(days=13))
        .extra(select={'day': "date(created_at)"})
        .values('day')
        .annotate(c=Count('id'))
        .order_by('day')
    )
    for row in qs:
        key = row['day'] if isinstance(row['day'], str) else row['day'].strftime('%Y-%m-%d')
        orders_by_day[key] = row['c']

    # Top selling products (by denormalized selling_count)
    top_products = Product.objects.order_by('-selling_count')[:5].values('id', 'name', 'selling_count')

    # Recent orders
    recent_orders = (
        Order.objects.select_related('user', 'store')
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
    }
    return render(request, 'admin/metrics.html', context)
