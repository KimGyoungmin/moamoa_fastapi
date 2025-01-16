from datetime import date
from typing import Optional

from pydantic import BaseModel

from database.models import UserBase

# 키즈 회원가입
class UserCreate(UserBase):
    password: str
    first_name: str
    profile_image: Optional[str] = None

# 키즈 정보 수정
class UserUpdate(BaseModel):
    password: Optional[str] = None
    first_name: Optional[str] = None
    birthday: Optional[date] = None
    profile_image: Optional[str] = None


## 키즈 월별 용돈 기입장 리스트 요청
class ChildMonthlyList(BaseModel):
    child_id: int
    year: int
    month: int


