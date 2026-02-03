from typing import Optional, List, Any
from datetime import datetime, date
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON, UniqueConstraint

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    role: str = Field(default="operator")  # admin | operator

class Camera(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    rtsp_url: Optional[str] = None
    roi: Optional[Any] = Field(default=None, sa_column=Column(JSON))  # polygon points
    line: Optional[Any] = Field(default=None, sa_column=Column(JSON)) # line crossing config

class VisitEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: int = Field(index=True, foreign_key="camera.id")
    ts: datetime = Field(index=True)
    count_in: int = 0
    count_out: int = 0
    track_ids: Optional[Any] = Field(default=None, sa_column=Column(JSON))

class DailySummary(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("camera_id", "day", name="uq_camera_day"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: int = Field(index=True, foreign_key="camera.id")
    day: date = Field(index=True)

    total_in: int = 0
    total_out: int = 0
    unique_estimate: int = 0
