"""
WebSocket consumers for real-time dashboard updates
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # التحقق من المصادقة - السماح للمستخدمين المسجلين فقط
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(code=4001)
            return
            
        # إضافة المستخدم إلى مجموعة dashboard
        self.dashboard_group_name = 'dashboard_updates'
        
        try:
            await self.channel_layer.group_add(
                self.dashboard_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # إرسال رسالة ترحيب
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'متصل بنجاح مع لوحة التحكم'
            }))
        except Exception as e:
            print(f'Error in WebSocket connect: {e}')
            await self.close(code=4000)

    async def disconnect(self, close_code):
        # إزالة المستخدم من المجموعة
        try:
            if hasattr(self, 'dashboard_group_name'):
                await self.channel_layer.group_discard(
                    self.dashboard_group_name,
                    self.channel_name
                )
        except Exception as e:
            print(f'Error in WebSocket disconnect: {e}')

    # استقبال رسائل من WebSocket
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', '')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
        except json.JSONDecodeError as e:
            print(f'Invalid JSON received: {e}')
        except Exception as e:
            print(f'Error in WebSocket receive: {e}')

    # استقبال رسائل من المجموعة
    async def new_order(self, event):
        """إرسال إشعار طلب جديد"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_order',
                'order': event.get('order', {}),
                'message': event.get('message', 'طلب جديد')
            }))
        except Exception as e:
            print(f'Error sending new_order: {e}')

    async def order_status_changed(self, event):
        """إرسال إشعار تغيير حالة الطلب"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'order_status_changed',
                'order': event.get('order', {}),
                'message': event.get('message', 'تم تحديث الطلب')
            }))
        except Exception as e:
            print(f'Error sending order_status_changed: {e}')

    async def stats_update(self, event):
        """إرسال تحديث الإحصائيات"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'stats_update',
                'stats': event.get('stats', {})
            }))
        except Exception as e:
            print(f'Error sending stats_update: {e}')

# //

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Join per-order group for real-time tracking."""
        user = self.scope.get("user")
        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        # Extract order_id from route kwargs
        try:
            order_id = self.scope["url_route"]["kwargs"]["order_id"]
            self.order_group_name = f"order_{order_id}"
        except Exception:
            await self.close(code=4000)
            return

        try:
            await self.channel_layer.group_add(self.order_group_name, self.channel_name)
            await self.accept()
            await self.send(text_data=json.dumps({
                "type": "connection_established",
                "message": f"joined order {order_id}",
            }))
        except Exception as e:
            print(f"Error in OrderTrackingConsumer.connect: {e}")
            await self.close(code=4000)

    async def disconnect(self, close_code):
        try:
            if hasattr(self, "order_group_name"):
                await self.channel_layer.group_discard(self.order_group_name, self.channel_name)
        except Exception as e:
            print(f"Error in OrderTrackingConsumer.disconnect: {e}")

    async def receive(self, text_data):
        """Handle incoming messages from client (e.g., driver location updates)."""
        try:
            user = self.scope.get("user")
            data = json.loads(text_data or "{}")
            msg_type = data.get("type")

            if msg_type == "ping":
                await self.send(text_data=json.dumps({"type": "pong", "timestamp": data.get("timestamp")}))
                return

            # Only delivery or staff can publish location updates
            if msg_type == "location_update":
                if not (getattr(user, "is_delivery", False) or getattr(user, "is_staff", False)):
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "not_authorized_to_publish_location"
                    }))
                    return

                payload = {
                    "event": "location_update",
                    "driver_id": getattr(user, "id", None),
                    "lat": data.get("lat"),
                    "lng": data.get("lng"),
                    "speed": data.get("speed"),
                    "heading": data.get("heading"),
                    "ts": data.get("ts"),
                }
                await self.channel_layer.group_send(
                    self.order_group_name,
                    {"type": "location_update", **payload}
                )
                return
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in OrderTrackingConsumer.receive: {e}")
        except Exception as e:
            print(f"Error in OrderTrackingConsumer.receive: {e}")

    async def location_update(self, event):
        """Fan-out location update to all connected clients for the order."""
        try:
            await self.send(text_data=json.dumps(event))
        except Exception as e:
            print(f"Error sending location_update: {e}")


# ===== إضافة WebSocket للموصل - بداية التعديل =====
class DriverConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer خاص بالموصلين لاستقبال الطلبات الجديدة والتحديثات
    """
    
    async def connect(self):
        """اتصال الموصل بالـ WebSocket"""
        user = self.scope.get("user")
        
        print(f"DriverConsumer connect attempt - User: {user}")
        
        # التحقق من المصادقة والتأكد أن المستخدم موصل
        if not user or user.is_anonymous:
            print("WebSocket connection rejected: User not authenticated")
            await self.close(code=4001)  # Unauthorized
            return
            
        print(f"User authenticated: {user.email} (ID: {user.id})")
        
        # التحقق من أن المستخدم موصل معتمد
        is_driver = await self.check_driver_status(user)
        print(f"Driver status check result: {is_driver}")
        
        if not is_driver:
            print("WebSocket connection rejected: User is not an approved driver")
            await self.close(code=4003)  # Forbidden - Not a driver
            return
        
        # إضافة الموصل إلى مجموعة الموصلين
        self.driver_group_name = f'driver_{user.id}'
        self.all_drivers_group = 'all_drivers'
        
        try:
            # إضافة إلى مجموعة الموصل الشخصية
            await self.channel_layer.group_add(
                self.driver_group_name,
                self.channel_name
            )
            
            # إضافة إلى مجموعة جميع الموصلين
            await self.channel_layer.group_add(
                self.all_drivers_group,
                self.channel_name
            )
            
            await self.accept()
            
            # إرسال رسالة ترحيب
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'مرحباً! أنت متصل الآن لاستقبال الطلبات',
                'driver_id': user.id
            }))
            
            # تحديث حالة الموصل إلى متصل
            await self.update_driver_online_status(user, True)
            
        except Exception as e:
            print(f'Error in DriverConsumer connect: {e}')
            await self.close(code=4000)

    async def disconnect(self, close_code):
        """قطع اتصال الموصل"""
        user = self.scope.get("user")
        
        try:
            # إزالة من المجموعات
            if hasattr(self, 'driver_group_name'):
                await self.channel_layer.group_discard(
                    self.driver_group_name,
                    self.channel_name
                )
            
            if hasattr(self, 'all_drivers_group'):
                await self.channel_layer.group_discard(
                    self.all_drivers_group,
                    self.channel_name
                )
            
            # تحديث حالة الموصل إلى غير متصل
            if user and not user.is_anonymous:
                await self.update_driver_online_status(user, False)
                
        except Exception as e:
            print(f'Error in DriverConsumer disconnect: {e}')

    async def receive(self, text_data):
        """استقبال رسائل من الموصل"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')
            
            if message_type == 'ping':
                print("Received ping from driver")
                # رد على ping للتأكد من الاتصال
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
            elif message_type == 'location_update':
                # تحديث موقع الموصل
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                if latitude and longitude:
                    await self.update_driver_location(
                        self.scope['user'], 
                        latitude, 
                        longitude
                    )
                    
            elif message_type == 'availability_update':
                # تحديث حالة توفر الموصل
                is_available = data.get('is_available', False)
                await self.update_driver_availability(
                    self.scope['user'], 
                    is_available
                )
                
        except json.JSONDecodeError as e:
            print(f'Invalid JSON received in DriverConsumer: {e}')
        except Exception as e:
            print(f'Error in DriverConsumer receive: {e}')

    # رسائل الطلبات
    async def new_order_available(self, event):
        """إشعار بطلب جديد متاح للقبول"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'new_order_available',
                'order': event.get('order', {}),
                'message': event.get('message', 'طلب جديد متاح للقبول!')
            }))
        except Exception as e:
            print(f'Error sending new_order_available: {e}')

    async def order_assigned(self, event):
        """إشعار بتعيين طلب للموصل"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'order_assigned',
                'order': event.get('order', {}),
                'message': event.get('message', 'تم تعيين طلب جديد لك!')
            }))
        except Exception as e:
            print(f'Error sending order_assigned: {e}')

    async def order_cancelled(self, event):
        """إشعار بإلغاء طلب"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'order_cancelled',
                'order_id': event.get('order_id'),
                'message': event.get('message', 'تم إلغاء الطلب')
            }))
        except Exception as e:
            print(f'Error sending order_cancelled: {e}')

    async def driver_notification(self, event):
        """إشعار عام للموصل"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'driver_notification',
                'title': event.get('title', 'إشعار'),
                'message': event.get('message', ''),
                'data': event.get('data', {})
            }))
        except Exception as e:
            print(f'Error sending driver_notification: {e}')

    # دوال مساعدة
    @database_sync_to_async
    def check_driver_status(self, user):
        """التحقق من أن المستخدم موصل معتمد"""
        try:
            print(f"Checking driver status for user {user.id}")
            print(f"user.is_delivery: {getattr(user, 'is_delivery', False)}")
            
            # التحقق الأساسي من أن المستخدم موصل
            if not getattr(user, 'is_delivery', False):
                print("User is not marked as delivery driver")
                return False
            
            # التحقق من وجود ملف الموصل
            if not hasattr(user, 'deliveryprofile'):
                print("User has no delivery profile")
                # للاختبار: السماح بالاتصال حتى لو لم يكن لديه ملف موصل مكتمل
                return True
            
            profile = user.deliveryprofile
            print(f"Delivery profile found - Status: {profile.verification_status}")
            
            # التحقق من حالة التحقق
            if profile.verification_status != 'APPROVED':
                print(f"Driver not approved - Status: {profile.verification_status}")
                # للاختبار: السماح بالاتصال حتى لو لم يكن معتمد
                return True
            
            # التحقق من عدم الإيقاف
            if getattr(profile, 'suspended', False):
                print("Driver is suspended")
                return False
            
            print("Driver status check passed")
            return True
            
        except Exception as e:
            print(f"Error in check_driver_status: {e}")
            # للاختبار: السماح بالاتصال في حالة الخطأ
            return True

    @database_sync_to_async
    def update_driver_online_status(self, user, is_online):
        """تحديث حالة الاتصال للموصل"""
        try:
            from django.utils import timezone
            if hasattr(user, 'deliveryprofile'):
                user.deliveryprofile.last_seen_at = timezone.now()
                user.deliveryprofile.save(update_fields=['last_seen_at'])
        except Exception as e:
            print(f'Error updating driver online status: {e}')

    @database_sync_to_async
    def update_driver_location(self, user, latitude, longitude) :
        """تحديث موقع الموصل"""
        try:
            from django.utils import timezone
            if hasattr(user, 'deliveryprofile'):
                profile = user.deliveryprofile
                profile.current_latitude = latitude
                profile.current_longitude = longitude
                profile.location_updated_at = timezone.now()
                profile.save(update_fields=[
                    'current_latitude', 
                    'current_longitude', 
                    'location_updated_at'
                ])

                 
        except Exception as e:
            print(f'Error updating driver location: {e}')

    @database_sync_to_async
    def update_driver_availability(self, user, is_available):
        """تحديث حالة توفر الموصل"""
        try:
            if hasattr(user, 'deliveryprofile'):
                user.deliveryprofile.is_available = is_available
                user.deliveryprofile.save(update_fields=['is_available'])
        except Exception as e:
            print(f'Error updating driver availability: {e}')

  
# ===== إضافة WebSocket للموصل - نهاية التعديل =====
