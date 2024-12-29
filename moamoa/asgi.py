"""
ASGI config for moamoa project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'moamoa.settings')

application = get_asgi_application()
# django_asgi_app = get_asgi_application()


# # channels 라우팅과 미들웨어는 Django 초기화 이후에 가져와야 합니다.
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.security.websocket import AllowedHostsOriginValidator
# import diaries.routing  # 이제 이 코드는 안전하게 실행될 수 있습니다.

# application = ProtocolTypeRouter({
#     "http": django_asgi_app,
#     "websocket": 
#         AuthMiddlewareStack(
#             AllowedHostsOriginValidator(
#             URLRouter(
#                 diaries.routing.websocket_urlpatterns
#             )     
#         ),
#     ),
# })