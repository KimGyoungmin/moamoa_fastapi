from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from router import accounts
from database import engine, Base
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from fastapi import Depends
from models import User
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from database import get_db, engine, Base
import base64
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI()


# 2025.01.11 세션 미들웨어 추가
app.add_middleware(
    SessionMiddleware,
    secret_key="moamoa1004!!@@",
    session_cookie="session"
)

# 2025.01.11 정적 파일 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2025.01.11템플릿 설정
templates = Jinja2Templates(directory="templates")

# 2025.01.12 CSS 버전 관리 나중에 제거 
templates.env.filters["strftime"] = lambda value: datetime.now().strftime(value)

app.include_router(accounts.router)

#2025.01.11 메인 및 프로필 적용
@app.get("/")
async def read_root(request: Request):
    # 로그아웃 상태에서는 메인 페이지로, 로그인 상태에서만 프로필로 리다이렉트
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/profile")
    return templates.TemplateResponse("webs/index.html", {"request": request})
    

#2025.01.11 프로필 적용
#2025.01.11 프로필 토큰 적용
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):

    try:
        access_token = request.session.get("access_token")
        if not access_token:
            return RedirectResponse(url="/")
            
        current_user = accounts.get_current_user(access_token, db)
        # 2025.01.11보안
        encoded_token = base64.b64encode(access_token.encode()).decode() if access_token else ""

        return templates.TemplateResponse(
            "webs/profile.html",
            {
                "request": request,
                "headermenuleft" : "hidden",
                "user": current_user,
                "encoded_token": encoded_token
            }
        )
    except Exception as e:
        print(e)
        return RedirectResponse(url="/")


# 2025.01.12 부모님 로그인에서 아이들 회원가입
@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, db: Session = Depends(get_db)):
    access_token = request.session.get("access_token")
    if not access_token:
        return RedirectResponse(url="/")
    return templates.TemplateResponse("webs/children_create.html", {"request": request})
