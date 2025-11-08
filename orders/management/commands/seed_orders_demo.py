import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from stores.models import PlatformCategory, Store
from products.models import ProductCategory, Product, ProductVariant, ProductImage
from orders.models import CartItem, Order, OrderItem


class Command(BaseCommand):
    help = "Seed demo data for orders workflow (users, stores, products, cart, orders)."

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete previously seeded demo data before seeding again')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Seeding demo data...'))
        if options.get('flush'):
            self._flush_demo()

        User = get_user_model()

        # Create users
        vendor_email = 'vendor@example.com'
        customer_email = 'customer@example.com'
        vendor = User.objects.filter(email=vendor_email).first()
        if not vendor:
            try:
                vendor = User.objects.create_user(email=vendor_email, password='Pass1234!', is_vendor=True, is_staff=True)
            except TypeError:
                # Fallback if create_user requires username
                vendor = User.objects.create_user(username='vendor', email=vendor_email, password='Pass1234!', is_vendor=True, is_staff=True)
        customer = User.objects.filter(email=customer_email).first()
        if not customer:
            try:
                customer = User.objects.create_user(email=customer_email, password='Pass1234!', is_vendor=False)
            except TypeError:
                customer = User.objects.create_user(username='customer', email=customer_email, password='Pass1234!', is_vendor=False)

        self.stdout.write(self.style.SUCCESS(f"Users ready: vendor={vendor.email}, customer={customer.email}"))

        # Platform category
        pc, _ = PlatformCategory.objects.get_or_create(name='Electronics', defaults={'image_url': ''})

        # Store for vendor
        store, _ = Store.objects.get_or_create(owner=vendor, name='Tech Hub', defaults={
            'platform_category': pc,
            'description': 'Gadgets and electronics',
            'logo_url': '',
            'is_active': True,
        })

        # Product categories (tree)
        cat_root, _ = ProductCategory.objects.get_or_create(store=store, name='Phones', parent=None)
        cat_child, _ = ProductCategory.objects.get_or_create(store=store, name='Smartphones', parent=cat_root)

        # Products and variants
        products = []
        for i in range(1, 4):
            p, _ = Product.objects.get_or_create(
                store=store,
                name=f"Phone Model {i}",
                defaults={
                    'category': cat_child,
                    'description': f"Demo smartphone {i}",
                    'specifications': {'Screen': '6.1 inch', 'RAM': f'{4+i}GB'},
                    'cover_image_url': '',
                    'average_rating': 4.2,
                    'review_count': random.randint(1, 50),
                    'selling_count': random.randint(10, 200),
                }
            )
            # Variants
            for storage in (64, 128):
                v, _ = ProductVariant.objects.get_or_create(
                    product=p,
                    options={'color': 'Black', 'storage': f'{storage}GB'},
                    defaults={
                        'price': Decimal('299.99') + Decimal(i * 50) + Decimal(storage/100),
                        'sku': f"P{i}-{storage}",
                        'cover_image_url': '',
                    }
                )
            products.append(p)

        # Optional: one image per product
        for p in products:
            ProductImage.objects.get_or_create(product=p, image_url='https://via.placeholder.com/300', display_order=0)

        # Create some cart items for the customer
        variants = list(ProductVariant.objects.filter(product__in=products)[:3])
        for idx, v in enumerate(variants, start=1):
            CartItem.objects.get_or_create(user=customer, variant=v, defaults={'quantity': idx})

        # Create demo orders (one per store) from those cart items (independent of API)
        cart_items = list(CartItem.objects.filter(user=customer).select_related('variant', 'variant__product', 'variant__product__store'))
        if cart_items:
            # group by store
            groups = {}
            for ci in cart_items:
                s = ci.variant.product.store
                groups.setdefault(s.id, {'store': s, 'items': []})['items'].append(ci)

            for store_id, data in groups.items():
                order = Order.objects.create(
                    user=customer,
                    store=data['store'],
                    grand_total=0,
                    shipping_address_snapshot={'name': 'Ahmed', 'city': 'Cairo', 'street': 'Street 1', 'phone': '01000000000'},
                )
                total = Decimal('0')
                for ci in data['items']:
                    OrderItem.objects.create(
                        order=order,
                        variant=ci.variant,
                        quantity=ci.quantity,
                        price_at_purchase=ci.variant.price,
                        product_name_snapshot=ci.variant.product.name,
                        variant_options_snapshot=ci.variant.options or {},
                    )
                    total += ci.variant.price * ci.quantity
                order.grand_total = total
                order.save(update_fields=['grand_total'])

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))
