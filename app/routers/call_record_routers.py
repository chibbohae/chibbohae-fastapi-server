# from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
# import os
# import boto3
# import uuid
# from pydub import AudioSegment
# from io import BytesIO
# from app.dependencies.db import get_db
# from app.models.call_models import CallRecords
# from sqlalchemy.orm import Session
# from dotenv import load_dotenv

# load_dotenv()

# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# S3_REGION = os.getenv("S3_REGION")
# S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
# S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")

# s3_client = boto3.client(
#     "s3",
#     region_name=S3_REGION,
#     aws_access_key_id=S3_ACCESS_KEY,
#     aws_secret_access_key=S3_SECRET_KEY,
# )

# router = APIRouter(prefix="/call/record")

# # 지원하는 오디오 확장자자 리스트
# SUPPORTED_AUDIO_FORMATS = ["wav", "webm", "mp3", "ogg", "m4a"]


# @router.post("/upload")
# async def upload_audio(
#     file: UploadFile = File(...),
#     call_id: str = "",
#     user_id: str = "",
#     db: Session = Depends(get_db),
# ):
#     try:
#         # 파일 확장자 검사
#         file_extension = file.filename.split(".")[-1].lower()
#         if file_extension not in SUPPORTED_AUDIO_FORMATS:
#             raise HTTPException(
#                 status_code=400, detail=f"지원되지 않는 파일 형식 ({file_extension})"
#             )

#         # 업로드된 파일을 메모리에서 읽기
#         file_bytes = await file.read()
#         audio = AudioSegment.from_file(BytesIO(file_bytes), format=file_extension)

#         # FLAC 변환 (샘플링 레이트 통일)
#         flac_buffer = BytesIO()
#         audio.export(flac_buffer, format="flac")
#         flac_buffer.seek(0)

#         # S3에 업로드할 파일 경로 설정 (user_id 포함)
#         flac_filename = f"recordings/{call_id}_{user_id}_{uuid.uuid4().hex}.flac"

#         # S3에 업로드
#         s3_client.upload_fileobj(
#             flac_buffer,
#             S3_BUCKET_NAME,
#             flac_filename,
#             ExtraArgs={"ContentType": "audio/flac"},
#         )

#         # S3 파일 URL 생성
#         s3_file_url = (
#             f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{flac_filename}"
#         )

#         # DB에 녹음 파일 경로 저장
#         call_record = (
#             db.query(CallRecords).filter(CallRecords.call_id == call_id).first()
#         )
#         if call_record:
#             if call_record.recording_path:
#                 call_record.recording_path += f",{s3_file_url}"
#             else:
#                 call_record.recording_path = s3_file_url
#             db.commit()

#         return {"message": "녹음 파일 업로드 성공", "file_url": s3_file_url}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"오디오 업로드 실패: {str(e)}")
