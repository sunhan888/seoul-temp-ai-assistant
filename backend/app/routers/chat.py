import logging

from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from app.schemas import ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(prefix="/api", tags=["AI 채팅"])
log = logging.getLogger("chat")


@router.post("/chat", response_model=ChatResponse, summary="AI 대화 (데이터 요약 주입 + 자동 저장)")
def chat(req: ChatRequest):
    try:
        reply, conv_id, summary = chat_service.chat(req.message, req.conversation_id)
    except LookupError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:          # 환경 변수 누락 등 설정 문제
        raise HTTPException(500, str(e))
    except OpenAIError as e:           # 키 오류, 한도 초과, 네트워크 등
        log.exception("OpenAI 호출 실패")
        raise HTTPException(502, f"AI 응답 생성에 실패했습니다: {type(e).__name__}")
    return {"reply": reply, "conversation_id": conv_id, "summary_used": summary}
