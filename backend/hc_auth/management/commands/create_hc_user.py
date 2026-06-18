"""단일 외부 계정(HC) 생성/초기화.

초기 PW 123456 + password_change_required=True (첫 로그인 시 강제 변경).
일반 계정(admin 아님) — 계산기 사용 전용. fee 데이터 관리용 admin superuser 는
운영자가 별도 createsuperuser 로 생성(외부 계정에 admin 미부여).

  python manage.py create_hc_user                # HC/123456 생성
  python manage.py create_hc_user --reset        # 이미 있으면 PW 초기화
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "단일 외부 계정 HC 생성/초기화 (초기 PW 123456, 첫 로그인 강제 변경)"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="HC")
        parser.add_argument("--password", default="123456")
        parser.add_argument(
            "--reset", action="store_true", help="이미 있으면 PW/강제변경 재설정"
        )

    def handle(self, *args, **opts):
        User = get_user_model()
        username = opts["username"]
        password = opts["password"]
        obj, created = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": False, "is_superuser": False},
        )
        if created or opts["reset"]:
            obj.set_password(password)
            obj.password_change_required = True
            obj.is_staff = False
            obj.is_superuser = False
            obj.save()
            action = "생성" if created else "재설정"
            self.stdout.write(
                self.style.SUCCESS(f"{action}: {username} (초기PW + 강제변경 ON)")
            )
        else:
            self.stdout.write(f"이미 존재: {username} (--reset 으로 PW 재설정)")
