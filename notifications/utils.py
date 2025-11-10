"""
Notification Utilities
معالجات ودوال مساعدة للإشعارات
"""


def serialize_content_object(obj):
    """
    تحويل content_object من Django model instance إلى dictionary
    لجعله قابلاً للـ JSON serialization
    يدعم جميع الـ Models بشكل تلقائي
    
    Args:
        obj: Notification instance with content_object
        
    Returns:
        dict: Serialized content_object أو None
    """
    if obj.content_object is None:
        return None
    
    try:
        content_type = obj.content_type
        if not content_type:
            return None
        
        model_name = content_type.model
        instance = obj.content_object
        
        # ✅ حالات خاصة للـ Models الأساسية - بناءً على الحقول الفعلية
        if model_name == 'order':
            return {
                'id': instance.id,
                'fulfillment_status': instance.fulfillment_status,
                'payment_status': instance.payment_status,
                'grand_total': float(instance.grand_total) if instance.grand_total else 0,
                'delivery_fee': float(instance.delivery_fee) if instance.delivery_fee else 0,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'store_name': instance.store.name if instance.store else None,
            }
        
        elif model_name == 'product':
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description if instance.description else None,
                'cover_image_url': instance.cover_image_url if instance.cover_image_url else None,
                'is_active': instance.is_active,
                'average_rating': float(instance.average_rating) if instance.average_rating else 0,
                'review_count': instance.review_count,
            }
        
        elif model_name == 'store':
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description if instance.description else None,
                'status': instance.status,
                'logo_url': instance.logo_url if instance.logo_url else None,
                'cover_image_url': instance.cover_image_url if instance.cover_image_url else None,
                'city': instance.city if instance.city else None,
            }
        
        elif model_name == 'promotion':
            # الحصول على الصورة (ImageField يُرجع url via .url)
            image_url = None
            if instance.image:
                try:
                    image_url = instance.image.url
                except:
                    pass
            
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description if instance.description else None,
                'promotion_type': instance.promotion_type,
                'value': float(instance.value) if instance.value else 0,
                'image_url': image_url,
                'active': instance.active,
                'start_at': instance.start_at.isoformat() if instance.start_at else None,
                'end_at': instance.end_at.isoformat() if instance.end_at else None,
                'approval_status': instance.approval_status,
            }
        
        elif model_name == 'coupon':
            return {
                'id': instance.id,
                'code': instance.code,
                'active': instance.active,
                'start_at': instance.start_at.isoformat() if instance.start_at else None,
                'end_at': instance.end_at.isoformat() if instance.end_at else None,
                'usage_limit': instance.usage_limit,
                'limit_per_user': instance.limit_per_user if instance.limit_per_user else None,
                'approval_status': instance.approval_status,
            }
        
        elif model_name == 'offer':
            # الحصول على الصورة (ImageField)
            image_url = None
            if instance.image:
                try:
                    image_url = instance.image.url
                except:
                    pass
            
            return {
                'id': instance.id,
                'name': instance.name,
                'description': instance.description if instance.description else None,
                'offer_type': instance.offer_type,
                'image_url': image_url,
                'active': instance.active,
                'start_at': instance.start_at.isoformat() if instance.start_at else None,
                'end_at': instance.end_at.isoformat() if instance.end_at else None,
                'approval_status': instance.approval_status,
                'configuration': instance.configuration,
            }
        
        elif model_name in ['productreview', 'storereview']:
            return {
                'id': instance.id,
                'rating': int(instance.rating) if hasattr(instance, 'rating') else 0,
                'comment': instance.comment if instance.comment else None,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
            }
        
        elif model_name == 'orderreview':
            return {
                'id': instance.id,
                'delivery_speed_rating': int(instance.delivery_speed_rating),
                'service_quality_rating': int(instance.service_quality_rating),
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
            }
        
        elif model_name in ['user', 'customuser']:
            return {
                'id': instance.id,
                'email': instance.email,
                'full_name': instance.get_full_name() if hasattr(instance, 'get_full_name') else None,
            }
        
        elif model_name == 'cartitem':
            return {
                'id': instance.id,
                'quantity': instance.quantity,
                'product_name': instance.variant.product.name if instance.variant and instance.variant.product else None,
                'added_at': instance.added_at.isoformat() if instance.added_at else None,
            }
        
        elif model_name == 'orderitem':
            return {
                'id': instance.id,
                'quantity': instance.quantity,
                'product_name_snapshot': instance.product_name_snapshot,
                'price_at_purchase': float(instance.price_at_purchase) if instance.price_at_purchase else 0,
                'status': instance.status,
            }
        
        elif model_name == 'productvariant':
            return {
                'id': instance.id,
                'product_name': instance.product.name if instance.product else None,
                'price': float(instance.price) if instance.price else 0,
                'sku': instance.sku if instance.sku else None,
                'options': instance.options,
            }
        
        elif model_name == 'productcategory':
            return {
                'id': instance.id,
                'name': instance.name,
                'store_name': instance.store.name if instance.store else None,
            }
        
        elif model_name == 'platformcategory':
            return {
                'id': instance.id,
                'name': instance.name,
                'image_url': instance.image_url if instance.image_url else None,
                'is_featured': instance.is_featured,
            }
        
        # ✅ Generic handler لأي model آخر - يجمع الحقول الأساسية تلقائياً
        else:
            result = {'id': instance.id, 'type': model_name}
            
            # محاولة جمع الحقول الشائعة
            common_fields = ['name', 'title', 'status', 'is_active', 'created_at']
            for field in common_fields:
                if hasattr(instance, field):
                    value = getattr(instance, field)
                    # تحويل القيم لأنواع قابلة للـ JSON
                    if hasattr(value, 'isoformat'):  # datetime objects
                        result[field] = value.isoformat()
                    elif isinstance(value, (int, str, bool, type(None))):
                        result[field] = value
                    else:
                        result[field] = str(value)
            
            # إضافة __str__ representation
            result['display_name'] = str(instance)
            
            return result
    
    except Exception as e:
        # في حالة حدوث خطأ، نرجع بيانات أساسية
        print(f"Warning: Error serializing content_object for notification {obj.id}: {e}")
        return {
            'id': obj.object_id,
            'type': content_type.model if content_type else 'unknown',
            'error': str(e)
        }
