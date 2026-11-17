# 🌙 오늘 밤 실행 가이드 — 서울 기온 AI 비서

> 코드는 이미 다 짜여 있고 동작 테스트도 끝났습니다.
> 한선 님이 할 일: **① 계정·키 준비 → ② 내 컴퓨터에서 실행 → ③ 배포 → ④ 스크린샷**
> 각 단계마다 "이게 무슨 개념인지"를 먼저 읽고 → 실행 → ✅ 확인 순서로 진행하세요.
> 예상 시간: 약 2시간 30분

---

## 🗺️ 전체 그림 먼저 (식당 비유)

```
 손님(브라우저)          홀 직원(프론트엔드)         주방(백엔드 FastAPI)        창고(Firestore)
 "가장 더운 날?"  ──▶  Vercel에 있는 화면  ──fetch──▶  Render에 있는 서버   ──▶  data / conversations
                                                          │
                                                          ▼
                                                    외부 셰프(GPT)
                                       "이 메모(요약) 보고 답해줘" ← 컨텍스트 주입
```

- **프론트엔드(Vercel)**: 손님이 보는 화면. 주문을 받아 주방에 전달만 함
- **백엔드(Render)**: 주문을 처리하는 주방. 창고에서 재료(데이터)를 꺼내고, 셰프(GPT)에게 요리를 부탁
- **Firestore**: 창고. 서버가 꺼져도 데이터가 남아 있음
- **GPT**: 실력은 좋지만 우리 창고를 모르는 외부 셰프 → 그래서 **요약 메모를 같이 건네줌** (= 컨텍스트 주입)

---

## STEP 0. 계정·키 준비 (30분) 🔑

### 0-1. Firebase (창고 만들기)
1. https://console.firebase.google.com → **프로젝트 추가** → 이름 `seoul-temp-ai` → (애널리틱스는 꺼도 됨)
2. 왼쪽 메뉴 **빌드 → Firestore Database → 데이터베이스 만들기**
   - 위치: `asia-northeast3 (서울)` / 모드: **프로덕션 모드**
3. 왼쪽 위 ⚙️ **프로젝트 설정 → 서비스 계정 탭 → 새 비공개 키 생성** → JSON 파일 다운로드
4. 다운로드한 파일 이름을 `serviceAccountKey.json` 으로 바꿔 `backend/` 폴더에 넣기

> 💡 **서비스 계정 키 = 창고 마스터키.** 이 파일만 있으면 누구나 내 DB를 읽고 지울 수 있어요.
> 그래서 코드에 쓰지 않고, GitHub에도 절대 올리지 않습니다(`.gitignore`에 등록됨).

### 0-2. OpenAI (셰프 고용)
1. https://platform.openai.com → **Settings → Billing** 에서 크레딧 충전(최소 $5)
2. **API keys → Create new secret key** → `sk-...` 복사 (한 번만 보여줌!)
3. (권장) **Limits** 에서 월 사용 한도를 $5 정도로 설정 → 과금 사고 방지

### 0-3. Render, Vercel
- https://render.com , https://vercel.com 에 **GitHub 계정으로 로그인**만 해 두기

✅ 확인: `backend/serviceAccountKey.json` 파일이 있고, `sk-...` 키를 메모장에 복사해 둠

---

## STEP 1. 데이터 이해하기 (10분) 📈

지난 미션의 **서울 기온 CSV(2016~2025)**를 재사용합니다. 이번엔 그중 **2025년 365일**만 씁니다.

```bash
cd backend
python scripts/prepare_data.py
# ✅ 365개 데이터 포인트 저장 → seoul_temp_2025.csv
```

> 💡 **왜 1년치만?** Firestore 무료 한도는 하루 읽기 5만 건이에요. 10년치(3,650개)를 쓰면
> 목록 한 번 볼 때마다 3,650건씩 읽혀서 금방 바닥나요. 미션 조건(100개 이상)도 충분히 만족합니다.

**요약 정보(`/api/data/summary`)는 이렇게 생겼어요** — AI에게 줄 "한 장짜리 브리핑 메모":

```json
{
  "period": "2025-01-01 ~ 2025-12-31",
  "count": 365,
  "metrics": { "average": 14.2, "max": 32.8, "max_date": "2025-07-27", "min": -9.7, "min_date": "2025-01-09" },
  "trend": "하강 (최근 30일 평균 1.1℃, 직전 30일 대비 -7.6℃)",
  "monthly_avg": { "2025-01": -0.4, ..., "2025-07": 28.8, ... },
  "recent": [ 최근 7일 ]
}
```

- **추세 계산법**: 최근 30일 평균 vs 그 직전 30일 평균. 0.5℃ 넘게 오르면 상승, 내리면 하강, 아니면 유지
- 코드: `backend/app/services/summary_service.py`

---

## STEP 2. 내 컴퓨터에서 백엔드 켜기 (20분) 🍳

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Windows: copy .env.example .env
```

`.env` 파일을 열어 `OPENAI_API_KEY=sk-...` 에 진짜 키를 붙여넣기 (나머지는 그대로)

> 💡 **가상환경(venv) = 프로젝트 전용 공구함.** 이 프로젝트에 필요한 패키지만 따로 담아,
> 다른 프로젝트와 버전이 섞이지 않게 합니다.
> 💡 **.env = 금고.** `config.py`가 실행될 때 이 금고에서 키를 꺼내 씁니다.

---

## STEP 3. 창고에 데이터 넣기 (10분) 📦

```bash
python scripts/seed_data.py
# ✅ Firestore 'data' 컬렉션에 365개 업로드 완료
```

✅ 확인: Firebase 콘솔 → Firestore Database 에 `data` 컬렉션과 `2025-01-01` 같은 문서들이 보임

> 💡 **컬렉션 = 서랍, 문서 = 서랍 속 카드 한 장.**
> `data` 서랍에는 하루치 기온 카드 365장, `conversations` 서랍에는 대화 카드가 들어갑니다.
> (`conversations`는 첫 채팅을 하면 자동으로 생겨요)

---

## STEP 4. Swagger로 API 직접 눌러보기 (20분) 🧪

```bash
uvicorn main:app --reload
```
브라우저에서 **http://127.0.0.1:8000/docs** 열기

순서대로 **Try it out → Execute** 해 보세요:

| 순서 | 해볼 것 | 기대 결과 |
|---|---|---|
| 1 | `GET /api/data/summary` | 위의 요약 JSON |
| 2 | `POST /api/data` 에 `{"date":"2026-01-01","value":-3.2,"memo":"테스트"}` | 201 + id 발급 |
| 3 | 같은 요청에 `"value": 999` | **422** ← Pydantic이 막음 |
| 4 | `PUT /api/data/{2번 id}` 에 `{"value": 1.5}` | 200, 값 변경 |
| 5 | `DELETE /api/data/{2번 id}` | 200 / 한 번 더 하면 **404** |
| 6 | `POST /api/chat` 에 `{"message":"가장 더웠던 날은?"}` | GPT 답변 + `conversation_id` |
| 7 | `GET /api/conversations` → `GET /api/conversations/{id}` | 목록 / 전체 메시지 |

> 💡 **Pydantic = 입국 심사대.** `schemas.py`에 "value는 -60~60 사이 숫자" 같은 규칙을 적어 두면,
> 규칙을 어긴 요청은 함수에 들어오기도 전에 422로 돌려보내요. 그래서 DB에 이상한 값이 쌓이지 않습니다.
>
> 💡 **라우터 vs 서비스 = 접수 창구 vs 주방.**
> `routers/`는 "이 주소로 온 요청은 이 함수로" + "없으면 404" 만,
> `services/`는 DB 읽기·쓰기, 통계 계산, GPT 호출 같은 실제 일만 합니다.
> 그래서 채팅 서비스가 요약을 쓸 때 HTTP를 거치지 않고 `summary_service.get_summary()`를 바로 재사용할 수 있어요.

---

## STEP 5. 화면 켜고 써보기 (15분) 🖥️

백엔드는 켜 둔 채로 **새 터미널**:
```bash
cd frontend
python -m http.server 5500
```
**http://127.0.0.1:5500** 열기 → 오른쪽 위 "서버 연결됨" 초록 배지 확인

- 채팅: "2025년에 가장 더웠던 날은?", "7월과 1월 평균기온 차이는?", "12월 추세는 어때?"
- 데이터 관리 탭: 추가 → 수정 → 삭제 (왼쪽 요약의 개수가 바뀌는지 보기)
- 대화 기록: "+ 새 대화" → 다른 질문 → 왼쪽 목록에서 이전 대화 클릭하면 다시 불러와짐

> 💡 **컨텍스트 주입의 핵심 코드**는 `backend/app/services/chat_service.py` 의 `SYSTEM_TEMPLATE`.
> GPT는 매번 기억이 없는 상태로 호출돼요. 그래서 **질문할 때마다** 요약 메모를 시스템 프롬프트에 끼워
> "너는 이 데이터를 아는 비서야"라고 다시 알려주는 거예요.
> 데이터를 수정하면 요약이 바뀌고 → 다음 답변도 바뀝니다. (직접 확인해 보세요!)

---

## STEP 6. GitHub에 올리기 (10분) 🐙

GitHub에서 새 저장소 `seoul-temp-ai-assistant` 생성 (README 체크 해제) 후, 프로젝트 최상위 폴더에서:

```bash
git init
git add .
git status        # ⚠️ .env 와 serviceAccountKey.json 이 목록에 "없는지" 꼭 확인!
git commit -m "서울 기온 AI 비서: FastAPI + Firestore + GPT + 바닐라 프론트"
git branch -M main
git remote add origin https://github.com/sunhan888/seoul-temp-ai-assistant.git
git push -u origin main
```

---

## STEP 7. 백엔드 배포 — Render (20분) 🚀

1. Render 대시보드 → **New + → Web Service** → 방금 만든 저장소 선택
2. 설정:

| 항목 | 값 |
|---|---|
| Root Directory | `backend` |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

3. **Environment Variables** 추가:

| Key | Value |
|---|---|
| `OPENAI_API_KEY` | `sk-...` |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | `serviceAccountKey.json` 파일을 메모장으로 열어 **내용 전체** 복사·붙여넣기 |
| `ALLOWED_ORIGINS` | 일단 `http://127.0.0.1:5500` (Vercel 주소는 STEP 8 후 추가) |

4. **Deploy** → 3~5분 기다리기 → `https://xxxx.onrender.com/docs` 열어서 Swagger 보이면 성공 ✅

> 💡 **왜 로컬은 파일 경로, Render는 JSON 내용?** Render 서버에는 내 컴퓨터의 키 파일이 없어요
> (GitHub에도 안 올렸으니까). 그래서 파일 내용 자체를 환경 변수 금고에 넣어 둡니다.
> `firebase.py`가 두 방식을 모두 받아들이도록 짜여 있어요.
>
> 💡 **콜드스타트**: 무료 서버는 15분 동안 손님이 없으면 잠들어요. 다음 손님이 오면 깨어나는 데 30~60초.
> 그래서 화면은 시작할 때 `/health`를 먼저 부르고, 3초 넘게 걸리면 "서버가 깨는 중" 안내를 띄웁니다.

---

## STEP 8. 프론트엔드 배포 — Vercel (15분) 🌐

1. Vercel → **Add New → Project** → 같은 저장소 Import
2. 설정:

| 항목 | 값 |
|---|---|
| Root Directory | `frontend` (Edit 눌러서 선택) |
| Framework Preset | Other |
| Environment Variables | `API_BASE_URL` = `https://xxxx.onrender.com` (끝에 `/` 없이) |

3. **Deploy** → `https://xxxx.vercel.app` 주소 복사

> 💡 **HTML 파일은 환경 변수를 못 읽어요.** 그래서 `build.js`가 배포할 때
> `API_BASE_URL` 값을 `config.js` 파일로 "구워서" 넣어 줍니다. (`vercel.json`이 이 빌드를 실행하라고 지시)

### 8-1. CORS 마무리 (5분) ⚠️ 가장 많이 막히는 곳
Render → Environment → `ALLOWED_ORIGINS` 를 다음처럼 수정 → 저장(자동 재배포):
```
https://xxxx.vercel.app,http://127.0.0.1:5500
```

> 💡 **CORS = 아파트 출입 명단.** 브라우저는 보안상 "다른 주소(vercel.app)의 화면이
> 남의 서버(onrender.com)에 요청하는 것"을 기본적으로 막아요. 서버가 "vercel.app은 우리 손님이야"라고
> 명단에 올려 줘야 통과됩니다. 이걸 빠뜨리면 화면에 "서버 연결 실패"가 떠요.
> (주소 끝에 `/`를 붙이지 마세요)

✅ 확인: Vercel 주소에서 채팅 → 답변 오면 완성!

---

## STEP 9. 스크린샷 + README 마무리 (20분) 📸

1. 배포된 화면에서 스크린샷 3장 찍어 `docs/screenshots/` 폴더에 저장:
   - `01_chat.png` — 왼쪽 요약 + 질문·답변이 보이는 채팅 화면
   - `02_data.png` — 데이터 추가(또는 수정) 직후 "✅ 추가 완료" 메시지가 보이는 화면
   - `03_history.png` — 대화 기록에서 이전 대화를 클릭해 불러온 화면
2. `README.md`의 `YOUR-APP`, `YOUR-API` 를 실제 주소로 바꾸기
3. 올리기:
```bash
git add .
git commit -m "README 배포 URL, 스크린샷 추가"
git push
```

---

## 🎓 마지막 셀프 체크 — 이 6가지를 내 말로 설명할 수 있나요?

| # | 질문 | 힌트 (어디를 보면 되나) |
|---|---|---|
| 1 | 시계열 데이터를 어떻게 요약해서 서비스에 썼나? | `summary_service.py` — 기간/개수/통계/30일 추세/월평균 → 프롬프트 |
| 2 | 라우터와 서비스는 왜 나눴나? | 창구(URL·상태코드) vs 주방(DB·계산·GPT). 재사용·수정이 쉬움 |
| 3 | Pydantic으로 무엇을, 왜 검증했나? | `schemas.py` — 날짜 형식, 기온 범위, 글자 수. 이상한 값이 DB에 들어가지 않게 |
| 4 | Firestore에 어떻게 저장하고 CRUD했나? | `data_service.py` — `collection().document().set/get/update/delete` |
| 5 | 컨텍스트 주입이란? | GPT는 내 데이터를 모름 → 매 질문마다 요약을 시스템 프롬프트에 넣어줌 |
| 6 | 배포에서 CORS/환경변수/키 관리가 왜 필요한가? | CORS=출입명단, 환경변수=금고. 키가 GitHub에 올라가면 누구나 내 돈·DB를 씀 |

## 🆘 막힐 때

| 증상 | 원인 / 해결 |
|---|---|
| 화면에 "서버 연결 실패" | ① Render 주소가 맞는지 ② `ALLOWED_ORIGINS`에 Vercel 주소가 있는지(끝 `/` 없이) ③ 콜드스타트면 1분 후 새로고침 |
| 채팅 시 `502 AI 응답 생성에 실패` | OpenAI 키 오타 또는 크레딧 없음 (Billing 확인) |
| `500 Firebase 키가 없습니다` | `.env`(로컬) 또는 Render 환경 변수에 Firebase 키 누락 |
| Render 빌드 실패 | Root Directory가 `backend`인지 확인 |
| 요약이 "데이터 없음" | STEP 3 `seed_data.py`를 실행했는지 확인 |
