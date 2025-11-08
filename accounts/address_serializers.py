from rest_framework import serializers
from .models import UserAddress


class UserAddressSerializer(serializers.ModelSerializer):
    """
    Serializer for UserAddress model
    ✅ منطق ذكي لتعيين العنوان الافتراضي تلقائياً
    """
    
    class Meta:
        model = UserAddress
        fields = ['id', 'label', 'city', 'street', 'landmark', 
                  'latitude', 'longitude', 'is_default']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        """
        إذا كان هذا العنوان الافتراضي، إلغاء تعيين الافتراضية من العناوين الأخرى
        """
        if validated_data.get('is_default', False):
            UserAddress.objects.filter(
                user=validated_data['user']
            ).update(is_default=False)
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """
        إذا تم تعيين هذا العنوان كافتراضي، إلغاء تعيين الافتراضية من العناوين الأخرى
        """
        if validated_data.get('is_default', False):
            UserAddress.objects.filter(
                user=instance.user
            ).exclude(id=instance.id).update(is_default=False)
        
        return super().update(instance, validated_data)
