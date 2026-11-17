"""
환경 변수 모음 — 비밀번호(키)는 코드에 쓰지 않고 '금고(.env / Render 설정)'에서 꺼내 씁니다.
로컬: backend/.env 파일 / 배포: Render 대시보드 Environment 탭
"""
import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일이 있으면 읽어서 os.environ에 넣어줌

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))  # 과금 방지용 답변 길이 제한

# 서비스 계정 키: JSON 내용 전체(배포용) 또는 파일 경로(로컬용) 중 하나
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")

# CORS 허용 도메인 (쉼표로 구분)
ALLOWED_ORIGINS = [
    o.strip().rstrip("/")
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500"
    ).split(",")
    if o.strip()
]
