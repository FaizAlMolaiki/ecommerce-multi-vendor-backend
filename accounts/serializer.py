from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

User = get_user_model()



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'name', 'phone_number',
            'is_active', 'is_verified', 'is_vendor', 'is_delivery', 'is_staff'
        )
        

class RegisterSerializer(serializers.Serializer):
    name=serializers.CharField(required=False,max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(validators=[validate_password])

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ConfirmResetSerializer(serializers.Serializer):
    reset_token =  serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(validators=[validate_password])

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    

class CheckPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()
    
    
