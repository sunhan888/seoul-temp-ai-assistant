"""
[STEP 3] 정제된 CSV(365개)를 Firestore 'data' 컬렉션에 한 번에 올립니다.
문서 ID를 날짜로 써서, 여러 번 실행해도 중복되지 않고 덮어씁니다.

실행 (backend 폴더, .env 설정 후):
    python scripts/seed_data.py
"""
import csv
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))  # app 패키지를 import할 수 있게

from app.firebase import get_db  # noqa: E402
from app.utils import now_iso    # noqa: E402

CSV_PATH = BASE / "data" / "seoul_temp_2025.csv"


def main():
    db = get_db()
    col = db.collection("data")
    with open(CSV_PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    batch, n = db.batch(), 0
    for r in rows:
        batch.set(col.document(r["date"]), {
            "date": r["date"],
            "value": float(r["value"]),
            "memo": f"최저 {r['min']}℃ / 최고 {r['max']}℃",
            "created_at": now_iso(),
        })
        n += 1
        if n % 400 == 0:          # Firestore 배치는 한 번에 최대 500개
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"✅ Firestore 'data' 컬렉션에 {n}개 업로드 완료")


if __name__ == "__main__":
    main()
