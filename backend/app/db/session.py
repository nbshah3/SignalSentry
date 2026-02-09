from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}


def _ensure_sqlite_dir() -> None:
    if not settings.database_url.startswith("sqlite"):
        return
    parsed = urlparse(settings.database_url)
    path = parsed.path
    if path.startswith("//"):
        file_path = Path(path[1:])
    else:
        file_path = Path(path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    file_path.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir()

engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Iterator[Session]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
