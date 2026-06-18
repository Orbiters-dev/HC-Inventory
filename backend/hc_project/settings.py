"""
HC-Inventory 계산기 독립 사이트 — Django settings.

대시보드(WONGI/export_calculator)와 완전 분리된 standalone 설정.
- INSTALLED_APPS / MIDDLEWARE 화이트리스트 (datakeeper/onzenna/prometheus 등 제거).
- 단일 외부 계정 인증: AUTH_USER_MODEL = hc_auth.ExternalUser, DRF 전역 IsAuthenticated.
- 시크릿은 전부 환경변수(EnvironmentFile). repo 가 public 이므로 하드코딩 금지.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# --- 시크릿 / 환경 (전부 env, public repo 라 하드코딩 금지) ---
SECRET_KEY = os.environ.get("HC_SECRET_KEY", "dev-insecure-change-me-in-prod")
DEBUG = os.environ.get("HC_DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    h for h in os.environ.get("HC_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h
]
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("HC_CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

# --- 앱 (최소 화이트리스트) ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "hc_auth",
    "hc_calc",
]

# --- 미들웨어 (Django 표준만 — datakeeper.core.* / prometheus 제거) ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hc_project.urls"
WSGI_APPLICATION = "hc_project.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- DB: 전용 PostgreSQL (5434, WONGI 5433 과 프로세스 분리). 전부 env ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("HC_DB_NAME", "hc_inventory"),
        "USER": os.environ.get("HC_DB_USER", "hc_user"),
        "PASSWORD": os.environ.get("HC_DB_PASSWORD", ""),
        "HOST": os.environ.get("HC_DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("HC_DB_PORT", "5434"),
        # 전용 cluster 라 statement_timeout 미설정(PG 기본 0=무제한) → 이관/재집계 timeout 비위험.
    }
}

AUTH_USER_MODEL = "hc_auth.ExternalUser"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
]

# --- DRF: 전역 인증 강제 (계산 5뷰 + 이력뷰 자동 보호). 단일계정이라 권한모델 없음 ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- 보안 (외부 노출, "적당히") — prod 는 env 로 켬 ---
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # FE getCSRFToken 이 쿠키 read (same-origin double-submit)
SESSION_COOKIE_SECURE = os.environ.get("HC_SECURE", "0") == "1"
CSRF_COOKIE_SECURE = os.environ.get("HC_SECURE", "0") == "1"
SECURE_SSL_REDIRECT = os.environ.get("HC_SECURE", "0") == "1"
if os.environ.get("HC_SECURE", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SESSION_COOKIE_AGE = int(os.environ.get("HC_SESSION_AGE", str(60 * 60 * 8)))  # 8h 기본
