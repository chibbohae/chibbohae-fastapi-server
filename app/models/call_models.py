from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone, timedelta

Base = declarative_base()


class CallRecords(Base):
    __tablename__ = "call_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    call_id = Column(String(50), nullable=True)  # UUID 형태
    caller_id = Column(String(50), nullable=False)
    receiver_id = Column(String(50), nullable=False)
    start_time = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).astimezone(
            timezone(timedelta(hours=9))
        ),
        nullable=True,
    )
    end_time = Column(DateTime, nullable=True)
    recording_path = Column(Text, nullable=True)
