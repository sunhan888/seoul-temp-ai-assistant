"""
conversations 컬렉션
문서 구조: conversations/{id} = {
    title: "가장 더웠던 날은?",
    messages: [ {role: "user", content: "...", created_at: "..."}, {role: "assistant", ...} ],
    created_at, updated_at
}
"""
from firebase_admin import firestore

from app.firebase import get_db
from app.utils import now_iso

COLLECTION = "conversations"


def create_conversation(title: str | None, messages: list[dict]) -> str:
    now = now_iso()
    for m in messages:
        m.setdefault("created_at", now)
        if m["created_at"] is None:
            m["created_at"] = now
    if not title:
        first_user = next((m["content"] for m in messages if m["role"] == "user"), "새 대화")
        title = first_user[:30]
    ref = get_db().collection(COLLECTION).document()
    ref.set({"title": title, "messages": messages, "created_at": now, "updated_at": now})
    return ref.id


def list_conversations() -> list[dict]:
    docs = (get_db().collection(COLLECTION)
            .order_by("updated_at", direction=firestore.Query.DESCENDING).stream())
    result = []
    for doc in docs:
        d = doc.to_dict()
        result.append({"id": doc.id, "title": d.get("title", "제목 없음"),
                       "message_count": len(d.get("messages", [])),
                       "updated_at": d.get("updated_at", "")})
    return result


def get_conversation(conv_id: str) -> dict | None:
    doc = get_db().collection(COLLECTION).document(conv_id).get()
    if not doc.exists:
        return None
    return {"id": doc.id, **doc.to_dict()}


def append_messages(conv_id: str, new_messages: list[dict]) -> None:
    ref = get_db().collection(COLLECTION).document(conv_id)
    doc = ref.get()
    messages = doc.to_dict().get("messages", []) + new_messages
    ref.update({"messages": messages, "updated_at": now_iso()})


def delete_conversation(conv_id: str) -> bool:
    ref = get_db().collection(COLLECTION).document(conv_id)
    if not ref.get().exists:
        return False
    ref.delete()
    return True
