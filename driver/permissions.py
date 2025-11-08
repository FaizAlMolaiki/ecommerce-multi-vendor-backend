from rest_framework.permissions import BasePermission

class IsDeliveryUser(BasePermission):
    """
    Allows access only to users with the 'is_delivery' flag set to True.
    """
    message = 'You do not have permission to perform this action as you are not a delivery person.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_delivery
