"""hc_auth — 단일 외부 계정 인증 뷰.

세션 기반 로그인 + 마이페이지 비번변경 + 초기PW 강제변경 게이트.
권한 시스템 없음(단일 계정). brute-force 방어는 nginx rate-limit(P7).
"""

import logging

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

logger = logging.getLogger(__name__)

MIN_PW_LEN = 6


def _payload(user):
    return {
        "authenticated": True,
        "user": user.get_username(),
        "password_change_required": getattr(user, "password_change_required", False),
    }


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def session_status(request):
    """FE AuthGate 용 — csrftoken 쿠키도 함께 내림(getCSRFToken 읽기용)."""
    if request.user.is_authenticated:
        return Response(_payload(request.user))
    return Response({"authenticated": False})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {"error": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=400
        )
    login(request, user)
    return Response(_payload(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({"authenticated": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_password(request):
    """마이페이지 비번변경 + 초기PW 강제변경(password_change_required 해제)."""
    current = request.data.get("current_password") or ""
    new = request.data.get("new_password") or ""
    user = request.user
    if not user.check_password(current):
        return Response({"error": "현재 비밀번호가 올바르지 않습니다."}, status=400)
    if len(new) < MIN_PW_LEN:
        return Response(
            {"error": f"새 비밀번호는 {MIN_PW_LEN}자 이상이어야 합니다."}, status=400
        )
    user.set_password(new)
    user.password_change_required = False
    user.save(update_fields=["password", "password_change_required"])
    update_session_auth_hash(request, user)  # 세션 유지(set_password 후 무효화 방지)
    return Response({"ok": True})
