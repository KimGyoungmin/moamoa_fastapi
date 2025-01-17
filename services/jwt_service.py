import pytz
from jose import jwt, JWTError
from datetime import datetime, timedelta

from fastapi import HTTPException

class JWTService:
    def __init__(self, secret_key: str, algorithm: str = "HS256", token_expire_minutes: int = 300):
        self.secret_key = "your_secret_key"
        self.algorithm = algorithm
        self.token_expire_minutes = token_expire_minutes
        self.seoul_tz = pytz.timezone = "Asia/Seoul"

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(self.seoul_tz) + timedelta(minutes=self.token_expire_minutes)
        to_encode.update({"exp" : expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)


    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
