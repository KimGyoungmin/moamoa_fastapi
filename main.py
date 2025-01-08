from fastapi import FastAPI
from router import accounts
from database import engine, Base

# 데이터베이스 초기화
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(accounts.router)

@app.get("/")
def read_root():
    return {"moamoa"}