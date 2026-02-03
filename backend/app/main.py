from datetime import datetime, date
from typing import List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlmodel import Session, select
import redis

from .settings import settings
from .db import init_db, get_session, engine
from .models import User, Camera, VisitEvent, DailySummary
from .auth import hash_password, verify_password, create_access_token, get_user_by_username, require_role

app = FastAPI(title="Visitor Monitoring API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rds = redis.Redis.from_url(settings.redis_url, decode_responses=True)

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"

class UserOut(BaseModel):
    id: int
    username: str
    role: str

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    roi: Optional[Any] = None
    line: Optional[Any] = None

class CameraOut(BaseModel):
    id: int
    name: str
    rtsp_url: Optional[str] = None
    roi: Optional[Any] = None
    line: Optional[Any] = None

class EventIn(BaseModel):
    camera_id: int
    ts: datetime
    count_in: int = 0
    count_out: int = 0
    track_ids: Optional[List[str]] = None

class DailyOut(BaseModel):
    day: date
    camera_id: int
    total_in: int
    total_out: int
    unique_estimate: int

@app.on_event("startup")
def on_startup():
    init_db()
    with Session(engine) as session:
        admin = get_user_by_username(session, settings.admin_username)
        if not admin:
            admin = User(
                username=settings.admin_username,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            )
            session.add(admin)
            session.commit()

        cam = session.exec(select(Camera).order_by(Camera.id)).first()
        if not cam:
            cam = Camera(
                name=settings.default_camera_name,
                rtsp_url=settings.default_camera_rtsp,
                roi=None,
                line=None,
            )
            session.add(cam)
            session.commit()

@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, session: Session = Depends(get_session)):
    user = get_user_by_username(session, payload.username)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username/password")
    return TokenOut(access_token=create_access_token(user.username))

@app.get("/api/me", response_model=UserOut)
def me(user: User = Depends(require_role("admin", "operator"))):
    return UserOut(id=user.id, username=user.username, role=user.role)

@app.post("/api/users", response_model=UserOut)
def create_user(payload: UserCreate, session: Session = Depends(get_session), _: User = Depends(require_role("admin"))):
    if get_user_by_username(session, payload.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    u = User(username=payload.username, password_hash=hash_password(payload.password), role=payload.role)
    session.add(u)
    session.commit()
    session.refresh(u)
    return UserOut(id=u.id, username=u.username, role=u.role)

@app.get("/api/users", response_model=List[UserOut])
def list_users(session: Session = Depends(get_session), _: User = Depends(require_role("admin"))):
    users = session.exec(select(User)).all()
    return [UserOut(id=u.id, username=u.username, role=u.role) for u in users]

@app.get("/api/cameras/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: int, session: Session = Depends(get_session), _: User = Depends(require_role("admin", "operator"))):
    cam = session.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraOut(id=cam.id, name=cam.name, rtsp_url=cam.rtsp_url, roi=cam.roi, line=cam.line)

@app.put("/api/cameras/{camera_id}", response_model=CameraOut)
def update_camera(camera_id: int, payload: CameraUpdate, session: Session = Depends(get_session), _: User = Depends(require_role("admin"))):
    cam = session.get(Camera, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(cam, k, v)
    session.add(cam)
    session.commit()
    session.refresh(cam)
    return CameraOut(id=cam.id, name=cam.name, rtsp_url=cam.rtsp_url, roi=cam.roi, line=cam.line)

@app.post("/api/events/ingest")
def ingest_event(payload: EventIn, session: Session = Depends(get_session)):
    ev = VisitEvent(camera_id=payload.camera_id, ts=payload.ts, count_in=payload.count_in, count_out=payload.count_out, track_ids=payload.track_ids)
    session.add(ev)

    d = payload.ts.date()
    summary = session.exec(select(DailySummary).where(DailySummary.camera_id == payload.camera_id, DailySummary.day == d)).first()
    if not summary:
        summary = DailySummary(camera_id=payload.camera_id, day=d, total_in=0, total_out=0, unique_estimate=0)
        session.add(summary)

    summary.total_in += int(payload.count_in or 0)
    summary.total_out += int(payload.count_out or 0)

    if payload.track_ids:
        key = f"uniq:{d.isoformat()}:{payload.camera_id}"
        rds.sadd(key, *payload.track_ids)
        summary.unique_estimate = int(rds.scard(key))

    session.commit()
    return {"ok": True}

@app.get("/api/stats/daily", response_model=List[DailyOut])
def stats_daily(day: Optional[date] = None, session: Session = Depends(get_session), _: User = Depends(require_role("admin", "operator"))):
    q = select(DailySummary)
    if day:
        q = q.where(DailySummary.day == day)
    rows = session.exec(q.order_by(DailySummary.day.desc())).all()
    return [DailyOut(day=r.day, camera_id=r.camera_id, total_in=r.total_in, total_out=r.total_out, unique_estimate=r.unique_estimate) for r in rows]

@app.get("/api/reports/csv")
def report_csv(from_day: date, to_day: date, session: Session = Depends(get_session), _: User = Depends(require_role("admin", "operator"))):
    import io, csv
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["day", "camera_id", "total_in", "total_out", "unique_estimate"])
    rows = session.exec(select(DailySummary).where(DailySummary.day >= from_day, DailySummary.day <= to_day).order_by(DailySummary.day)).all()
    for r in rows:
        writer.writerow([r.day.isoformat(), r.camera_id, r.total_in, r.total_out, r.unique_estimate])
    return {"filename": f"report_{from_day}_{to_day}.csv", "csv": out.getvalue()}
