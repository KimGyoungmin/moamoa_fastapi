from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from schema.request import ChildMonthlyList
from schema.response import MonthlyDiaryResponse
from database.repository import UserRepository, DiaryRepository
from database.models import User
from accounts import get_current_user

router = APIRouter(
    prefix='/diary',
    tags=['diary']
)



# 아이 월별 용돈기입장 리스트
@router.get("/{child_id}/{year}/{month}")
async def monthly_diary_view(
        request: ChildMonthlyList,
        user_repo: UserRepository = Depends(),
        diary_repo: DiaryRepository = Depends(),
        current_user: User = Depends(get_current_user),
) -> MonthlyDiaryResponse:
    # 1. child_id, year, month -> request

    user: User | None = user_repo.get_user_by_id(request.child_id)
    # 2. child_id -> exist or not
    if not user:
        raise HTTPException(status_code=403, detail="다른 유저는 볼 권한이 없습니다.")
    # 3. if exist -> check year, month & select diaries
    diaries = diary_repo.get_monthly_diaries(
        child_id =request.child_id,
        year=request.year,
        month=request.month,
    )
    # 4. diaries exist -> get remaing price
    if diaries:
        remaining_amount = diaries[-1].remaining if diaries else 0
        total_income = sum(d.amount for d in diaries if d.transaction_type == "수입")
        total_expense = sum(d.amount for d in diaries if d.transaction_type == "지출")
    return MonthlyDiaryResponse(
        child_id=request.child_id,
        year=request.year,
        month=request.month,
        total_income=total_income,
        total_expense=total_expense,
        remaining_amount=remaining_amount,
        monthly_diaries=diaries,
        )