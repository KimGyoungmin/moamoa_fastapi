from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, DateTime
from sqlalchemy.orm import relationship
from database import Base
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import pytz

# 타임존 설정
SEOUL_TZ = pytz.timezone("Asia/Seoul")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True) # 키즈 아이디
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True) # 키즈 이름
    parents_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    birthday = Column(Date, nullable=True)
    images = Column(String, nullable=True, default="default_profile.png") # 부모 프로필
    profile_image = Column(String, nullable=True, default="default_profile.png") # 키즈 프로필
    encouragement = Column(Text, nullable=True) # 응원 메시지
    total = Column(Integer, default=0)
    created_at = Column(
        DateTime, default=lambda: datetime.now(SEOUL_TZ), nullable=False
    )
    updated_at = Column(
        DateTime, default=lambda: datetime.now(SEOUL_TZ), onupdate=lambda: datetime.now(SEOUL_TZ), nullable=False
    )
    children = relationship("User", backref="parents", remote_side=[id])

class UserBase(BaseModel):
    username: str
    birthday: Optional[date]

# 키즈 회원가입
class UserCreate(UserBase):
    password: str
    first_name: str
    profile_image: Optional[str] = None

# 키즈 조회
class UserResponse(UserBase):
    id: int
    encouragement: Optional[str]
    first_name: Optional[str]
    profile_images: Optional[str] = None

    #2025.01.11파트너 정보가 필요 
    parents_id: Optional[int] = None

    class Config:
        from_attributes = True

# 부모가 키즈 정보 확인할 때
class ChildResponse(UserResponse):
    parents_id: Optional[int]

# 키즈 정보 수정
class UserUpdate(BaseModel):
    password: Optional[str] = None
    first_name: Optional[str] = None
    birthday: Optional[date] = None
    profile_image: Optional[str] = None

# 부모 조회
class ParentResponse(UserResponse):
    encouragement: Optional[str]
    first_name: Optional[str]
    images: Optional[str]

    class config:
        from_attribute = True
