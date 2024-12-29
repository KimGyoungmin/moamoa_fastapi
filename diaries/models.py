from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()

# 월말결산
class MonthlySummary(models.Model):
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plans")
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_plans")
    content = models.TextField()
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('child', 'parent', 'year', 'month')

    def __str__(self):
        return f"{self.child.username}의 {self.year}년 {self.month}월 결산 - {self.content}"

# 용돈기입장
class FinanceDiary(models.Model):
    child = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="diaries")
    parent = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="parent_diaries")
    diary_detail = models.TextField()
    category = models.CharField(max_length=100)
    transaction_type = models.CharField(max_length=7)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining = models.IntegerField(default = 0)
    today = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.child.username} - {self.diary_detail} ({self.transaction_type})"

