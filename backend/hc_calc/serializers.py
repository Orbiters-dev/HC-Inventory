from rest_framework import serializers

from .models import CalculationLog


class CalculationLogSerializer(serializers.ModelSerializer):
    """계산 이력 직렬화 — 입력값 + 결과 + 시각 전체."""

    class Meta:
        model = CalculationLog
        fields = "__all__"
