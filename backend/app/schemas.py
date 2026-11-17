"""
Pydantic 스키마 = API의 '입국 심사대'
요청 데이터가 규칙에 맞지 않으면 함수가 실행되기 전에 422 오류로 돌려보냅니다.
"""
from datetime import date as Date
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ---------- 시계열 데이터 ----------
class DataCreate(BaseModel):
    date: Date = Field(..., description="날짜 (YYYY-MM-DD)", examples=["2025-12-31"])
    value: float = Field(..., ge=-60, le=60, description="일 평균기온(℃)", examples=[-5.6])
    memo: str = Field("", max_length=200, description="메모", examples=["최저 -8.9 / 최고 -1.2"])


class DataUpdate(BaseModel):
    """수정은 바꾸고 싶은 필드만 보내면 됩니다."""
    date: Optional[Date] = None
    value: Optional[float] = Field(None, ge=-60, le=60)
    memo: Optional[str] = Field(None, max_length=200)

    @model_validator(mode="after")
    def at_least_one(self):
        if self.date is None and self.value is None and self.memo is None:
            raise ValueError("수정할 필드를 하나 이상 보내야 합니다.")
        return self


class DataItem(BaseModel):
    id: str
    date: str
    value: float
    memo: str = ""


class Summary(BaseModel):
    period: str
    count: int
    metrics: dict
    trend: str
    latest_date: Optional[str] = None
    monthly_avg: dict = {}
    recent: list = []


# ---------- 대화 ----------
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)
    created_at: Optional[str] = None


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    messages: list[Message] = Field(..., min_length=1)


class ConversationListItem(BaseModel):
    """목록에는 messages를 넣지 않습니다(가볍게). 전체 내용은 GET /api/conversations/{id}"""
    id: str
    title: str
    message_count: int
    updated_at: str


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: list[Message]
    created_at: str
    updated_at: str


# ---------- 채팅 ----------
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000, examples=["가장 더웠던 날은 언제야?"])
    conversation_id: Optional[str] = Field(None, description="이어서 대화할 때만 보냄")


class ChatResponse(BaseModel):
    reply: str
    conversation_id: str
    summary_used: Summary
