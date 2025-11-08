"""
JWT Authentication Middleware for WebSocket connections
"""
import jwt
from django.conf import settings
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs


class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT Authentication middleware for Django Channels WebSocket connections
    """
    
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        # استخراج JWT token من query parameters
        token = self.get_token_from_scope(scope)
        
        if token:
            user = await self.get_user_from_token(token)
            scope['user'] = user
        else:
            # لا يوجد JWT token - مستخدم غير مصادق
            from django.contrib.auth.models import AnonymousUser
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)

    def get_token_from_scope(self, scope):
        """استخراج JWT token من WebSocket query parameters"""
        try:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            
            # البحث عن token في query parameters
            if 'token' in query_params:
                return query_params['token'][0]
                
        except Exception as e:
            print(f'Error extracting token from scope: {e}')
        
        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        """التحقق من JWT token وإرجاع المستخدم"""
        try:
            # استيراد النماذج هنا لتجنب مشاكل الاستيراد المبكر
            from django.contrib.auth.models import AnonymousUser
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            # فك تشفير JWT token
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256']
            )
            
            # استخراج user_id من payload
            user_id = payload.get('user_id')
            if not user_id:
                print('No user_id in JWT payload')
                return AnonymousUser()
            
            # البحث عن المستخدم في قاعدة البيانات
            user = User.objects.get(id=user_id)
            
            # التحقق من أن المستخدم نشط
            if not user.is_active:
                print(f'User {user_id} is not active')
                return AnonymousUser()
            
            print(f'JWT Authentication successful for user: {user.email} (ID: {user.id})')
            return user
            
        except jwt.ExpiredSignatureError:
            print('JWT token has expired')
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        except jwt.InvalidTokenError as e:
            print(f'Invalid JWT token: {e}')
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()
        except Exception as e:
            print(f'Error in JWT authentication: {e}')
            from django.contrib.auth.models import AnonymousUser
            return AnonymousUser()



def JWTAuthMiddlewareStack(inner):
    """
    JWT Authentication middleware stack for WebSocket connections
    """
    return JWTAuthMiddleware(inner)
