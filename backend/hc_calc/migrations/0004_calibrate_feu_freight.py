"""마진분석 모듈 보정 — FEU(40'HQ) 해상운임 현실화.

문제: 11~20 팔레트(FCL) 구간 해상운임 = recent_feu × avg_real_per_idx_feu 가
      약 $7,995 로, 실제 40'HQ 해상운임(~$3,188, AP Shipping 인보이스 평균) 대비
      약 2.5배 과대예측. 운임지수가 과거 고시세 기준.
보정: DeliveryIndex.real_per_idx_feu 원본값을 일괄 스케일하여 FEU 운임이 ~$3,188
      이 되게 한다. 원본 데이터를 바꾸므로 SummaryUpdater 재계산에도 유지(durable).
      → FEU(40'HQ) 운임에만 영향. per-product(소량) 마진·TEU 계산에는 영향 없음.

코드 수정 없음(데이터 보정). 되돌리기(backward) 지원.
"""

from django.db import migrations
from django.db.models import Avg

TARGET_NEW = 3188.0  # 현재 40'HQ 실제 해상운임 (인보이스 001 $3,162 / 002 $3,213 평균)
TARGET_OLD = 7995.0  # 보정 전 관측값 (되돌리기 기준)


def _recalibrate_feu(apps, target):
    DeliveryIndex = apps.get_model("hc_calc", "DeliveryIndex")
    Summary = apps.get_model("hc_calc", "DeliveryIndicesSummary")

    s = Summary.objects.filter(key=1).first()
    if not s or not s.recent_feu or not s.avg_real_per_idx_feu:
        return  # 운임지수 미설정 — 보정 생략(안전)
    current = s.recent_feu * s.avg_real_per_idx_feu
    if current <= 0:
        return
    factor = target / current

    # 원본 DeliveryIndex.real_per_idx_feu 일괄 스케일 (재계산 시에도 유지)
    for di in DeliveryIndex.objects.exclude(real_per_idx_feu=None):
        di.real_per_idx_feu = di.real_per_idx_feu * factor
        di.save(update_fields=["real_per_idx_feu"])

    # 요약 재계산 (계산기가 읽는 값)
    new_avg = DeliveryIndex.objects.aggregate(Avg("real_per_idx_feu"))[
        "real_per_idx_feu__avg"
    ]
    s.avg_real_per_idx_feu = new_avg
    s.save(update_fields=["avg_real_per_idx_feu"])


def forward(apps, schema_editor):
    _recalibrate_feu(apps, TARGET_NEW)


def backward(apps, schema_editor):
    _recalibrate_feu(apps, TARGET_OLD)


class Migration(migrations.Migration):
    dependencies = [
        ("hc_calc", "0003_calibrate_customs_duty"),
    ]
    operations = [migrations.RunPython(forward, backward)]
