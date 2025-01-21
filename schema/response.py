# refactor
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime

from pydantic import BaseModel

from database.models import UserBase



# 부모가 키즈 정보 확인할 때
class UserResponse(UserBase):
    id: int
    encouragement: Optional[str]
    first_name: Optional[str]
    profile_images: Optional[str] = None

    class Config:
        from_attributes = True

# 키즈 조회
class ChildResponse(UserResponse):
    parents_id: Optional[int]

# 부모가 키즈 정보 확인할 때
class ParentResponse(UserResponse):
    encouragement: Optional[str]
    first_name: Optional[str]
    images: Optional[str]

    class config:
        from_attribute = True

class DiarySchema(BaseModel):
    id: int
    diary_detail: str
    category:str
    transaction_type: str
    amount: Decimal
    remaining: int
    today: date
    created_at: datetime

    class Config:
        from_attribute = True

class MonthlyDiaryResponse(BaseModel):
    child_id: int
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    remaining_amount: int
    monthly_diaries: List[DiarySchema]

    class Config:
        from_attribute = True
