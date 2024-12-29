from rest_framework import serializers
from .models import FinanceDiary, MonthlySummary

class FinanceDiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinanceDiary
        fields = '__all__'

    def validate_transaction_type(self, value):
        if value not in ['수입', '지출']:  # 수입/지출 외 입력 방지
            raise serializers.ValidationError("거래 유형은 '수입' 또는 '지출'이어야 합니다.")
        return value
    
class MonthlySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlySummary
        fields = '__all__'

