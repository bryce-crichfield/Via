import logging
import random
from datetime import datetime, timezone

from PyQt6.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot

import config
from models import GpsReading, SessionLocal

logger = logging.getLogger(__name__)


class NavigationController(QObject):
    """Controller for GPS navigation and map interaction."""

    gpsUpdated = pyqtSignal(float, float, float)  # lat, lon, accuracy

    def __init__(self, parent=None):
        super().__init__(parent)
        self._session_id: int | None = None

        # Simulated GPS state (replaced by real hardware when GPS_SIMULATE=false)
        self._current_latitude = 37.7749
        self._current_longitude = -122.4194
        self._current_accuracy = 15.0

        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._simulate_gps_update)
        self._update_timer.start(config.GPS_UPDATE_INTERVAL_MS)

    # ------------------------------------------------------------------
    # Session wiring
    # ------------------------------------------------------------------

    @pyqtSlot(int)
    def set_session_id(self, session_id: int) -> None:
        """Called by main when the engine controller opens or closes a session."""
        self._session_id = session_id if session_id >= 0 else None
        logger.debug("NavigationController session_id → %s", self._session_id)

    # ------------------------------------------------------------------
    # GPS
    # ------------------------------------------------------------------

    @pyqtSlot()
    def requestGPSUpdate(self):
        """Emit current GPS position to QML."""
        self.gpsUpdated.emit(
            self._current_latitude,
            self._current_longitude,
            self._current_accuracy,
        )

    def _simulate_gps_update(self):
        """Random-walk GPS simulation (used when GPS_SIMULATE=true)."""
        self._current_latitude += random.uniform(-0.0001, 0.0001)
        self._current_longitude += random.uniform(-0.0001, 0.0001)
        self._current_accuracy = random.uniform(5.0, 20.0)

        self.gpsUpdated.emit(
            self._current_latitude,
            self._current_longitude,
            self._current_accuracy,
        )
        self._write_reading(
            self._current_latitude,
            self._current_longitude,
            self._current_accuracy,
        )

    def _write_reading(self, lat: float, lon: float, accuracy: float) -> None:
        db = SessionLocal()
        try:
            reading = GpsReading(
                session_id=self._session_id,
                timestamp=datetime.now(timezone.utc),
                latitude=lat,
                longitude=lon,
                accuracy_m=accuracy,
            )
            db.add(reading)
            db.commit()
        except Exception:
            logger.exception("Failed to write GpsReading")
            db.rollback()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Future hardware integration stubs
    # ------------------------------------------------------------------

    def connect_gps(self, port: str, baudrate: int = config.GPS_BAUD_RATE) -> None:
        """Connect to a hardware GPS module (Neo6 / similar) via serial."""
        # TODO: open serial port and start NMEA reader thread
        logger.info("connect_gps called (port=%s, baud=%d) — not yet implemented", port, baudrate)

    def _parse_nmea_sentence(self, sentence: str) -> None:
        """Parse a single NMEA sentence (GPGGA, GPRMC, etc.)."""
        # TODO: implement NMEA parsing and call _write_reading
        logger.debug("NMEA: %s", sentence.strip())
