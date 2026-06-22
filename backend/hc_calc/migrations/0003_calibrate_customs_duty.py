"""마진분석 모듈 보정 — 관세율 현실화.

문제: '관세 관련 비용' 설정값이 0.00125(HMF 0.125%만) 라 미국 수입관세 10%가 빠져
      있어 실제 발생 듀티 대비 비용을 크게 과소예측.
보정: 0.10125 (수입관세 10% + HMF 0.125%) 로 갱신.
      → HS 3924909000(플라스틱 식기) 등 10% 듀티 품목 기준. 실제 인보이스
        (DUTY 10% + HMF 0.125%) 와 일치.

코드 수정 없음(설정값 1건 update). 되돌리기(backward) 지원.
"""

from django.db import migrations

CUSTOMS_NAME = "관세 관련 비용"
NEW_VALUE = 0.10125  # 미국 수입관세 10% + HMF 0.125%
OLD_VALUE = 0.00125  # 보정 전 (HMF 0.125% 만)


def forward(apps, schema_editor):
    VC = apps.get_model("hc_calc", "VariableConfigurations")
    VC.objects.filter(name=CUSTOMS_NAME).update(value=NEW_VALUE)


def backward(apps, schema_editor):
    VC = apps.get_model("hc_calc", "VariableConfigurations")
    VC.objects.filter(name=CUSTOMS_NAME).update(value=OLD_VALUE)


class Migration(migrations.Migration):
    dependencies = [
        ("hc_calc", "0002_calculationlog_memo_calculationlog_product_name"),
    ]
    operations = [migrations.RunPython(forward, backward)]
