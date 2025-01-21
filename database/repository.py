# repository refactoring
from fastapi import Depends
from connection import get_db
from models import User, FinanceDiary
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy import Select, desc, extract



class UserRepository():
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_user_by_id(self, child_id: int) -> User | None:
        # request -> child_id
        return self.session.scalar(Select(User).where(User.id == child_id))


class DiaryRepository():
    def __init__(self, session: Session = Depends(get_db)):
        self.session = session

    def get_monthly_diaries(self, child_id: int, year: int, month: int) -> List[FinanceDiary]:
        return (
            self.session.query(FinanceDiary).filter(
                FinanceDiary.child_id == child_id,
                extract('year', FinanceDiary.today) == year,
                extract('month', FinanceDiary.today) == month
            ).order_by(desc(FinanceDiary.created_at), desc(FinanceDiary.id)).all()
        )

