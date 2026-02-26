import time
import os
from typing import Optional

from sqlalchemy import event
from sqlmodel import Field, Session, SQLModel, create_engine, col, select, delete

DB_PATH = os.getenv("DB_PATH", "/app/data/travel.db")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Settings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    origin: str = ""
    destination: str = ""
    active: bool = False
    mode: str = "travel_time"           # "travel_time" | "arrive_time"
    alert_threshold_minutes: Optional[int] = None
    arrive_by: Optional[int] = None     # unix timestamp
    buffer_minutes: Optional[int] = None


class CheckLog(SQLModel, table=True):
    __tablename__ = "check_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    checked_at: int                     # unix timestamp
    travel_minutes: float
    alerted: bool = False


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine = create_engine(f"sqlite:///{DB_PATH}")


@event.listens_for(engine, "connect")
def _set_wal_mode(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.get(Settings, 1):
            session.add(Settings(id=1))
            session.commit()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_settings() -> Settings | None:
    with Session(engine) as session:
        return session.get(Settings, 1)


def upsert_settings(data: dict) -> Settings:
    with Session(engine) as session:
        settings = session.get(Settings, 1) or Settings(id=1)
        for key, value in data.items():
            if hasattr(settings, key) and key != "id":
                setattr(settings, key, value)
        session.add(settings)
        session.commit()
        session.refresh(settings)
        return settings


# ---------------------------------------------------------------------------
# Check log
# ---------------------------------------------------------------------------

def append_check_log(travel_minutes: float, alerted: bool) -> None:
    with Session(engine) as session:
        session.add(CheckLog(
            checked_at=int(time.time()),
            travel_minutes=travel_minutes,
            alerted=alerted,
        ))
        session.commit()


def get_check_log(limit: int = 20) -> list[CheckLog]:
    with Session(engine) as session:
        return session.exec(
            select(CheckLog)
            .order_by(col(CheckLog.checked_at).desc())
            .limit(limit)
        ).all()


def clear_check_log() -> None:
    with Session(engine) as session:
        session.exec(delete(CheckLog))
        session.commit()
