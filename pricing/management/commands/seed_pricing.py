from django.core.management.base import BaseCommand
from django.utils import timezone
from pricing.models import Coupon, Promotion, Offer


class Command(BaseCommand):
    help = "Seed pricing demo data: coupons, promotions, offers"

    def handle(self, *args, **options):
        created = {"coupons": 0, "promotions": 0, "offers": 0}

        # Coupons
        coupons = [
            {"code": "WELCOME10", "active": True},
            {"code": "FREESHIP", "active": True},
            {"code": "VIP20", "active": True},
        ]
        for data in coupons:
            obj, was_created = Coupon.objects.get_or_create(code=data["code"], defaults=data)
            if was_created:
                created["coupons"] += 1

        # Promotions (percentage and fixed)
        promos = [
            {
                "name": "خصم 10% على السلة",
                "promotion_type": "CART_PERCENTAGE",
                "value": 10,
                "active": True,
                "priority": 50,
            },
            {
                "name": "خصم 20 ريال على المنتجات",
                "promotion_type": "PRODUCT_FIXED_AMOUNT",
                "value": 20,
                "active": True,
                "priority": 60,
            },
        ]
        for data in promos:
            obj, was_created = Promotion.objects.get_or_create(name=data["name"], defaults=data)
            if was_created:
                created["promotions"] += 1

        # Offers (bundle and threshold gift/free shipping)
        offers = [
            {
                "name": "باقة 3 منتجات بـ 99",
                "offer_type": "BUNDLE_FIXED_PRICE",
                "configuration": {"bundle_price": 99.0, "product_ids": []},
                "active": True,
                "priority": 70,
            },
            {
                "name": "هدية عند 200",
                "offer_type": "THRESHOLD_GIFT",
                "configuration": {"threshold_amount": 200, "gift_product_id": None},
                "active": True,
                "priority": 80,
            },
            {
                "name": "شحن مجاني عند 150",
                "offer_type": "THRESHOLD_FREE_SHIPPING",
                "configuration": {"threshold_amount": 150},
                "active": True,
                "priority": 90,
            },
        ]
        for data in offers:
            obj, was_created = Offer.objects.get_or_create(name=data["name"], defaults=data)
            if was_created:
                created["offers"] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Seed completed. Coupons: +{created['coupons']}, Promotions: +{created['promotions']}, Offers: +{created['offers']}"
        ))
