from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, DateTime, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import pytz

# 타임존 설정
SEOUL_TZ = pytz.timezone("Asia/Seoul")

Base = declarative_base()


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


# 월말결산
class MonthlySummary(Base):
    __tablename__ = "monthly_summary"

    id = Column(Integer, primary_key=True, index=True)
    # child -> User id(FK)
    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # parent -> User id(FK)
    parent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # context -> String
    context = Column(String, nullable=False)
    # year -> Integer(Positive)
    year = Column(Integer, nullable=False)
    # month -> Integer(Positive)
    month = Column(Integer, nullable=False)
    # created_at
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(SEOUL_TZ),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint('year > 0', name='check_year_positive'),
        CheckConstraint('month > 0 AND month <= 12', name='check_month_range')
    )

    child = relationship(
        "User",
        foreign_keys=[child_id],
        backref="monthly_expenses",
        primaryjoin="MonthlySummary.child_id == User.id",
        )
    parent = relationship(
        "User",
        foreign_keys=[parent_id],
        backref="child_monthly_summary",
        primaryjoin="MonthlySummary.parent_id == User.id",
        )


