import time
import os
from typing import Optional

from sqlalchemy import event
from sqlmodel import Field, Session, SQLModel, create_engine, col, select, delete

DB_PATH = os.getenv("DB_PATH", "/app/data/travel.db")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Monitor(SQLModel, table=True):
    __tablename__ = "monitors"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = ""
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
    monitor_id: int = Field(foreign_key="monitors.id")
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


# ---------------------------------------------------------------------------
# Monitors
# ---------------------------------------------------------------------------

def get_all_monitors() -> list[Monitor]:
    with Session(engine) as session:
        return session.exec(select(Monitor)).all()


def get_monitor(id: int) -> Monitor | None:
    with Session(engine) as session:
        return session.get(Monitor, id)


def create_monitor(data: dict) -> Monitor:
    with Session(engine) as session:
        monitor = Monitor(**{k: v for k, v in data.items() if hasattr(Monitor, k)})
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        return monitor


def update_monitor(id: int, data: dict) -> Monitor | None:
    with Session(engine) as session:
        monitor = session.get(Monitor, id)
        if not monitor:
            return None
        for key, value in data.items():
            if hasattr(monitor, key) and key != "id":
                setattr(monitor, key, value)
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        return monitor


def delete_monitor(id: int) -> bool:
    with Session(engine) as session:
        monitor = session.get(Monitor, id)
        if not monitor:
            return False
        session.exec(delete(CheckLog).where(CheckLog.monitor_id == id))
        session.delete(monitor)
        session.commit()
        return True


# ---------------------------------------------------------------------------
# Check log
# ---------------------------------------------------------------------------

def append_check_log(monitor_id: int, travel_minutes: float, alerted: bool) -> None:
    with Session(engine) as session:
        session.add(CheckLog(
            monitor_id=monitor_id,
            checked_at=int(time.time()),
            travel_minutes=travel_minutes,
            alerted=alerted,
        ))
        session.commit()


def get_check_log(monitor_id: int, limit: int = 20) -> list[CheckLog]:
    with Session(engine) as session:
        return session.exec(
            select(CheckLog)
            .where(CheckLog.monitor_id == monitor_id)
            .order_by(col(CheckLog.checked_at).desc())
            .limit(limit)
        ).all()


def clear_check_log(monitor_id: int) -> None:
    with Session(engine) as session:
        session.exec(delete(CheckLog).where(CheckLog.monitor_id == monitor_id))
        session.commit()
