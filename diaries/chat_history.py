from langchain_community.chat_message_histories import RedisChatMessageHistory
import pytz
from django.utils import timezone
from moamoa.config import REDIS_URL
from django.conf import settings


# 한국 시간대 설정
KOREA_TZ = pytz.timezone(settings.TIME_ZONE)

# 현재 한국 시간을 가져오는 함수
def get_current_korea_time():
    return timezone.now().astimezone(KOREA_TZ)

class CustomRedisChatMessageHistory(RedisChatMessageHistory):
    def add_message(self, message):
        # 현재 한국 시간 가져오기
        korea_time = get_current_korea_time()
        # 타임 스탬프 추가
        message.additional_kwargs['time_stamp'] = korea_time.isoformat()
        return super().add_message(message)

def get_current_korea_date():
    return get_current_korea_time().date()

# redis 저장 기간
three_months = 90 * 24 * 60 * 60

# Redis 방식 저장
def get_message_history(session_id: str) -> RedisChatMessageHistory:
    # 세션 id를 기반으로 RedisChatMessageHistory 객체를 반환
    return CustomRedisChatMessageHistory(session_id, url=REDIS_URL, ttl=three_months)


