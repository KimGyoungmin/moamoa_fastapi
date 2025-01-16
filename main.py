from fastapi import FastAPI
from router import accounts, diaries
from database.connection import engine
from database.models import Base

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(accounts.router)
app.include_router(diaries.router)

@app.get("/")
def read_root():
    return {"moamoa"}