from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
import os
from datetime import datetime, timezone, timedelta
from app.dependencies.db import get_db
from app.models.call_models import CallRecords
from app.dependencies.redis_manager import redis_client
from app.models.call_manager_models import (
    CallAnswerRequest,
    CallEndRequest,
    CallRequest,
    CallResponse,
)
import logging


router = APIRouter(prefix="/call")

# 오디오 파일 저장 경로
UPLOAD_DIR = "recordings"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# KST 타임존 설정
KST = timezone(timedelta(hours=9))


# 통화 요청 API
@router.post("/request", response_model=CallResponse)
def request_call(request: CallRequest, db: Session = Depends(get_db)) -> CallResponse:
    try:
        new_call = CallRecords(
            call_id=None, caller_id=request.caller_id, receiver_id=request.receiver_id
        )
        db.add(new_call)
        db.commit()
        return CallResponse(message="통화 요청됨")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"통화 요청 실패: {str(e)}")


# 통화 수락/거절 API
@router.post("/answer", response_model=CallResponse)
def answer_call(
    request: CallAnswerRequest, db: Session = Depends(get_db)
) -> CallResponse:
    try:
        call = (
            db.query(CallRecords)
            .filter(
                CallRecords.caller_id == request.caller_id,
                CallRecords.receiver_id == request.receiver_id,
            )
            .first()
        )

        if not call:
            raise HTTPException(status_code=404, detail="통화 요청을 찾을 수 없음")

        if not request.accepted:
            call.end_time = None
            call.start_time = None
            call.call_id = None
            db.commit()
            return CallResponse(message="통화 거절됨")

        # ✅ 통화 수락 시 UUID 생성 및 KST 시간 기록
        call.call_id = str(uuid.uuid4())
        call.start_time = datetime.now(timezone.utc).astimezone(KST)

        db.commit()
        db.refresh(call)

        # ✅ Redis에 call_id 저장 (1시간 후 자동 만료)

        try:
            redis_client.setex(
                f"accept:{call.caller_id}:{call.receiver_id}", 3600, call.call_id
            )
            logging.info(f"✅ Redis에 call_id 저장 완료: {call.call_id}")
        except Exception as e:
            logging.error(f"🚨 Redis 저장 실패: {e}")

        return CallResponse(message="통화 수락됨", call_id=call.call_id)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"통화 수락/거절 처리 실패: {str(e)}"
        )


# 통화 종료 API
@router.post("/end", response_model=CallResponse)
def end_call(request: CallEndRequest, db: Session = Depends(get_db)) -> CallResponse:
    try:
        call = (
            db.query(CallRecords).filter(CallRecords.call_id == request.call_id).first()
        )
        if not call:
            raise HTTPException(status_code=404, detail="통화 기록을 찾을 수 없음")

        call.end_time = datetime.now(timezone.utc).astimezone(KST)
        db.commit()

        # ✅ Redis에서 call_id 삭제
        redis_client.delete(f"accept:{call.caller_id}:{call.receiver_id}")

        return CallResponse(message="통화 종료됨", call_id=call.call_id)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"통화 종료 실패: {str(e)}")
