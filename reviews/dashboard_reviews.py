from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from reviews.models import ProductReview, StoreReview, OrderReview
from products.models import Product
from stores.models import Store
from accounts.models import User


@staff_member_required
def reviews_list_view(request):
    """
    Dashboard list for reviews with basic filters and pagination.
    Shows product reviews and store reviews in the same page using two paginated lists.
    """
    # Filters
    email = request.GET.get('email')
    product_id = request.GET.get('product')
    store_id = request.GET.get('store')
    rating = request.GET.get('rating')

    # Base querysets
    pr_qs = ProductReview.objects.select_related('user', 'product').order_by('-created_at')
    sr_qs = StoreReview.objects.select_related('user', 'store').order_by('-created_at')

    if email:
        pr_qs = pr_qs.filter(user__email__icontains=email)
        sr_qs = sr_qs.filter(user__email__icontains=email)
    if product_id:
        pr_qs = pr_qs.filter(product_id=product_id)
    if store_id:
        sr_qs = sr_qs.filter(store_id=store_id)
    if rating and rating.isdigit():
        pr_qs = pr_qs.filter(rating=int(rating))
        sr_qs = sr_qs.filter(rating=int(rating))

    # Pagination (independent for each list)
    pr_page_number = request.GET.get('pr_page') or 1
    sr_page_number = request.GET.get('sr_page') or 1
    pr_page = Paginator(pr_qs, 20).get_page(pr_page_number)
    sr_page = Paginator(sr_qs, 20).get_page(sr_page_number)

    products = Product.objects.all().values('id', 'name')
    stores = Store.objects.all().values('id', 'name')

    context = {
        'pr_page': pr_page,
        'sr_page': sr_page,
        'filters': {
            'email': email or '',
            'product': product_id or '',
            'store': store_id or '',
            'rating': rating or '',
        },
        'products': list(products),
        'stores': list(stores),
        'nav_active': 'reviews',
    }
    return render(request, 'dashboard/pages/reviews/list.html', context)
