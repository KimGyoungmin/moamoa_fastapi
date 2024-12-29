from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    parents = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children',
                                help_text='부모님 기본 0 | 아이들은 부모님 번호')
    birthday = models.DateField(null=True, blank=True, help_text='생년월일')
    images = models.ImageField(upload_to='profile_images/', null=True, blank=True, default='default_profile.png', help_text='프로필 이미지')
    encouragement = models.TextField(blank=True, null=True, help_text='부모님이 자녀에게 남기는 격려 메시지')
    total = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        # 기본 이미지를 설정하고 저장 로직을 오버라이드 할 필요가 없음
        super().save(*args, **kwargs)

