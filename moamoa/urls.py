from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static #20241004


urlpatterns = [
    # 프론트엔드 페이지
    path('', include("webs.urls")), # 프론트엔드

    # API 엔드포인트
    path('admin/', admin.site.urls),
    path('api/v1/accounts/', include("accounts.urls")),  # 회원
    path('api/v1/diary/', include("diaries.urls")),  # 용돈기입장
]

# 개발 환경에서 미디어 파일 서빙
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

