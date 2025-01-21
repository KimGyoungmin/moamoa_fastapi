from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, File, UploadFile
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from config import REST_API_KEY, CLIENT_SECRET, KAKAO_CALLBACK_URI
from database.models import User
from schema.request import UserUpdate
from schema.response import UserResponse, ChildResponse
from database.connection import get_db
from services.jwt_service import JWTService
import httpx
import hashlib
import os
import pytz
import shutil
import uuid

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    responses={404: {"description": "찾을 수 없습니다."}},
)

# # JWT 설정
# SECRET_KEY = "your_secret_key" # 추후 변경하기
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 300
#
# # 타임존 설정
# SEOUL_TZ = pytz.timezone("Asia/Seoul")

# JWT 생성
# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.now(SEOUL_TZ) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 인증된 사용자 가져오기 함수
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db),
                     jwt_service: JWTService = Depends(),
                     ):
    try:
        payload = jwt_service.verify_token(token=token)
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        user: User | None = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다.")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

# 카카오 로그인
@router.get("/auth/kakao/login")
def kakao_login():
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize?"
        f"client_id={REST_API_KEY}&redirect_uri={KAKAO_CALLBACK_URI}&response_type=code"
    )
    return {"url": kakao_auth_url}

# 카카오 콜백
@router.get("/auth/kakao/callback")
def kakao_callback(code: str, db: Session = Depends(get_db), jwt_service: JWTService = Depends()):
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
        )
        db.add(user)
    else:
        # 기존 사용자 정보 업데이트
        user.first_name = nickname
        user.images = images
    db.commit()
    db.refresh(user)

    token_data = {"sub": user.username}
    access_token = jwt_service.create_access_token(data=token_data)

    return {
        "message": "로그인 되었습니다.",
        "access_token": access_token,
        "user": UserResponse.model_validate(user),
    }


# # 유저 토큰 확인
# @router.get("/check_token/")
# def check_token(token: str = Depends(get_current_user)):
#     return {"message": "Token is valid"}

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

# 부모 조회
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
    db: Session = Depends(get_db),
    jwt_service: JWTService = Depends(),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=400, detail="사용할 수 없는 아이디나 비밀번호 입니다.")
    token = jwt_service.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "user": UserResponse.model_validate(user)}

# 아이들 로그아웃
@router.post("/logout/")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "로그아웃 되었습니다.`"}