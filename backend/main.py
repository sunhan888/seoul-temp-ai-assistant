"""
앱의 '현관문' — FastAPI 앱을 만들고, CORS를 설정하고, 라우터(창구)들을 연결합니다.

로컬 실행 (backend 폴더에서):
    uvicorn main:app --reload
    → http://127.0.0.1:8000/docs  (Swagger UI)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routers import chat, conversations, data

app = FastAPI(
    title="서울 기온 AI 비서 API",
    description="서울 2025년 일 평균기온 데이터를 이해하고 답하는 AI 비서의 백엔드",
    version="1.0.0",
)

# CORS: '다른 주소(Vercel)에서 온 브라우저 요청'을 허락할 목록
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/", tags=["상태"])
def root():
    return {"message": "서울 기온 AI 비서 API", "docs": "/docs"}


@app.get("/health", tags=["상태"], summary="서버 깨어있는지 확인 (콜드스타트 체크용)")
def health():
    return {"status": "ok"}
