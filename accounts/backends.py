from django.contrib.auth.backends import ModelBackend
from .models import User
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
            if user.check_password(password) and (user.is_verified or user.is_staff or user.is_superuser):
                return user
        except User.DoesNotExist:
            return None
    def get_user(self, user_id):
        return super().get_user(user_id)