from typing import Optional

from database.models import UserBase



# 부모가 키즈 정보 확인할 때
class UserResponse(UserBase):
    id: int
    encouragement: Optional[str]
    first_name: Optional[str]
    profile_images: Optional[str] = None

    class Config:
        from_attributes = True

# 키즈 조회
class ChildResponse(UserResponse):
    parents_id: Optional[int]

# 부모가 키즈 정보 확인할 때
class ParentResponse(UserResponse):
    encouragement: Optional[str]
    first_name: Optional[str]
    images: Optional[str]

    class config:
        from_attribute = True
