"""마진분석 모듈 보정 — 항만료(과대) + 수취료(과소, 3PL 누락) 현실화.

실제 인보이스(AP Shipping, 부산→Hesperia AWD, 20팔레트 FCL) 대비:
- 항만료: 모듈 ~$1,594 vs 실제 THC+씰+보안 ~$156 → 요율 ~10배 과대.
          → '항만료' 설정값을 0.098배로 보정.
- 수취료: 모듈 $9.5/팔레트(=$190) 에 미국 내륙운송(AWD까지 $1,650)·포워더
          핸들링커미션($1,000)·한국 트럭킹($515) 등 3PL 비용이 빠짐.
          실제 트럭킹/수취/핸들링 합 ~$3,362/컨테이너(20팔레트) → $168.13/팔레트.
          → 'Receiving' 설정값 9.5 → 168.13 (3PL 내륙운송·핸들링 포함).

→ 너희 표준 라인(부산→Hesperia AWD, 20팔레트 FCL) 기준 실비 반영.
  코드 수정 없음(설정값 2건). 되돌리기(backward) 지원.
"""

from django.db import migrations

PORT_NAME = "항만료"
PORT_SCALE = 0.098  # ~$1,594 → ~$156

RECEIVING_NAME = "Receiving"
RECEIVING_NEW = 168.13  # 3PL 내륙운송+핸들링 포함 ($/팔레트)
RECEIVING_OLD = 9.5


def forward(apps, schema_editor):
    VC = apps.get_model("hc_calc", "VariableConfigurations")
    port = VC.objects.filter(name=PORT_NAME).first()
    if port:
        port.value = port.value * PORT_SCALE
        port.save(update_fields=["value"])
    VC.objects.filter(name=RECEIVING_NAME).update(value=RECEIVING_NEW)


def backward(apps, schema_editor):
    VC = apps.get_model("hc_calc", "VariableConfigurations")
    port = VC.objects.filter(name=PORT_NAME).first()
    if port:
        port.value = port.value / PORT_SCALE
        port.save(update_fields=["value"])
    VC.objects.filter(name=RECEIVING_NAME).update(value=RECEIVING_OLD)


class Migration(migrations.Migration):
    dependencies = [
        ("hc_calc", "0004_calibrate_feu_freight"),
    ]
    operations = [migrations.RunPython(forward, backward)]
