"""hc_calc summary 자동갱신 signal — calculations/signals.py 의 post_save receiver 3개.

원천 테이블 변경(admin 등) 시 파생 summary/fee 를 자동 재계산.
log_admin_login(AdminLoginLog/ipware)은 범위 밖이라 제외.

⚠️ 데이터 이관(계획 §3 H1/H9): 이 receiver 들은 raw 가드가 없어 loaddata 시에도 발화한다.
이관 관리명령은 loaddata 직전 disconnect() → update_all_summaries() 명시 호출 →
try/finally 로 reconnect 하여 이중적재를 구조적으로 차단한다(summary 는 key=1 upsert 라
재연결 누락 시에도 손상 없음 — 2차 안전망).
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import DeliveryIndex, ShippingRecord, ZoneWeight
from .services import ModelUpdater, SummaryUpdater


@receiver(post_save, sender=ShippingRecord)
def update_shipping_records_summary(sender, instance, **kwargs):
    SummaryUpdater.update_shipping_records_summary()


@receiver(post_save, sender=DeliveryIndex)
def update_delivery_indices_summary(sender, instance, **kwargs):
    SummaryUpdater.update_delivery_indices_summary()


@receiver(post_save, sender=ZoneWeight)
def update_model_instance(sender, instance, **kwargs):
    ModelUpdater.update_additional_delivery_fee(instance)
