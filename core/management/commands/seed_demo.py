import random
import string
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from accounts.models import User, UserAddress
from stores.models import Store, PlatformCategory
from products.models import ProductCategory, Product, ProductVariant, ProductImage
from orders.models import CartItem, Order, OrderItem
from reviews.models import ProductReview, StoreReview, OrderReview
from wishlist.models import UserStoreFavorite, UserProductFavorite
from pricing.models import Coupon, Promotion, Offer
from notifications.models import Notification, FCMDevice
from driver.models import DeliveryProfile


DEMO_TAG = "[DEMO]"


class Command(BaseCommand):
    help = "Seed demo data for the e-commerce multi-vendor project"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5, help="Number of customer users to create")
        parser.add_argument("--vendors", type=int, default=3, help="Number of vendor users to create")
        parser.add_argument("--stores", type=int, default=3, help="Number of stores to create")
        parser.add_argument("--products", type=int, default=5, help="Products per store")
        parser.add_argument("--variants", type=int, default=3, help="Variants per product (approx)")
        parser.add_argument("--orders", type=int, default=10, help="Number of orders to create")
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data before seeding")

    def handle(self, *args, **options):
        start = timezone.now()
        if options["reset"]:
            self._reset_demo_data()
            self.stdout.write(self.style.WARNING("Existing demo data removed."))

        with transaction.atomic():
            users = self._ensure_users(options["users"], options["vendors"])
            stores = self._ensure_stores(options["stores"], users["vendors"])
            categories = self._ensure_categories(stores)
            products = self._ensure_products(stores, categories, per_store=options["products"], variants_per_product=options["variants"])
            self._ensure_wishlist(users, stores, products)
            coupons, promotions, offers = self._ensure_pricing(stores, products)
            delivery_profiles = self._ensure_delivery_profiles(users)
            orders = self._ensure_orders(options["orders"], users, stores, products)
            self._ensure_reviews(users, stores, products, orders)
            self._ensure_notifications(users)

        elapsed = (timezone.now() - start).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"Seed complete in {elapsed:.2f}s"))

    # ---------- Utilities ----------

    def _rand_word(self, n=8):
        return ''.join(random.choices(string.ascii_lowercase, k=n))

    def _rand_price(self):
        return round(random.uniform(5.0, 500.0), 2)

    def _rand_image(self):
        # Placeholder images
        pics = [
            "https://picsum.photos/seed/1/600/400",
            "https://picsum.photos/seed/2/600/400",
            "https://picsum.photos/seed/3/600/400",
            "https://picsum.photos/seed/4/600/400",
            "https://picsum.photos/seed/5/600/400",
        ]
        return random.choice(pics)

    # ---------- Reset ----------

    def _reset_demo_data(self):
        # Delete only demo-tagged data and derivatives that are safe to remove
        Notification.objects.filter(Q(title__contains=DEMO_TAG) | Q(body__contains=DEMO_TAG)).delete()
        FCMDevice.objects.filter(device_name__startswith=DEMO_TAG).delete()
        OrderItem.objects.filter(product_name_snapshot__contains=DEMO_TAG).delete()
        Order.objects.filter(Q(shipping_address_snapshot__has_key='demo_tag') | Q(payment_status='PENDING_PAYMENT')).delete()
        CartItem.objects.all().delete()
        ProductReview.objects.all().delete()
        StoreReview.objects.all().delete()
        OrderReview.objects.all().delete()
        UserStoreFavorite.objects.all().delete()
        UserProductFavorite.objects.all().delete()
        Promotion.objects.filter(name__contains=DEMO_TAG).delete()
        Offer.objects.filter(name__contains=DEMO_TAG).delete()
        Coupon.objects.filter(code__startswith="DEMO-").delete()
        ProductImage.objects.all().delete()
        ProductVariant.objects.filter(Q(sku__startswith="DEMO-") | Q(cover_image_url__startswith="http")) .delete()
        Product.objects.filter(Q(name__contains=DEMO_TAG) | Q(cover_image_url__startswith="http")).delete()
        ProductCategory.objects.filter(name__startswith=DEMO_TAG).delete()
        Store.objects.filter(name__contains=DEMO_TAG).delete()
        PlatformCategory.objects.filter(name__startswith=DEMO_TAG).delete()
        DeliveryProfile.objects.all().delete()
        UserAddress.objects.filter(label__startswith=DEMO_TAG).delete()
        User.objects.filter(email__startswith="demo_").delete()

    # ---------- Users ----------

    def _ensure_users(self, n_customers: int, n_vendors: int):
        created_customers = []
        created_vendors = []

        # Admin user for convenience (if not exists)
        admin_email = "admin@example.com"
        if not User.objects.filter(email=admin_email).exists():
            admin = User.objects.create_superuser(email=admin_email, password="AdminPass123!")
            admin.name = "Admin User"
            admin.is_verified = True
            admin.save()

        # Customers
        for i in range(n_customers):
            email = f"demo_customer_{i}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": f"{DEMO_TAG} Customer {i}",
                    "is_active": True,
                    "is_verified": True,
                    "is_vendor": False,
                    "is_delivery": False,
                },
            )
            if created:
                user.set_password("Customer123!")
                user.save()
            created_customers.append(user)

            # Address
            UserAddress.objects.get_or_create(
                user=user,
                label=f"{DEMO_TAG} Home",
                defaults={
                    "city": random.choice(["صنعاء", "عدن", "تعز", "إب", "الحديدة"]),
                    "street": f"Street {random.randint(1, 99)}",
                    "landmark": "Near Demo Park",
                    "is_default": True,
                },
            )

            # FCM device
            FCMDevice.objects.get_or_create(
                user=user,
                registration_token=f"token-{self._rand_word(12)}-{i}",
                defaults={
                    "device_type": random.choice(["android", "ios"]),
                    "device_name": f"{DEMO_TAG} Device {i}",
                    "is_active": True,
                },
            )

        # Vendors
        for i in range(n_vendors):
            email = f"demo_vendor_{i}@example.com"
            vendor, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": f"{DEMO_TAG} Vendor {i}",
                    "is_active": True,
                    "is_verified": True,
                    "is_vendor": True,
                },
            )
            if created:
                vendor.set_password("Vendor123!")
                vendor.save()
            created_vendors.append(vendor)

        return {"customers": created_customers, "vendors": created_vendors}

    # ---------- Stores & Categories ----------

    def _ensure_stores(self, n_stores: int, vendors):
        # Platform categories
        plat_names = [f"{DEMO_TAG} Electronics", f"{DEMO_TAG} Fashion", f"{DEMO_TAG} Home"]
        plat_cats = []
        for name in plat_names:
            pc, _ = PlatformCategory.objects.get_or_create(name=name, defaults={"image_url": self._rand_image(), "is_featured": True})
            plat_cats.append(pc)

        cities = ["صنعاء", "عدن", "تعز", "إب"]
        stores = []
        for i in range(n_stores):
            owner = vendors[i % len(vendors)] if vendors else None
            name = f"{DEMO_TAG} Store {i}"
            store, _ = Store.objects.get_or_create(
                name=name,
                owner=owner,
                defaults={
                    "description": "Demo store for testing",
                    "platform_category": random.choice(plat_cats),
                    "status": Store.StoreStatus.ACTIVE,
                    "logo_url": self._rand_image(),
                    "cover_image_url": self._rand_image(),
                    "phone_number": f"777{random.randint(100000, 999999)}",
                    "address": "Demo Address",
                    "city": random.choice(cities),
                    "opening_time": timezone.now().time().replace(hour=8, minute=0, second=0, microsecond=0),
                    "closing_time": timezone.now().time().replace(hour=22, minute=0, second=0, microsecond=0),
                },
            )
            stores.append(store)
        return stores

    def _ensure_categories(self, stores):
        categories = []
        for store in stores:
            # Root categories
            for name in [f"{DEMO_TAG} Phones", f"{DEMO_TAG} Laptops", f"{DEMO_TAG} Accessories"]:
                cat, _ = ProductCategory.objects.get_or_create(store=store, name=name, parent=None)
                categories.append(cat)
                # Subcategory
                sub, _ = ProductCategory.objects.get_or_create(store=store, name=f"{name} - Premium", parent=cat)
                categories.append(sub)
        return categories

    # ---------- Products ----------

    def _ensure_products(self, stores, categories, per_store=5, variants_per_product=3):
        all_products = []
        for store in stores:
            store_cats = [c for c in categories if c.store_id == store.id and c.parent_id is not None]
            for i in range(per_store):
                name = f"{DEMO_TAG} Product {store.id}-{i}"
                category = random.choice(store_cats) if store_cats else None
                product, _ = Product.objects.get_or_create(
                    store=store,
                    name=name,
                    defaults={
                        "category": category,
                        "description": "This is a demo product used for testing the system.",
                        "specifications": {"Brand": "DemoBrand", "Warranty": "1 year"},
                        "is_active": True,
                        "cover_image_url": self._rand_image(),
                        "average_rating": 0.0,
                        "review_count": 0,
                        "selling_count": 0,
                    },
                )
                # Images
                for order in range(3):
                    ProductImage.objects.get_or_create(
                        product=product,
                        image_url=self._rand_image(),
                        display_order=order,
                    )
                # Variants
                for v in range(max(1, variants_per_product + random.choice([-1, 0, 1]))):
                    sku = f"DEMO-{product.id}-{v}-{random.randint(1000,9999)}"
                    pv, _ = ProductVariant.objects.get_or_create(
                        product=product,
                        sku=sku,
                        defaults={
                            "price": self._rand_price(),
                            "options": {
                                "color": random.choice(["Black", "White", "Blue", "Red"]),
                                "storage": random.choice(["64GB", "128GB", "256GB"]),
                            },
                            "cover_image_url": self._rand_image(),
                        },
                    )
                all_products.append(product)
        return all_products

    # ---------- Wishlist ----------

    def _ensure_wishlist(self, users, stores, products):
        customers = users["customers"]
        for u in customers:
            for s in random.sample(stores, k=min(2, len(stores))):
                UserStoreFavorite.objects.get_or_create(user=u, store=s)
            for p in random.sample(products, k=min(4, len(products))):
                UserProductFavorite.objects.get_or_create(user=u, product=p)

    # ---------- Pricing ----------

    def _ensure_pricing(self, stores, products):
        # Coupon
        coupon, _ = Coupon.objects.get_or_create(code="DEMO-10OFF", defaults={"active": True})
        # Promotion: 10% on random store
        promo, _ = Promotion.objects.get_or_create(
            name=f"{DEMO_TAG} 10% Off",
            defaults={
                "promotion_type": Promotion.PromotionType.PRODUCT_PERCENTAGE,
                "value": 10,
                "active": True,
                "priority": 10,
                "stackable": True,
                "required_coupon": None,
            },
        )
        promo.stores.set(random.sample(stores, k=min(1, len(stores))))
        # Offer example
        offer, _ = Offer.objects.get_or_create(
            name=f"{DEMO_TAG} Buy 2 Get 1",
            defaults={
                "offer_type": Offer.OfferType.BUY_X_GET_Y,
                "active": True,
                "priority": 20,
                "configuration": {"buy_quantity": 2, "get_quantity": 1},
            },
        )
        if products:
            offer.products.set(random.sample(products, k=min(3, len(products))))
        return coupon, promo, offer

    # ---------- Delivery Profiles ----------

    def _ensure_delivery_profiles(self, users):
        # Create 2 delivery agents from customers for realism
        customers = users["customers"]
        selected = customers[:2] if len(customers) >= 2 else customers
        profiles = []
        for idx, u in enumerate(selected):
            u.is_delivery = True
            u.save(update_fields=["is_delivery"])
            dp, _ = DeliveryProfile.objects.get_or_create(
                user=u,
                defaults={
                    "id_card_image": "delivery/ids/demo.png",
                    "driver_license_image": "delivery/licenses/demo.png",
                    "vehicle_type": random.choice(["Car", "Bike", "Scooter"]),
                    "city": random.choice(["صنعاء", "عدن", "تعز", "إب"]),
                    "delivery_state": DeliveryProfile.DeliveryState.AVAILABLE,
                    "verification_status": DeliveryProfile.VerificationStatus.APPROVED,
                    "suspended": False,
                },
            )
            profiles.append(dp)
        return profiles

    # ---------- Orders ----------

    def _ensure_orders(self, n_orders, users, stores, products):
        customers = users["customers"]
        orders = []
        if not customers or not products:
            return orders

        for i in range(n_orders):
            user = random.choice(customers)
            store = random.choice(stores)

            # Choose 1-3 variants from products belonging to this store
            store_products = [p for p in products if p.store_id == store.id]
            if not store_products:
                continue
            selected_products = random.sample(store_products, k=min(random.randint(1, 3), len(store_products)))

            items_snapshot = []
            grand_total = 0
            order = Order.objects.create(
                store=store,
                user=user,
                delivery_agent=None,
                grand_total=0,
                delivery_fee=round(random.uniform(1.0, 5.0), 2),
                shipping_address_snapshot={
                    "demo_tag": True,
                    "city": random.choice(["صنعاء", "عدن", "تعز", "إب"]),
                    "street": f"Street {random.randint(1, 99)}",
                    "label": "Home",
                },
                payment_status=Order.PaymentStatus.PENDING_PAYMENT,
                fulfillment_status=Order.FulfillmentStatus.PENDING,
            )

            for p in selected_products:
                variants = list(p.variants.all())
                if not variants:
                    continue
                variant = random.choice(variants)
                qty = random.randint(1, 3)
                line_total = float(variant.price) * qty
                grand_total += line_total

                OrderItem.objects.create(
                    order=order,
                    variant=variant,
                    quantity=qty,
                    price_at_purchase=variant.price,
                    product_name_snapshot=f"{DEMO_TAG} {p.name}",
                    variant_options_snapshot=variant.options,
                    status=OrderItem.Status.ACTIVE,
                )

            order.grand_total = round(grand_total + float(order.delivery_fee), 2)
            order.payment_status = Order.PaymentStatus.PAID if random.random() > 0.3 else Order.PaymentStatus.PENDING_PAYMENT
            order.fulfillment_status = random.choice([
                Order.FulfillmentStatus.ACCEPTED,
                Order.FulfillmentStatus.PREPARING,
                Order.FulfillmentStatus.SHIPPED,
                Order.FulfillmentStatus.DELIVERED,
                Order.FulfillmentStatus.PENDING,
            ])
            order.save()
            orders.append(order)

        return orders

    # ---------- Reviews ----------

    def _ensure_reviews(self, users, stores, products, orders):
        customers = users["customers"]
        for u in customers:
            # Product reviews
            for p in random.sample(products, k=min(3, len(products))):
                rating = random.randint(3, 5)
                ProductReview.objects.get_or_create(
                    user=u,
                    product=p,
                    defaults={
                        "rating": rating,
                        "comment": "Great demo product!",
                    },
                )
            # Store reviews
            for s in random.sample(stores, k=min(2, len(stores))):
                rating = random.randint(3, 5)
                StoreReview.objects.get_or_create(
                    user=u,
                    store=s,
                    defaults={
                        "rating": rating,
                        "comment": "Nice demo store!",
                    },
                )

        # Order reviews
        for o in random.sample(orders, k=min(len(orders)//2, len(orders))):
            if o.user_id:
                OrderReview.objects.get_or_create(
                    user=o.user,
                    order=o,
                    defaults={
                        "delivery_speed_rating": random.randint(3, 5),
                        "service_quality_rating": random.randint(3, 5),
                    },
                )

    # ---------- Notifications ----------

    def _ensure_notifications(self, users):
        all_users = users["customers"] + users["vendors"]
        for u in all_users:
            Notification.objects.get_or_create(
                user=u,
                title=f"{DEMO_TAG} Welcome",
                defaults={
                    "body": f"{DEMO_TAG} Hello {u.get_short_name()}, your demo account is ready.",
                    "type": "system",
                    "priority": "normal",
                    "data": {"demo": True},
                    "image_url": None,
                    "is_read": False,
                },
            )
