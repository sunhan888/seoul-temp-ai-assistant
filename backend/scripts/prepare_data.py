"""
[STEP 1] 기상청 원본 CSV → 서비스용 깔끔한 CSV로 변환

원본(seoul_temp_2016_2025.csv)은
  - 인코딩이 cp949(옛 한글 윈도우 방식)이고
  - 위쪽 7줄이 '검색조건' 설명이며
  - 날짜 앞에 탭(\t)이 붙어 있습니다.

이 스크립트는 그중 2025년 1년치(365일)만 골라
date,value,min,max 형태의 UTF-8 CSV로 저장합니다.
  - date  : 날짜 (YYYY-MM-DD)
  - value : 일 평균기온(℃)  ← 미션의 value
  - min/max : 최저/최고기온 → Firestore에 올릴 때 memo로 들어감

실행 (backend 폴더에서):
    python scripts/prepare_data.py
"""
import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "seoul_temp_2016_2025.csv"
DST = BASE / "data" / "seoul_temp_2025.csv"
YEAR = "2025"


def main():
    rows = []
    with open(SRC, encoding="cp949") as f:
        for line in csv.reader(f):
            if len(line) < 5:
                continue                      # 설명 줄, 빈 줄 건너뛰기
            date = line[0].strip()            # '\t2016-01-01' → '2016-01-01'
            if not date.startswith(YEAR):
                continue                      # 헤더 줄과 다른 연도 건너뛰기
            avg, tmin, tmax = line[2], line[3], line[4]
            if avg == "":
                continue                      # 결측치(빈 값) 건너뛰기
            rows.append([date, avg, tmin, tmax])

    with open(DST, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "value", "min", "max"])
        w.writerows(rows)

    print(f"✅ {len(rows)}개 데이터 포인트 저장 → {DST.name}")
    print(f"   기간: {rows[0][0]} ~ {rows[-1][0]}")


if __name__ == "__main__":
    main()
