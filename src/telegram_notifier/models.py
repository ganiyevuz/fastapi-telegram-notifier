from __future__ import annotations

from sqlalchemy import (
    JSON as SAJson,
)
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class ExceptionLog(Base):
    __tablename__ = "exception_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    exception_class = Column(String(255), index=True)
    message = Column(Text)
    traceback = Column(Text)
    level = Column(String(10), default="error")
    severity = Column(String(10), default="high")
    status = Column(String(10), default="new", index=True)
    path = Column(String(500), default="")
    method = Column(String(10), default="")
    query_params = Column(SAJson, default=dict)
    body = Column(Text, default="")
    user_info = Column(String(255), default="")
    ip_address = Column(String(45), default="")
    headers = Column(SAJson, default=dict)
    hostname = Column(String(255), default="")
    environment = Column(String(50), default="")
    is_sent = Column(Boolean, default=False)
    created_at = Column(
        DateTime, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return (
            f"<ExceptionLog(id={self.id}, "
            f"exception_class={self.exception_class!r})>"
        )
