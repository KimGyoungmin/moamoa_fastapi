from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, File, UploadFile, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from config import REST_API_KEY, CLIENT_SECRET, KAKAO_CALLBACK_URI
from models import User, UserCreate, UserResponse, ChildResponse, UserUpdate, ParentResponse
from database import get_db
import httpx
import hashlib
import os
import pytz
import shutil
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    responses={404: {"description": "찾을 수 없습니다."}},
)

# JWT 설정
# SECRET_KEY = "your_secret_key" # CLIENT_SECRET 적용
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300

# 타임존 설정
SEOUL_TZ = pytz.timezone("Asia/Seoul")

# JWT 생성
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(SEOUL_TZ) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, CLIENT_SECRET, algorithm=ALGORITHM)
    return jwt.encode(to_encode, CLIENT_SECRET, algorithm=ALGORITHM)

# 인증된 사용자 가져오기 함수 수정
def get_current_user(token: str, db: Session = Depends(get_db)):  # OAuth2PasswordBearer 의존성 제거
    try:
        payload = jwt.decode(token, CLIENT_SECRET, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

# 2025.01.11 Templates 설정 추가
templates = Jinja2Templates(directory="templates")

# 카카오 로그인
@router.get("/auth/kakao/login")
def kakao_login():
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={REST_API_KEY}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code"
    )
    return {"url": kakao_auth_url}

# 카카오 콜백 2025.01.11
@router.get("/auth/kakao/callback")
async def kakao_callback(request: Request, code: str, db: Session = Depends(get_db)):
    try:
        token_url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": REST_API_KEY,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": KAKAO_CALLBACK_URI,
            "code": code,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        with httpx.Client() as client:
            token_response = client.post(token_url, headers=headers, data=data)
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="토큰을 가져오는 데 실패했습니다.")
            access_token = token_response.json().get("access_token")

        user_info_url = "https://kapi.kakao.com/v2/user/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client() as client:
            user_info_response = client.get(user_info_url, headers=headers)
            if user_info_response.status_code != 200:
                raise HTTPException(status_code=400, detail="사용자 정보를 불러오지 못했습니다.")
            user_info = user_info_response.json()

        kakao_id = str(user_info["id"])
        email = user_info["kakao_account"].get("email")
        nickname = user_info["kakao_account"]["profile"].get("nickname")
        images = user_info["kakao_account"]["profile"].get("profile_image")

        hash_object = hashlib.sha256(kakao_id.encode())
        password_hash = hash_object.hexdigest()

        user = db.query(User).filter(User.username == kakao_id).first()
        if not user:
            user = User(
                username=kakao_id,
                email=email,
                password=password_hash,
                first_name=nickname,
                images=images,
                parents_id=None #2025.01.11 파트너 정보가 필요
            )
            db.add(user)
        else:
            # 기존 사용자 정보 업데이트
            user.first_name = nickname
            user.images = images
        db.commit()
        db.refresh(user)

        token_data = {"sub": user.username}
        access_token = create_access_token(data=token_data)

        
        # 2025.01.11 세션에 토큰 저장
        request.session["access_token"] = access_token
        
        # 2025.01.11 프로필 페이지로 리다이렉트
        response = RedirectResponse(url="/profile")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800,  # 30분
            secure=False  # 개발환경에서는 False, 프로덕션에서는 True
        )
        return response

    except Exception as e:
        return JSONResponse(
            status_code=404,
            content={"detail": str(e)}
        )

# 아이들 회원가입
@router.post("/children/create")
def create_child(
    username: str,
    password: str,
    first_name: str,
    birthday: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    profile_image: UploadFile = File(None),
):
    if not current_user:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    # 프로필 이미지 저장 처리
    image_path = None
    if profile_image:
        # 파일 저장 디렉토리 생성 
        upload_dir = "uploads/children"
        os.makedirs(upload_dir, exist_ok=True)

        # 파일 이름을 고유하게 설정
        unique_filename = f"{uuid.uuid4()}_{profile_image.filename}"
        image_path = os.path.join(upload_dir, unique_filename)

        # 파일 저장
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(profile_image.file, buffer)

    # 아이 아이디 객체 생성
    birthday_date = datetime.strptime(birthday, "%Y-%m-%d").date()

    new_child = User(
        username=username,
        password=password,
        first_name=first_name,
        birthday=birthday_date,
        parents_id=current_user.id, # 부모와 연결
        profile_image=image_path,
    )
    db.add(new_child)
    db.commit()
    db.refresh(new_child)

    return ChildResponse.model_validate(new_child)

# 아이들 조회
@router.get("/children/{child_id}/")
def get_child(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    child = db.query(User).filter(User.id == child_id, User.parents_id == current_user.id).first()
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다.")
    return ChildResponse.model_validate(child)

# 아이들 수정
@router.put("/children/{child_id}/")
def update_child(
    child_id: int,
    child: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 아이와 부모 관계 확인
    existing_child = db.query(User).filter(User.id == child_id, User.parents_id == current_user.id).first()
    if not existing_child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다.")
    
    for key, value in child.model_dump(exclude_unset=True).items():
        setattr(existing_child, key, value)
    
    db.commit()
    db.refresh(existing_child)
    return ChildResponse.model_validate(existing_child)

# 아이들 삭제
@router.delete("/children/{child_id}/")
def delete_child(
    child_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    child = db.query(User).filter(User.id == child_id, User.parents_id == current_user.id).first()
    
    if not child:
        raise HTTPException(status_code=404, detail="아이를 찾을 수 없습니다.")
    
    db.delete(child)
    db.commit()
    return {"message": "아이 계정이 삭제 되었습니다."}


@router.get("/") 
def get_parent(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "images": current_user.images,
    }

# 아이들 로그인
@router.post("/login/")
def child_login(
    username: str,
    password: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=400, detail="사용할 수 없는 아이디나 비밀번호 입니다.")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "user": UserResponse.model_validate(user)}

# 2025.01.12 아이들 로그아웃
@router.post("/logout/")
def logout(request: Request, response: Response):
    
    # 세션 및 쿠키 모두 제거
    if "access_token" in request.session:
        del request.session["access_token"]
    
    # 응답 생성 (리다이렉트)
    response = RedirectResponse(url="/",status_code=303  )
    
    # 쿠키 삭제
    response.delete_cookie(key="access_token",path="/",secure=False,httponly=True)
    
    return response