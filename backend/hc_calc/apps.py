from django.apps import AppConfig


class HcCalcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hc_calc"

    def ready(self):
        # P2: summary 자동갱신 signal 등록 (loaddata 이관 시 disconnect 패턴 — 계획 §3 H1/H9)
        from . import signals  # noqa: F401
