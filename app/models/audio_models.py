from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.dependencies.db import Base

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), index=True) # 같은 통화그룹을 구분하는 ID
    user_id = Column(String(255), index=True)
    filename = Column(String(255), index=True)
    file_path = Column(String(255), index=True)
    upload_time = Column(DateTime, server_default=func.now())