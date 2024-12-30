from fastapi import APIRouter

# 라우터 초기화
router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    responses={404: {"description": "찾을 수 없습니다."}},
)