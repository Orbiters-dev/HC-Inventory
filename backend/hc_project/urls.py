"""HC-Inventory URL 라우팅.

- /admin/        : Django admin (운영자 데이터 관리)
- /api/          : 계산기 API (hc_calc — P2 에서 배선)
- /auth/         : 단일계정 로그인 (hc_auth — P5 에서 배선)
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("hc_calc.urls")),
    path("auth/", include("hc_auth.urls")),
]
