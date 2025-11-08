from __future__ import annotations

from decimal import Decimal
from typing import Iterable, List, Tuple, Dict, Any

from orders.services.pricing_engine import price_cart, money


def build_cart_items_from_variants(variant_qty_list: Iterable[Tuple[Any, int]]) -> List[Dict[str, Any]]:
    """
    Build pricing_engine-compatible cart items from iterable of (variant, qty).
    - variant: ProductVariant instance (no import here to keep function generic)
    - qty: integer quantity
    Returns list of dicts with keys expected by pricing_engine.price_cart
    """
    items: List[Dict[str, Any]] = []
    for variant, qty in variant_qty_list:
        product = variant.product
        category_id = getattr(product, 'category_id', None)
        items.append({
            'product_id': product.id,
            'variant_id': variant.id,
            'store_id': product.store_id,
            'category_ids': [category_id] if category_id else [],
            'name': product.name,
            'qty': qty,
            'unit_price': variant.price,
        })
    return items


def compute_order_totals(
    user_id: int | None,
    cart_items: List[Dict[str, Any]],
    delivery_fee: Decimal = Decimal('0'),
    currency: str = 'SAR',
    coupon_code: str | None = None,
) -> tuple[Decimal, Decimal, Dict[str, Any]]:
    """
    Compute subtotal and grand_total using pricing_engine.price_cart(cart).
    Grand total is currently subtotal + delivery_fee (shipping not yet handled by engine).
    Returns (subtotal, grand_total)
    """
    cart = {
        'user_id': user_id,
        'items': cart_items,
        'coupon_code': coupon_code,
        'currency': currency,
    }
    pricing = price_cart(cart)
    subtotal = pricing.get('subtotal', Decimal('0'))
    grand_total = money(subtotal + (delivery_fee or Decimal('0')) - pricing.get('discounts_total', Decimal('0')))
    return subtotal, grand_total, pricing
