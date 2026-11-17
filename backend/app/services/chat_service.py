"""
AI 채팅 = '컨텍스트 주입'의 핵심

GPT는 한선 님의 데이터를 모릅니다. 그래서 질문할 때마다
  ① 데이터 요약을 꺼내고
  ② 시스템 프롬프트(=AI에게 주는 업무 지시서) 안에 끼워 넣고
  ③ GPT를 호출한 뒤
  ④ 대화를 conversations에 자동 저장합니다.
"""
import json

from openai import OpenAI

from app import config
from app.services import conversation_service, summary_service
from app.utils import now_iso

SYSTEM_TEMPLATE = """당신은 '서울 기온 데이터 분석 비서'입니다.

[사용자 데이터 요약] (서울 일 평균기온, 단위 ℃)
- 데이터 기간: {period}
- 총 레코드: {count}개
- 주요 지표: {metrics}
- 최근 트렌드: {trend}
- 월별 평균기온: {monthly_avg}
- 최근 7일: {recent}

[답변 규칙]
- 위 데이터를 근거로 맞춤형 답변을 하고, 숫자를 말할 때는 날짜나 기간을 함께 말하세요.
- 데이터의 마지막 날짜는 {latest_date}입니다. '이번 달', '최근'은 이 날짜를 기준으로 해석하세요.
- 요약에 없는 내용(예: 특정 날짜의 값)은 추측하지 말고 "요약 데이터에는 없다"고 솔직히 말하세요.
- 한국어로 3~5문장 이내, 친절하게 답하세요."""

HISTORY_LIMIT = 10  # 이전 대화는 최근 10개만 함께 보냄 (토큰=비용 절약)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY 환경 변수가 없습니다.")
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


def build_system_prompt(summary: dict) -> str:
    def dump(x):
        return json.dumps(x, ensure_ascii=False)

    return SYSTEM_TEMPLATE.format(
        period=summary["period"], count=summary["count"],
        metrics=dump(summary["metrics"]), trend=summary["trend"],
        monthly_avg=dump(summary["monthly_avg"]), recent=dump(summary["recent"]),
        latest_date=summary["latest_date"],
    )


def chat(message: str, conversation_id: str | None) -> tuple[str, str, dict]:
    # ① 요약 조회 (GET /api/data/summary 와 같은 함수)
    summary = summary_service.get_summary()

    # 이어서 하는 대화면 이전 메시지를 불러옴
    history = []
    if conversation_id:
        conv = conversation_service.get_conversation(conversation_id)
        if conv is None:
            raise LookupError("대화를 찾을 수 없습니다.")
        history = conv.get("messages", [])[-HISTORY_LIMIT:]

    # ② 시스템 프롬프트에 요약 주입
    messages = [{"role": "system", "content": build_system_prompt(summary)}]
    messages += [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})

    # ③ GPT 호출
    resp = _get_client().chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        max_tokens=config.OPENAI_MAX_TOKENS,
        temperature=0.3,
    )
    reply = (resp.choices[0].message.content or "").strip()

    # ④ 자동 저장
    now = now_iso()
    new_msgs = [
        {"role": "user", "content": message, "created_at": now},
        {"role": "assistant", "content": reply, "created_at": now},
    ]
    if conversation_id:
        conversation_service.append_messages(conversation_id, new_msgs)
    else:
        conversation_id = conversation_service.create_conversation(None, new_msgs)

    return reply, conversation_id, summary
