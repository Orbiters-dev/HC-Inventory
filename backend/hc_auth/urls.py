"""hc_auth 라우팅 (단일계정 세션 인증)."""

from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("session/status/", views.session_status, name="session_status"),
    path("change-password/", views.change_password, name="change_password"),
]
