from sqlmodel import Field, SQLModel, Relationship, create_engine
from typing import Optional, List
from datetime import datetime
from pydantic import EmailStr

class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)
    email: Optional[EmailStr] = Field(default=None, unique=True, index=True)
    profile_image: Optional[str] = Field(default="default_profile.png")
    encouragement: Optional[str] = Field(default=None)
    birthday: Optional[datetime] = Field(default=None)
    total: int = Field(default=0)
    is_active: bool = Field(default=True)
    
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="user.id")
    hashed_password: str
    
    
    
    # 1:N 관계 설정
    # 부모는 있을수도 없을수도 있고 자녀는 한부모에 여러명이 있을수 있다.
    parent: Optional["User"] = Relationship(
        # 역참조 할때 사용할 수 있음.... ex) user.children
        back_populates="children",
        # 부모와 자녀를 구분할 수 있는 매개변수
        sa_relationship_kwargs={"remote_side": [id]}
    )
    children: List["User"] = Relationship(back_populates="parent")
    
class Settings(SQLModel):
    DATABASE_URL: str = "sqlite:///database.db"
    echo: bool = True
    
settings = Settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.echo,
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
    