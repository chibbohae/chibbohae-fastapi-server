from pydantic import BaseModel


# 요청 및 응답 모델 정의
class CallRequest(BaseModel):
    caller_id: str
    receiver_id: str


class CallAnswerRequest(BaseModel):
    caller_id: str
    receiver_id: str
    accepted: bool


class CallEndRequest(BaseModel):
    call_id: str


class AudioUploadRequest(BaseModel):
    call_id: str


class CallResponse(BaseModel):
    message: str
    call_id: str | None = None


class AudioUploadResponse(BaseModel):
    message: str
    file_path: str
