"""hc_auth 라우팅.

P5 에서 배선:
  - login/            (POST, 세션 로그인)
  - logout/           (POST)
  - session/status/   (GET, FE AuthGate)
  - change-password/  (POST, 마이페이지 비번변경 + 초기PW 강제변경)
"""

from django.urls import path

urlpatterns = [
    # P5 에서 채움
]
