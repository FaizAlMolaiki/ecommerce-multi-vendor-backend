# """
# Pricing Engine - orders/services/pricing_engine.py

# Minimal, safe scaffold for the pricing engine with no side effects.
# - No Django model imports at module import time
# - Pure functions, standard library only
# - Ready for gradual expansion

# This module currently provides:
# - Public DTOs (TypedDicts) for Cart, CartItem, etc.
# - Utility helpers for decimal money math
# - A conservative price_cart(cart) implementation that computes subtotal only
#   and leaves discounts/offers as zero. This ensures callers can integrate the
#   function without breaking flows, while we iterate on rules application.
# """

# from __future__ import annotations

# from typing import List, Dict, Any, Optional, TypedDict, Literal
# from decimal import Decimal, ROUND_HALF_UP
# import logging

# logger = logging.getLogger(__name__)


# # ========= Public DTOs =========
# class CartItem(TypedDict):
#     product_id: int
#     variant_id: Optional[int]
#     store_id: Optional[int]
#     category_ids: List[int]
#     name: str
#     qty: int
#     unit_price: Decimal  # price before discount


# class Cart(TypedDict):
#     user_id: Optional[int]
#     items: List[CartItem]
#     coupon_code: Optional[str]
#     currency: str


# class AppliedRule(TypedDict):
#     rule_type: Literal["promotion", "offer"]
#     rule_id: int
#     name: str
#     amount: Decimal  # positive discount amount
#     meta: Dict[str, Any]


# class PricingResult(TypedDict):
#     subtotal: Decimal
#     discounts_total: Decimal
#     shipping: Decimal
#     grand_total: Decimal
#     applied_rules: List[AppliedRule]
#     line_discounts: Dict[int, Decimal]  # product_id -> discount amount
#     free_shipping: bool
#     gifts: List[int]  # product_ids gifted
#     notes: List[str]


# # ========= Utilities =========
# def to_decimal(value: Any) -> Decimal:
#     if isinstance(value, Decimal):
#         return value
#     try:
#         return Decimal(str(value))
#     except Exception:
#         return Decimal("0")


# def money(value: Decimal, places: int = 2) -> Decimal:
#     q = Decimal(10) ** -places
#     return value.quantize(q, rounding=ROUND_HALF_UP)


# # ========= Engine (no-op discounts for now) =========
# def price_cart(cart: Cart) -> PricingResult:
#     """Compute cart pricing with minimal cart-level promotions support.

#     Currently supported:
#     - CART_PERCENTAGE and CART_FIXED_AMOUNT promotions
#       - active and within time window
#       - optional required_coupon must match cart['coupon_code'] and be valid
#       - optional min_purchase_amount satisfied by subtotal
#       - Scope (stores/categories/products/variants) is ignored for now
#     - No stacking yet: first applicable promotion by priority is applied

#     Product-level discounts, offers, gifts, and free shipping will be added later.
#     """
#     # Subtotal
#     subtotal = Decimal("0")
#     for item in cart.get("items", []):
#         qty = to_decimal(item.get("qty", 0))
#         unit = to_decimal(item.get("unit_price", 0))
#         line = qty * unit
#         subtotal += line

#     subtotal = money(subtotal)

#     discounts_total = Decimal("0")
#     applied_rules: List[AppliedRule] = []

#     # Try to apply a single cart-level promotion
#     try:
#         # Import Django bits lazily to avoid side effects at module import time
#         from django.utils import timezone  # type: ignore
#         from pricing.models import Promotion  # type: ignore

#         coupon_code = (cart.get("coupon_code") or "").strip().upper()

#         # Only cart-level promotion types
#         CART_TYPES = {
#             "CART_PERCENTAGE",
#             "CART_FIXED_AMOUNT",
#         }

#         # Query promotions ordered by priority then id
#         promos = (
#             Promotion.objects.filter(active=True, promotion_type__in=CART_TYPES)
#             .select_related("required_coupon")
#             .order_by("priority", "id")
#         )

#         now = timezone.now()

#         for rule in promos:
#             # Time window
#             if hasattr(rule, "is_within_time_window") and not rule.is_within_time_window(now):
#                 continue

#             # Coupon requirement
#             if rule.required_coupon:
#                 rc = rule.required_coupon
#                 # Coupon must be active and within its own time window if set
#                 if not rc.active:
#                     continue
#                 if rc.start_at and now < rc.start_at:
#                     continue
#                 if rc.end_at and now > rc.end_at:
#                     continue
#                 # Must match provided coupon_code
#                 if not coupon_code or coupon_code != (rc.code or "").upper():
#                     continue

#             # Minimum purchase
#             if rule.min_purchase_amount and subtotal < rule.min_purchase_amount:
#                 continue

#             # Compute discount amount
#             disc = Decimal("0")
#             if rule.promotion_type == "CART_PERCENTAGE":
#                 # Clamp sensible percentage [0, 100]
#                 pct = to_decimal(rule.value)
#                 if pct <= 0:
#                     continue
#                 if pct > Decimal("100"):
#                     pct = Decimal("100")
#                 disc = (subtotal * pct) / Decimal("100")
#             elif rule.promotion_type == "CART_FIXED_AMOUNT":
#                 amt = to_decimal(rule.value)
#                 if amt <= 0:
#                     continue
#                 disc = amt if amt < subtotal else subtotal

#             disc = money(disc)
#             if disc <= 0:
#                 continue

#             discounts_total = disc
#             applied_rules.append(
#                 {
#                     "rule_type": "promotion",
#                     "rule_id": rule.id,
#                     "name": rule.name,
#                     "amount": disc,
#                     "meta": {
#                         "promotion_type": rule.promotion_type,
#                         "priority": rule.priority,
#                         "stackable": rule.stackable,
#                         "required_coupon": rule.required_coupon.code if rule.required_coupon else None,
#                     },
#                 }
#             )
#             # No stacking for now; stop at first applicable
#             break
#     except Exception as ex:  # pragma: no cover - safety net
#         logger.warning("pricing_engine: promotion application skipped due to error: %s", ex)

#     discounts_total = money(discounts_total)
#     shipping = money(Decimal("0"))
#     grand_total = money(subtotal - discounts_total + shipping)

#     result: PricingResult = {
#         "subtotal": subtotal,
#         "discounts_total": discounts_total,
#         "shipping": shipping,
#         "grand_total": grand_total,
#         "applied_rules": applied_rules,
#         "line_discounts": {},
#         "free_shipping": False,
#         "gifts": [],
#         "notes": [
#             "pricing_engine: subtotal + minimal cart promotions",
#             "no stacking; first applicable cart-level promotion only",
#         ],
#     }
#     return result


"""
Pricing Engine - orders/services/pricing_engine.py

Minimal, safe scaffold for the pricing engine with no side effects.
- No Django model imports at module import time
- Pure functions, standard library only
- Ready for gradual expansion

This module currently provides:
- Public DTOs (TypedDicts) for Cart, CartItem, etc.
- Utility helpers for decimal money math
- A conservative price_cart(cart) implementation that computes subtotal only
  and leaves discounts/offers as zero. This ensures callers can integrate the
  function without breaking flows, while we iterate on rules application.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, TypedDict, Literal
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)


# ========= Public DTOs =========
class CartItem(TypedDict):
    product_id: int
    variant_id: Optional[int]
    store_id: Optional[int]
    category_ids: List[int]
    name: str
    qty: int
    unit_price: Decimal  # price before discount


class Cart(TypedDict):
    user_id: Optional[int]
    items: List[CartItem]
    coupon_code: Optional[str]
    currency: str


class AppliedRule(TypedDict):
    rule_type: Literal["promotion", "offer"]
    rule_id: int
    name: str
    amount: Decimal  # positive discount amount
    meta: Dict[str, Any]


class PricingResult(TypedDict):
    subtotal: Decimal
    discounts_total: Decimal
    shipping: Decimal
    grand_total: Decimal
    applied_rules: List[AppliedRule]
    line_discounts: Dict[int, Decimal]  # product_id -> discount amount
    free_shipping: bool
    gifts: List[int]  # product_ids gifted
    notes: List[str]


# ========= Utilities =========
def to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def money(value: Decimal, places: int = 2) -> Decimal:
    q = Decimal(10) ** -places
    return value.quantize(q, rounding=ROUND_HALF_UP)


# NEW: Full pricing engine with discounts, offers, and coupons
def price_cart(cart: Cart) -> PricingResult:
    """حساب سعر السلة الكامل مع الخصومات والعروض
    
    Args:
        cart: Cart dict containing items, user_id, coupon_code, etc.
    
    Returns:
        PricingResult with subtotal, discounts, shipping, grand_total, etc.
    """
    # 1. حساب الإجمالي الفرعي
    subtotal = _calculate_subtotal(cart.get("items", []))
    
    # 2. تحميل القواعد المطبقة
    rules = _load_applicable_rules(cart, subtotal)
    
    # 3. تطبيق الخصومات والعروض
    discount_result = _apply_discounts(cart, rules, subtotal)
    
    # 4. حساب الشحن
    shipping = _calculate_shipping(cart, discount_result)
    
    # 5. الإجمالي النهائي
    grand_total = money(subtotal - discount_result["total"] + shipping)
    
    result: PricingResult = {
        "subtotal": subtotal,
        "discounts_total": discount_result["total"],
        "shipping": shipping,
        "grand_total": grand_total,
        "applied_rules": discount_result["rules"],
        "line_discounts": discount_result["line_discounts"],
        "free_shipping": discount_result["free_shipping"],
        "gifts": discount_result["gifts"],
        "notes": [],
    }
    return result


# NEW: Helper functions for pricing engine
def _calculate_subtotal(items: List[CartItem]) -> Decimal:
    """حساب الإجمالي الفرعي للسلة"""
    subtotal = Decimal("0")
    for item in items:
        qty = to_decimal(item.get("qty", 0))
        unit = to_decimal(item.get("unit_price", 0))
        subtotal += qty * unit
    return money(subtotal)


# NEW: Load applicable rules from database
def _load_applicable_rules(cart: Cart, subtotal: Decimal) -> List[Dict[str, Any]]:
    """تحميل القواعد القابلة للتطبيق من قاعدة البيانات
    
    Returns:
        List of rule dicts sorted by priority
    """
    try:
        from django.utils import timezone
        from pricing.models import Promotion, Offer, Coupon
        from django.db import models
        from django.db import transaction
    except ImportError:
        logger.warning("Cannot import Django models, returning empty rules")
        return []
    
    now = timezone.now()
    rules = []
    
    # 1. القواعد التلقائية (بدون كوبون)
    try:
        auto_promotions = Promotion.objects.filter(
            active=True,
            required_coupon__isnull=True
        ).filter(
            models.Q(start_at__isnull=True) | models.Q(start_at__lte=now)
        ).filter(
            models.Q(end_at__isnull=True) | models.Q(end_at__gte=now)
        ).prefetch_related('stores', 'categories', 'products', 'variants')
        
        for promo in auto_promotions:
            if promo.min_purchase_amount and subtotal < promo.min_purchase_amount:
                continue
                
            rules.append({
                'type': 'promotion',
                'obj': promo,
                'priority': promo.priority,
                'stackable': promo.stackable
            })
    except Exception as e:
        logger.error(f"Error loading auto promotions: {e}")
    
    # 2. إذا كان هناك كوبون
    coupon_code = cart.get("coupon_code")
    if coupon_code:
        try:
            # ✅ FIXED: استخدام transaction مع قفل السجل لمنع حالة السباق
            with transaction.atomic():
                coupon = Coupon.objects.select_for_update().get(
                    code=coupon_code,
                    active=True
                )
            
                # الآن، أي عملية أخرى تحاول الوصول لنفس الكوبون ستنتظر حتى انتهاء هذا البلوك
                # مما يجعل التحققات التالية آمنة 100%
            
                # التحقق من الصلاحية
                if coupon.start_at and now < coupon.start_at:
                    logger.warning(f"Coupon {coupon.code} not started yet")
                    return rules # لا يوجد تغيير هنا، يمكنك الخروج بأمان
                if coupon.end_at and now > coupon.end_at:
                    logger.warning(f"Coupon {coupon.code} expired")
                    return rules
                
                # التحقق من حدود الاستخدام (هذا العد الآن آمن)
                if coupon.usage_limit:
                    total_usage = coupon.redemptions.count()
                    if total_usage >= coupon.usage_limit:
                        logger.warning(f"Coupon {coupon.code} usage limit reached")
                        # لا تقم بإرجاع rules هنا مباشرة، بل اخرج من try/except
                        # للسماح للقواعد الأخرى بالتطبيق إذا أردت ذلك.
                        # ولكن في حالة الكوبون، من الأفضل الخروج تماماً.
                        raise Coupon.DoesNotExist("Usage limit reached")

                user_id = cart.get("user_id")
                if user_id and coupon.limit_per_user:
                    user_usage = coupon.redemptions.filter(user_id=user_id).count()
                    if user_usage >= coupon.limit_per_user:
                        logger.warning(f"User limit reached for coupon {coupon.code}")
                        raise Coupon.DoesNotExist("User usage limit reached")
                
                # إضافة قواعد الكوبون
                coupon_promotions = Promotion.objects.filter(
                    required_coupon=coupon,
                    active=True
                ).prefetch_related('stores', 'categories', 'products', 'variants')
                
                for promo in coupon_promotions:
                    if promo.min_purchase_amount and subtotal < promo.min_purchase_amount:
                        continue
                    rules.append({'type': 'promotion', 'obj': promo, 'priority': promo.priority, 'stackable': promo.stackable, 'coupon': coupon})
                
                # العروض المرتبطة بالكوبون
                coupon_offers = Offer.objects.filter(
                    required_coupon=coupon,
                    active=True
                ).prefetch_related('stores', 'categories', 'products', 'variants')
                
                for offer in coupon_offers:
                    if offer.min_purchase_amount and subtotal < offer.min_purchase_amount:
                        continue
                    rules.append({'type': 'offer', 'obj': offer, 'priority': offer.priority, 'stackable': offer.stackable, 'coupon': coupon})

        except Coupon.DoesNotExist as e:
            logger.warning(f"Invalid coupon code or limit reached: {coupon_code} ({e})")
        except Exception as e:
            logger.error(f"Error loading coupon rules: {e}", exc_info=True)
    
    # ترتيب القواعد حسب الأولوية
    return sorted(rules, key=lambda r: r['priority'])

# NEW: Apply all discounts and offers
def _apply_discounts(
    cart: Cart,
    rules: List[Dict[str, Any]],
    subtotal: Decimal
) -> Dict[str, Any]:
    """تطبيق الخصومات والعروض على السلة
    
    Returns:
        Dict with total, rules, line_discounts, free_shipping, gifts
    """
    total_discount = Decimal("0")
    applied = []
    line_discounts = {}
    free_shipping = False
    gifts = []
    
    for rule_data in rules:
        rule_obj = rule_data['obj']
        rule_type = rule_data['type']
        
        discount = Decimal("0")
        
        if rule_type == 'promotion':
            discount = _apply_promotion(
                rule_obj,
                cart,
                subtotal,
                line_discounts
            )
        elif rule_type == 'offer':
            result = _apply_offer(rule_obj, cart, subtotal)
            discount = result.get('discount', Decimal("0"))
            if result.get('free_shipping'):
                free_shipping = True
            if result.get('gifts'):
                gifts.extend(result['gifts'])
        
        if discount > 0:
            total_discount += discount
            applied.append({
                'rule_type': rule_type,
                'rule_id': rule_obj.id,
                'name': rule_obj.name,
                'amount': discount,
                'meta': {}
            })
            
            # إيقاف التكديس إذا كانت القاعدة غير قابلة للتكديس
            if not rule_data['stackable']:
                break
    
    return {
        'total': money(total_discount),
        'rules': applied,
        'line_discounts': line_discounts,
        'free_shipping': free_shipping,
        'gifts': gifts
    }


# NEW: Apply a single promotion
def _apply_promotion(
    promo,
    cart: Cart,
    subtotal: Decimal,
    line_discounts: Dict[int, Decimal]
) -> Decimal:
    """تطبيق خصم Promotion"""
    try:
        from pricing.models import Promotion
    except ImportError:
        return Decimal("0")
    
    discount = Decimal("0")
    
    # خصم على إجمالي السلة
    if promo.promotion_type == Promotion.PromotionType.CART_PERCENTAGE:
        discount = (subtotal * promo.value) / Decimal("100")
    
    elif promo.promotion_type == Promotion.PromotionType.CART_FIXED_AMOUNT:
        discount = min(promo.value, subtotal)
    
    # خصم على المنتجات المحددة
    elif promo.promotion_type == Promotion.PromotionType.PRODUCT_PERCENTAGE:
        for item in cart.get("items", []):
            if _item_matches_promotion(item, promo):
                item_qty = to_decimal(item.get("qty", 0))
                item_price = to_decimal(item.get("unit_price", 0))
                item_subtotal = item_qty * item_price
                item_discount = (item_subtotal * promo.value) / Decimal("100")
                discount += item_discount
                
                product_id = item.get("product_id")
                if product_id:
                    line_discounts[product_id] = \
                        line_discounts.get(product_id, Decimal("0")) + item_discount
    
    elif promo.promotion_type == Promotion.PromotionType.PRODUCT_FIXED_AMOUNT:
        for item in cart.get("items", []):
            if _item_matches_promotion(item, promo):
                item_qty = to_decimal(item.get("qty", 0))
                item_price = to_decimal(item.get("unit_price", 0))
                item_subtotal = item_qty * item_price
                item_discount = min(promo.value * item_qty, item_subtotal)
                discount += item_discount
                
                product_id = item.get("product_id")
                if product_id:
                    line_discounts[product_id] = \
                        line_discounts.get(product_id, Decimal("0")) + item_discount
    
    return money(discount)


# NEW: Check if item matches promotion criteria
def _item_matches_promotion(item: CartItem, promo) -> bool:
    """التحقق من أن المنتج يطابق شروط الخصم"""
    try:
        # إذا كان الخصم لكل المنصة (لا توجد قيود)
        has_stores = promo.stores.exists()
        has_categories = promo.categories.exists()
        has_products = promo.products.exists()
        has_variants = promo.variants.exists()
        
        if not (has_stores or has_categories or has_products or has_variants):
            return True
        
        # التحقق من المتجر
        if has_stores:
            store_id = item.get("store_id")
            if store_id and promo.stores.filter(id=store_id).exists():
                return True
        
        # التحقق من الفئة
        if has_categories:
            item_categories = set(item.get("category_ids", []))
            promo_categories = set(promo.categories.values_list('id', flat=True))
            if item_categories & promo_categories:
                return True
        
        # التحقق من المنتج
        if has_products:
            product_id = item.get("product_id")
            if product_id and promo.products.filter(id=product_id).exists():
                return True
        
        # التحقق من المتغير
        if has_variants:
            variant_id = item.get("variant_id")
            if variant_id and promo.variants.filter(id=variant_id).exists():
                return True
        
        return False
    except Exception as e:
        logger.error(f"Error matching item to promotion: {e}")
        return False


# NEW: Full pricing engine with discounts, offers, and coupons
def _apply_offer(offer, cart: Cart, subtotal: Decimal) -> Dict[str, Any]:
    """تطبيق عرض Offer"""
    try:
        from pricing.models import Offer
    except ImportError:
        return {'discount': Decimal("0"), 'free_shipping': False, 'gifts': []}
    
    result = {
        'discount': Decimal("0"),
        'free_shipping': False,
        'gifts': []
    }
    
    config = offer.configuration or {}
    
    # شحن مجاني عند مبلغ معين
    if offer.offer_type == Offer.OfferType.THRESHOLD_FREE_SHIPPING:
        threshold = to_decimal(config.get('threshold', 0))
        if subtotal >= threshold:
            result['free_shipping'] = True
            logger.info(f"Free shipping applied for order >= {threshold}")
    
    # هدية عند مبلغ معين
    elif offer.offer_type == Offer.OfferType.THRESHOLD_GIFT:
        threshold = to_decimal(config.get('threshold', 0))
        if subtotal >= threshold:
            gift_product_ids = config.get('gift_product_ids', [])
            result['gifts'] = gift_product_ids
            logger.info(f"Gift applied for order >= {threshold}")
    
    # ✅ FIXED: اشتر X واحصل على Y (بالمنطق الصحيح)
    elif offer.offer_type == Offer.OfferType.BUY_X_GET_Y:
        buy_qty = config.get('buy_quantity', 0)
        get_qty = config.get('get_quantity', 0)
        target_product_id = config.get('target_product_id')
        discount_type = config.get('discount_type', 'free')
        discount_value = to_decimal(config.get('discount_value', 100))
        
        if buy_qty <= 0 or get_qty <= 0:
            logger.warning(f"Invalid BUY_X_GET_Y config: buy={buy_qty}, get={get_qty}")
            return result
        
        matching_items = []
        for item in cart.get("items", []):
            if not target_product_id or item.get("product_id") == target_product_id:
                matching_items.append(item)
        
        total_discount = Decimal("0")
        for item in matching_items:
            item_qty = item.get("qty", 0)
            item_price = to_decimal(item.get("unit_price", 0))

            # 1. كم مرة تم تحقيق شرط الشراء؟
            # مثال: إذا اشترى 5 والعرض "اشتر 2"، فقد حقق الشرط مرتين.
            num_buy_conditions_met = item_qty // buy_qty

            if num_buy_conditions_met > 0:
                # 2. كم عدد القطع التي يجب أن يحصل عليها مجاناً؟
                # مثال: حقق الشرط مرتين والعرض "احصل على 1"، إذن سيحصل على 2 مجاناً (1*2).
                eligible_free_items = num_buy_conditions_met * get_qty
                
                # 3. حساب الخصم بناءً على عدد القطع المجانية المؤهلة.
                if discount_type == 'free':
                    # مجاني تماماً
                    item_discount = eligible_free_items * item_price
                else:
                    # خصم بنسبة مئوية
                    item_discount = (eligible_free_items * item_price * discount_value) / Decimal("100")
                
                total_discount += item_discount
                logger.info(f"BUY_X_GET_Y applied: {num_buy_conditions_met} times, granting {eligible_free_items} free items with discount: {item_discount}")
        
        if total_discount > 0:
            result['discount'] = money(total_discount)
    
    # NEW: باقة بسعر ثابت (مكتمل)
    elif offer.offer_type == Offer.OfferType.BUNDLE_FIXED_PRICE:
        bundle_price = to_decimal(config.get('bundle_price', 0))
        required_product_ids = config.get('required_product_ids', [])
        required_variant_ids = config.get('required_variant_ids', [])
        min_qty_each = config.get('min_quantity_each', 1)
        
        if not required_product_ids or bundle_price <= 0:
            logger.warning(f"Invalid BUNDLE_FIXED_PRICE config")
            return result
        
        cart_items = cart.get("items", [])
        found_products = {}
        
        for item in cart_items:
            item_product_id = item.get("product_id")
            item_variant_id = item.get("variant_id")
            item_qty = item.get("qty", 0)
            
            if item_product_id in required_product_ids:
                if not required_variant_ids or item_variant_id in required_variant_ids:
                    found_products[item_product_id] = {
                        'qty': item_qty,
                        'price': to_decimal(item.get("unit_price", 0))
                    }
        
        all_products_present = len(found_products) == len(required_product_ids)
        min_qty_met = all(item['qty'] >= min_qty_each for item in found_products.values())
        
        if all_products_present and min_qty_met:
            original_bundle_price = sum(item['price'] * min_qty_each for item in found_products.values())
            
            if bundle_price < original_bundle_price:
                bundle_discount = original_bundle_price - bundle_price
                result['discount'] = money(bundle_discount)
                logger.info(f"BUNDLE_FIXED_PRICE applied: discount {bundle_discount}")
            else:
                logger.warning(f"Bundle price {bundle_price} >= original {original_bundle_price}")
        else:
            logger.info(f"Bundle incomplete: found {len(found_products)}/{len(required_product_ids)}")
    
    return result

# NEW: Calculate shipping cost (مكتمل)
def _calculate_shipping(cart: Cart, discount_result: Dict[str, Any]) -> Decimal:
    """
    حساب تكلفة الشحن
    
    يمكن التوسع لاحقاً بإضافة:
    - حساب حسب المدينة/المنطقة
    - حساب حسب الوزن
    - حساب حسب المسافة
    - تكامل مع API شركات الشحن
    """
    # إذا كان الشحن مجاني من عرض
    if discount_result.get('free_shipping'):
        return Decimal("0")
    
    # NEW: منطق حساب الشحن البسيط
    items = cart.get("items", [])
    subtotal = Decimal("0")
    total_items = 0
    
    for item in items:
        qty = to_decimal(item.get("qty", 0))
        unit_price = to_decimal(item.get("unit_price", 0))
        subtotal += qty * unit_price
        total_items += qty
    
    # منطق الشحن:
    # 1. شحن مجاني لطلبات أكثر من 200 ريال
    if subtotal >= Decimal("200.00"):  # ✅ تصحيح: 200 ريال (وليس 2000)
        return Decimal("0")
    
    # 2. رسوم ثابتة حسب عدد المنتجات
    if total_items <= 3:
        shipping_cost = Decimal("15.00")  # شحن قياسي
    elif total_items <= 10:
        shipping_cost = Decimal("25.00")  # شحن متوسط
    else:
        shipping_cost = Decimal("35.00")  # شحن كبير
    
    # 3. يمكن إضافة رسوم إضافية حسب المنطقة
    # delivery_city = cart.get('delivery_city')
    # if delivery_city in ['remote_city_1', 'remote_city_2']:
    #     shipping_cost += Decimal("10.00")
    
    logger.info(f"Shipping cost calculated: {shipping_cost} for {total_items} items, subtotal {subtotal}")
    return money(shipping_cost)


