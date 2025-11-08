# utils.py New File
from datetime import datetime
from django.utils import timezone
from stores.models import Store
from rest_framework.response import Response
from rest_framework import status

def parse_aware_datetime(date_string: str | None) -> datetime | None:
    """
    تحويل سلسلة نصية بصيغة ISO 8601 إلى كائن datetime واعٍ بالمنطقة الزمنية.
    
    Args:
        date_string: السلسلة النصية للتاريخ المراد تحويلها.
    
    Returns:
        كائن datetime واعٍ بالمنطقة الزمنية إذا نجح التحويل، وإلا None.
    """
    if not date_string:
        return None

    try:
        # استبدال 'Z' (Zulu time) بـ '+00:00' ليكون متوافقاً مع fromisoformat
        dt_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        
        # إذا كان التاريخ "ساذجاً" (naive)، اجعله واعياً بالمنطقة الزمنية الافتراضية للمشروع
        if timezone.is_naive(dt_obj):
            return timezone.make_aware(dt_obj)
        
        # إذا كان بالفعل واعياً، أرجعه كما هو
        return dt_obj
        
    except (ValueError, TypeError):
        # في حالة كان تنسيق التاريخ غير صالح
        return None
    
def get_and_validate_store(request, store_id) -> Store | None:
    """
    التحقق من أن store_id موجود وأن المستخدم الحالي هو المالك.

    Args:
        request: كائن الطلب الحالي.
        store_id: معرّف المتجر المراد التحقق منه.

    Returns:
        كائن المتجر (Store object) إذا كان صالحاً، وإلا يثير استثناء.
        
    Raises:
        ValidationError: إذا كان store_id مفقوداً
        PermissionDenied: إذا كان المتجر غير موجود أو المستخدم لا يملكه
    """
    # استيراد الاستثناءات من DRF
    from rest_framework.exceptions import ValidationError, PermissionDenied
    
    if not store_id:
        raise ValidationError({'error': 'معرّف المتجر (store_id) مطلوب.'})

    try:
        # استخدام .get() للبحث عن المتجر والتأكد من الملكية في خطوة واحدة
        store = Store.objects.get(id=store_id, owner=request.user)
        return store
    except Store.DoesNotExist:
        # إذا لم يتم العثور عليه أو كان المالك مختلفاً، أثر استثناء الصلاحية
        raise PermissionDenied({'error': 'المتجر المحدد غير صالح أو لا تملكه.'})