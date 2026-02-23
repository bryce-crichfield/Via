"""
Application-wide configuration.

All values can be overridden via environment variables.  Sensitive or
machine-specific settings (port paths, etc.) belong here rather than
scattered throughout the codebase.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'app.db'}",
)

# ---------------------------------------------------------------------------
# OBD-II
# ---------------------------------------------------------------------------
# Set to a specific port string (e.g. "/dev/ttyUSB0") or leave None for
# auto-detection by the python-obd library.
OBD_PORT: str | None = os.environ.get("OBD_PORT", None)

# How often (in seconds) to write an EngineReading row.
# The OBD loop runs at 10 Hz; this downsamples writes to 1/sec by default.
OBD_LOG_INTERVAL_S: float = float(os.environ.get("OBD_LOG_INTERVAL_S", "1.0"))

# ---------------------------------------------------------------------------
# GPS
# ---------------------------------------------------------------------------
# Set GPS_SIMULATE=false and provide GPS_PORT when real hardware is attached.
GPS_SIMULATE: bool = os.environ.get("GPS_SIMULATE", "true").lower() != "false"
GPS_PORT: str | None = os.environ.get("GPS_PORT", None)
GPS_BAUD_RATE: int = int(os.environ.get("GPS_BAUD_RATE", "9600"))

# How often (in ms) the simulated GPS emits an update.
GPS_UPDATE_INTERVAL_MS: int = int(os.environ.get("GPS_UPDATE_INTERVAL_MS", "2000"))

# ---------------------------------------------------------------------------
# Bluetooth
# ---------------------------------------------------------------------------
BT_POLL_INTERVAL_MS: int = int(os.environ.get("BT_POLL_INTERVAL_MS", "2000"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
