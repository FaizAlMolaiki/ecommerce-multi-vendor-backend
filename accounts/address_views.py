from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import UserAddress
from .address_serializers import UserAddressSerializer


class AddressPagination(PageNumberPagination):
    """Custom pagination for addresses"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserAddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user addresses
    
    Endpoints:
    - GET    /api/v1/accounts/addresses/              # List all addresses
    - POST   /api/v1/accounts/addresses/              # Create address
    - GET    /api/v1/accounts/addresses/{id}/         # Get address
    - PUT    /api/v1/accounts/addresses/{id}/         # Update address
    - PATCH  /api/v1/accounts/addresses/{id}/         # Partial update
    - DELETE /api/v1/accounts/addresses/{id}/         # Delete address
    - POST   /api/v1/accounts/addresses/{id}/set_default/  # Set as default
    """
    serializer_class = UserAddressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AddressPagination
    
    def get_queryset(self):
        """عرض عناوين المستخدم الحالي فقط"""
        return UserAddress.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """تعيين المستخدم الحالي عند إنشاء عنوان جديد"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """
        تعيين عنوان كافتراضي
        
        POST /api/v1/accounts/addresses/{id}/set_default/
        """
        address = self.get_object()
        
        # إلغاء تعيين جميع العناوين الأخرى كافتراضية
        UserAddress.objects.filter(user=request.user).update(is_default=False)
        
        # تعيين هذا العنوان كافتراضي
        address.is_default = True
        address.save()
        
        serializer = self.get_serializer(address)
        return Response(serializer.data)
