"""hc_auth — 단일 외부 계정 인증 모델.

권한 시스템 없음(단일 계정 HC 운영). AbstractUser 최소 확장:
  - password_change_required: 초기 PW(123456) 첫 로그인 강제 변경 게이트 (계획 §16 H7).
  - partner_name: 거래처 표시명(선택).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class ExternalUser(AbstractUser):
    password_change_required = models.BooleanField(default=False)
    partner_name = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "hc_external_user"
