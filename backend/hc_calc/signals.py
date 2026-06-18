"""hc_calc summary 자동갱신 signal.

P2 에서 원본 calculations/signals.py 의 summary receiver 3개를 이식한다
(SummaryUpdater 기반 DeliveryIndicesSummary / ShippingRecordsSummary 자동 재계산).
log_admin_login receiver 는 제외(AdminLoginLog 범위 밖).

⚠️ 데이터 이관(계획 §3 H1/H9): loaddata 직전 이 receiver 들을 disconnect() 하고
update_all_summaries() 명시 호출 후 try/finally 로 reconnect — 이중적재 구조적 차단.
"""

# P2 에서 receiver 추가 예정.
