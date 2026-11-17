"""
라우터 = '접수 창구'. 어떤 주소(URL)로 들어온 요청을 어떤 서비스 함수에 넘길지만 정합니다.
실제 일(DB 읽기/쓰기, 계산)은 services/ 에서 합니다.
"""
from fastapi import APIRouter, HTTPException

from app.schemas import DataCreate, DataItem, DataUpdate, Summary
from app.services import data_service, summary_service

router = APIRouter(prefix="/api/data", tags=["데이터"])


# /summary 를 /{data_id} 보다 먼저 선언 (주소 충돌 방지)
@router.get("/summary", response_model=Summary, summary="데이터 요약 (프롬프트 주입용)")
def get_summary():
    return summary_service.get_summary()


@router.get("", response_model=list[DataItem], summary="데이터 목록 조회 (날짜순)")
def list_data():
    return data_service.list_data()


@router.post("", response_model=DataItem, status_code=201, summary="새 데이터 추가")
def create_data(item: DataCreate):
    return data_service.create_data(item)


@router.put("/{data_id}", response_model=DataItem, summary="데이터 수정")
def update_data(data_id: str, patch: DataUpdate):
    updated = data_service.update_data(data_id, patch)
    if updated is None:
        raise HTTPException(404, "해당 데이터를 찾을 수 없습니다.")
    return updated


@router.delete("/{data_id}", summary="데이터 삭제")
def delete_data(data_id: str):
    if not data_service.delete_data(data_id):
        raise HTTPException(404, "해당 데이터를 찾을 수 없습니다.")
    return {"deleted": data_id}
