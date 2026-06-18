"""계산 기준 데이터 이관 — seed JSON loaddata + summary 재계산.

계획 §3 H1/H9 (summary 이중적재 구조적 차단):
  1. summary post_save receiver 3개 disconnect
  2. loaddata <seed>   (원천 + 수수료표, summary 2테이블은 fixture 에서 제외)
  3. SummaryUpdater 로 summary 재계산 (signal 비의존 단일 권위 경로)
  4. try/finally 로 receiver reconnect (loaddata~재계산 중간 크래시에도 보장)
  5. 재연결 + summary key=1 검증 (영구 disconnect 탐지)

2차 안전망: summary 는 key=1 단일행 upsert 라 재연결 누락 시에도 손상 없음(다음
쓰기/재시작이 자가복구) — finally + 2차안전망 이중.

사용:
  # EC2: 운영(calculations) → seed → 앱라벨 치환 → 전용 DB 적재
  prod-manage dumpdata calculations.VariableConfigurations ... > seed_raw.json
  sed 's/"model": "calculations\\./"model": "hc_calc./g' seed_raw.json > seed/calc_seed.json
  python manage.py seed_calc_data seed/calc_seed.json
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save

from hc_calc import signals as sig
from hc_calc.models import (
    DeliveryIndex,
    DeliveryIndicesSummary,
    ShippingRecord,
    ShippingRecordsSummary,
    ZoneWeight,
)
from hc_calc.services import SummaryUpdater

_RECEIVERS = [
    (sig.update_shipping_records_summary, ShippingRecord),
    (sig.update_delivery_indices_summary, DeliveryIndex),
    (sig.update_model_instance, ZoneWeight),
]


class Command(BaseCommand):
    help = "계산 기준 데이터 이관 (loaddata + summary 재계산, signal 이중적재 차단)"

    def add_arguments(self, parser):
        parser.add_argument("seed", help="seed JSON 경로 (app label = hc_calc)")

    def handle(self, *args, **opts):
        for fn, sender in _RECEIVERS:
            post_save.disconnect(fn, sender=sender)
        try:
            call_command("loaddata", opts["seed"])
            # summary 재계산 — signal 비의존 단일 권위 경로
            SummaryUpdater.update_all_summaries()
            self.stdout.write(self.style.SUCCESS("loaddata + summary 재계산 완료"))
        finally:
            for fn, sender in _RECEIVERS:
                post_save.connect(fn, sender=sender)

        # 재연결 + summary 검증
        reconnected = all(
            any(r[1]() is fn for r in post_save.receivers if r[1]() is not None)
            for fn, _ in _RECEIVERS
        )
        dis = DeliveryIndicesSummary.objects.filter(key=1).count()
        srs = ShippingRecordsSummary.objects.filter(key=1).count()
        ok = reconnected and dis == 1 and srs == 1
        mark = self.style.SUCCESS("✓") if ok else self.style.WARNING("⚠")
        self.stdout.write(
            f"{mark} reconnect={reconnected} summary key=1: dis={dis} srs={srs}"
        )
        if not ok:
            raise SystemExit("이관 검증 실패 — reconnect 또는 summary key=1 누락")
