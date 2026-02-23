import logging
import time
from datetime import datetime, timezone
from threading import Thread

import obd
from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QGuiApplication

import config
import models
from models import DrivingSession, EngineReading, SessionLocal

logger = logging.getLogger(__name__)


class EngineController(QObject):
    # Property-change signals consumed by QML
    connectedChanged = pyqtSignal(bool)
    connectionStatusChanged = pyqtSignal(str)
    rpmChanged = pyqtSignal(int)
    speedChanged = pyqtSignal(int)
    coolantTempChanged = pyqtSignal(str)
    throttleChanged = pyqtSignal(str)
    engineLoadChanged = pyqtSignal(str)

    # Emits the active session PK (or -1 when no session is open).
    # Other controllers listen to this to associate their own DB rows.
    sessionIdChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connection = None
        self._connected = False
        self._connectionStatus = "Not Connected"
        self._rpm = 0
        self._speed = 0
        self._coolantTemp = "N/A"
        self._throttle = "N/A"
        self._engineLoad = "N/A"
        self.running = True
        self.obd_thread = None
        self._session_id: int | None = None

    # ------------------------------------------------------------------
    # Qt properties
    # ------------------------------------------------------------------

    @pyqtProperty(bool, notify=connectedChanged)
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        if self._connected != value:
            self._connected = value
            self.connectedChanged.emit(value)

    @pyqtProperty(str, notify=connectionStatusChanged)
    def connectionStatus(self):
        return self._connectionStatus

    @connectionStatus.setter
    def connectionStatus(self, value):
        if self._connectionStatus != value:
            self._connectionStatus = value
            self.connectionStatusChanged.emit(value)

    @pyqtProperty(int, notify=rpmChanged)
    def rpm(self):
        return self._rpm

    @rpm.setter
    def rpm(self, value):
        if self._rpm != value:
            self._rpm = value
            self.rpmChanged.emit(value)

    @pyqtProperty(int, notify=speedChanged)
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        if self._speed != value:
            self._speed = value
            self.speedChanged.emit(value)

    @pyqtProperty(str, notify=coolantTempChanged)
    def coolantTemp(self):
        return self._coolantTemp

    @coolantTemp.setter
    def coolantTemp(self, value):
        if self._coolantTemp != value:
            self._coolantTemp = value
            self.coolantTempChanged.emit(value)

    @pyqtProperty(str, notify=throttleChanged)
    def throttle(self):
        return self._throttle

    @throttle.setter
    def throttle(self, value):
        if self._throttle != value:
            self._throttle = value
            self.throttleChanged.emit(value)

    @pyqtProperty(str, notify=engineLoadChanged)
    def engineLoad(self):
        return self._engineLoad

    @engineLoad.setter
    def engineLoad(self, value):
        if self._engineLoad != value:
            self._engineLoad = value
            self.engineLoadChanged.emit(value)

    # ------------------------------------------------------------------
    # OBD connection
    # ------------------------------------------------------------------

    @pyqtSlot()
    def attemptConnection(self):
        """Start OBD connection attempt in a background thread."""
        self.connectionStatus = "Connecting..."
        Thread(target=self._connect_obd, daemon=True).start()

    def _connect_obd(self):
        try:
            self.connection = obd.OBD(config.OBD_PORT)

            if self.connection.is_connected():
                self._open_session()
                self.connected = True
                self.connectionStatus = "Connected"
                self.obd_thread = Thread(target=self._obd_loop, daemon=True)
                self.obd_thread.start()
            else:
                self.connectionStatus = "No adapter found"

        except Exception:
            logger.exception("OBD connection error")
            self.connectionStatus = "Connection error"

    def _open_session(self) -> None:
        """Create a DrivingSession row and broadcast its ID."""
        db = SessionLocal()
        try:
            session = DrivingSession(started_at=datetime.now(timezone.utc))
            db.add(session)
            db.commit()
            db.refresh(session)
            self._session_id = session.id
            logger.info("Driving session started (id=%d)", self._session_id)
            self.sessionIdChanged.emit(self._session_id)
        except Exception:
            logger.exception("Failed to create DrivingSession")
            db.rollback()
        finally:
            db.close()

    def _close_session(self) -> None:
        """Stamp ended_at on the current DrivingSession."""
        if self._session_id is None:
            return
        db = SessionLocal()
        try:
            session = db.get(DrivingSession, self._session_id)
            if session:
                session.ended_at = datetime.now(timezone.utc)
                db.commit()
                logger.info("Driving session ended (id=%d)", self._session_id)
        except Exception:
            logger.exception("Failed to close DrivingSession id=%s", self._session_id)
            db.rollback()
        finally:
            db.close()
            self._session_id = None
            self.sessionIdChanged.emit(-1)

    # ------------------------------------------------------------------
    # OBD data loop
    # ------------------------------------------------------------------

    def _obd_loop(self):
        """Background thread: read OBD PIDs and persist telemetry."""
        last_check = time.monotonic()
        last_log = time.monotonic()

        while self.running and self._connected:
            try:
                now = time.monotonic()

                # Periodic connection health-check
                if now - last_check > 2:
                    if not self.connection.is_connected():
                        logger.warning("OBD connection lost")
                        self.connected = False
                        self.connectionStatus = "Disconnected"
                        break
                    last_check = now

                # Query PIDs
                rpm_r = self.connection.query(obd.commands.RPM)
                speed_r = self.connection.query(obd.commands.SPEED)
                coolant_r = self.connection.query(obd.commands.COOLANT_TEMP)
                throttle_r = self.connection.query(obd.commands.THROTTLE_POS)
                load_r = self.connection.query(obd.commands.ENGINE_LOAD)

                # Extract raw numeric values for logging before formatting
                rpm_val = int(rpm_r.value.magnitude) if not rpm_r.is_null() else None
                speed_val = int(speed_r.value.magnitude) if not speed_r.is_null() else None
                coolant_val = int(coolant_r.value.magnitude) if not coolant_r.is_null() else None
                throttle_val = int(throttle_r.value.magnitude) if not throttle_r.is_null() else None
                load_val = int(load_r.value.magnitude) if not load_r.is_null() else None

                # Update Qt properties (drives QML)
                if rpm_val is not None:
                    self.rpm = rpm_val
                if speed_val is not None:
                    self.speed = speed_val
                if coolant_val is not None:
                    self.coolantTemp = f"{coolant_val}°C"
                if throttle_val is not None:
                    self.throttle = f"{throttle_val}%"
                if load_val is not None:
                    self.engineLoad = f"{load_val}%"

                # Persist one reading per OBD_LOG_INTERVAL_S
                if now - last_log >= config.OBD_LOG_INTERVAL_S:
                    self._write_reading(rpm_val, speed_val, coolant_val, throttle_val, load_val)
                    last_log = now

                time.sleep(0.1)  # 10 Hz

            except Exception:
                logger.exception("OBD read error")
                self.connected = False
                self.connectionStatus = "Read error"
                break

        self._close_session()

    def _write_reading(self, rpm, speed_kph, coolant_temp_c, throttle_pct, engine_load_pct) -> None:
        db = SessionLocal()
        try:
            reading = EngineReading(
                session_id=self._session_id,
                timestamp=datetime.now(timezone.utc),
                rpm=rpm,
                speed_kph=speed_kph,
                coolant_temp_c=coolant_temp_c,
                throttle_pct=throttle_pct,
                engine_load_pct=engine_load_pct,
            )
            db.add(reading)
            db.commit()
        except Exception:
            logger.exception("Failed to write EngineReading")
            db.rollback()
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Control slots
    # ------------------------------------------------------------------

    @pyqtSlot()
    def disconnect(self):
        self.connected = False
        if self.connection:
            self.connection.close()
            self.connection = None
        self.connectionStatus = "Not Connected"
        self.rpm = 0
        self.speed = 0
        self.coolantTemp = "N/A"
        self.throttle = "N/A"
        self.engineLoad = "N/A"
        # _close_session is called at the end of _obd_loop; call it here
        # too for the case where disconnect() is invoked before the loop exits.
        if self._session_id is not None:
            self._close_session()

    @pyqtSlot()
    def quit(self):
        self.running = False
        self.disconnect()
        QGuiApplication.quit()
