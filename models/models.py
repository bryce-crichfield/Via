from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DrivingSession(Base):
    __tablename__ = "driving_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    engine_readings = relationship(
        "EngineReading", back_populates="session", cascade="all, delete-orphan"
    )
    gps_readings = relationship(
        "GpsReading", back_populates="session", cascade="all, delete-orphan"
    )


class EngineReading(Base):
    __tablename__ = "engine_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("driving_sessions.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    rpm = Column(Float, nullable=True)
    speed_kph = Column(Float, nullable=True)
    coolant_temp_c = Column(Float, nullable=True)
    throttle_pct = Column(Float, nullable=True)
    engine_load_pct = Column(Float, nullable=True)

    session = relationship("DrivingSession", back_populates="engine_readings")


class GpsReading(Base):
    __tablename__ = "gps_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("driving_sessions.id"), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy_m = Column(Float, nullable=True)

    session = relationship("DrivingSession", back_populates="gps_readings")
