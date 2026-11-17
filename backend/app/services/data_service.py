"""
data 컬렉션 CRUD — Firestore와 직접 대화하는 곳 (라우터는 여기만 부르면 됨)
문서 구조: data/{id} = { date: "2025-01-01", value: 2.6, memo: "...", created_at: "..." }
"""
from app.firebase import get_db
from app.schemas import DataCreate, DataUpdate
from app.services import summary_service
from app.utils import now_iso

COLLECTION = "data"


def _to_item(doc) -> dict:
    d = doc.to_dict()
    return {"id": doc.id, "date": d["date"], "value": d["value"], "memo": d.get("memo", "")}


def list_data() -> list[dict]:
    docs = get_db().collection(COLLECTION).order_by("date").stream()
    return [_to_item(doc) for doc in docs]


def create_data(item: DataCreate) -> dict:
    ref = get_db().collection(COLLECTION).document()  # 자동 ID
    ref.set({
        "date": item.date.isoformat(),
        "value": item.value,
        "memo": item.memo,
        "created_at": now_iso(),
    })
    summary_service.invalidate_cache()  # 데이터가 바뀌었으니 요약 다시 계산
    return _to_item(ref.get())


def update_data(data_id: str, patch: DataUpdate) -> dict | None:
    ref = get_db().collection(COLLECTION).document(data_id)
    if not ref.get().exists:
        return None
    fields = patch.model_dump(exclude_none=True)
    if "date" in fields:
        fields["date"] = fields["date"].isoformat()
    ref.update(fields)
    summary_service.invalidate_cache()
    return _to_item(ref.get())


def delete_data(data_id: str) -> bool:
    ref = get_db().collection(COLLECTION).document(data_id)
    if not ref.get().exists:
        return False
    ref.delete()
    summary_service.invalidate_cache()
    return True
