from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))


def now_iso() -> str:
    """한국 시간 ISO 문자열 (예: 2026-11-17T23:10:00+09:00)"""
    return datetime.now(KST).isoformat(timespec="seconds")
