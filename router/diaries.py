from fastapi import APIRouter

from schema.request import ChildMonthlyList

router = APIRouter(
    prefix='/diary',
    tags=['diary']
)



# 아이 월별 용돈기입장 리스트
@router.get("/{child_id}/{year}/{month}")
def monthly_diary_view(
        request: ChildMonthlyList,

):
    # 1. child_id, year, month -> request
    # 2. child_id -> exist or not
    # 3. if exist -> check year, month & select diaries
    # 4. return select diaries
    return