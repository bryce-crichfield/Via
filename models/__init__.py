import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

import config
from .models import Base, DrivingSession, EngineReading, GpsReading

logger = logging.getLogger(__name__)

_engine = create_engine(config.DATABASE_URL, echo=False)
SessionLocal: scoped_session = scoped_session(sessionmaker(bind=_engine))


def init_db() -> None:
    """Create all tables if they do not exist."""
    Base.metadata.create_all(_engine)
    logger.info("Database initialised at %s", config.DATABASE_URL)


__all__ = [
    "init_db",
    "SessionLocal",
    "DrivingSession",
    "EngineReading",
    "GpsReading",
]
