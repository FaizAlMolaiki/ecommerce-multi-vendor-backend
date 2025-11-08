from driver.models import DeliveryProfile
from rest_framework import serializers


class DeliveryProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryProfile
        fields = [
            'user',
            'vehicle_type', 
            'license_plate', 
            'id_card_image', 
            'driver_license_image',
            'verification_status',
            # 'rejection_reason'
        ]
        read_only_fields = ['user', 'verification_status']

    def validate(self, data):
        # الوصول للمستخدم من سياق الطلب الذي سيتم تمريره من الـ View
        user = self.context['request'].user
        if DeliveryProfile.objects.filter(user=user,).exists():
            raise serializers.ValidationError("لقد قمت بتقديم طلب بالفعل.")
        return data