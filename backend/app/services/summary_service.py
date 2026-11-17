"""
데이터 요약 = AI에게 건네줄 '한 장짜리 브리핑 메모'
365개 숫자를 통째로 주는 대신, 기간·개수·통계·추세만 뽑아서 줍니다.

[캐시] Firestore 무료 한도(하루 읽기 5만 건)를 아끼기 위해
요약을 한 번 계산하면 기억해 두고, 데이터가 바뀔 때만 다시 계산합니다.
"""
from statistics import mean

_cache: dict | None = None


def invalidate_cache():
    global _cache
    _cache = None


def get_summary() -> dict:
    global _cache
    if _cache is None:
        from app.services import data_service  # 순환 import 방지용 지연 import
        _cache = build_summary(data_service.list_data())
    return _cache


def _trend(values: list[float]) -> str:
    """최근 30일 평균 vs 직전 30일 평균 비교 (데이터가 적으면 반으로 나눠 비교)"""
    if len(values) < 2:
        return "판단 불가 (데이터 부족)"
    n = 30 if len(values) >= 60 else len(values) // 2
    recent, before = mean(values[-n:]), mean(values[-2 * n:-n])
    diff = recent - before
    if diff > 0.5:
        word = "상승"
    elif diff < -0.5:
        word = "하강"
    else:
        word = "유지"
    return f"{word} (최근 {n}일 평균 {recent:.1f}℃, 직전 {n}일 대비 {diff:+.1f}℃)"


def build_summary(rows: list[dict]) -> dict:
    if not rows:
        return {"period": "데이터 없음", "count": 0, "metrics": {}, "trend": "판단 불가 (데이터 없음)",
                "latest_date": None, "monthly_avg": {}, "recent": []}

    rows = sorted(rows, key=lambda r: r["date"])
    values = [r["value"] for r in rows]
    hottest = max(rows, key=lambda r: r["value"])
    coldest = min(rows, key=lambda r: r["value"])

    # 월별 평균: {"2025-01": -1.2, ...}
    by_month: dict[str, list[float]] = {}
    for r in rows:
        by_month.setdefault(r["date"][:7], []).append(r["value"])
    monthly_avg = {m: round(mean(v), 1) for m, v in by_month.items()}

    return {
        "period": f"{rows[0]['date']} ~ {rows[-1]['date']}",
        "count": len(rows),
        "metrics": {
            "average": round(mean(values), 1),
            "max": hottest["value"], "max_date": hottest["date"],
            "min": coldest["value"], "min_date": coldest["date"],
        },
        "trend": _trend(values),
        "latest_date": rows[-1]["date"],
        "monthly_avg": monthly_avg,
        "recent": [{"date": r["date"], "value": r["value"]} for r in rows[-7:]],
    }
