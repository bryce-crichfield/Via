"""
log.py — Persistent file logging for the Via dashboard.

Call log.setup() once at startup before any other module creates a logger.
Writes to logs/via.log (rotating, 5 MB × 3 files) as well as stderr.
"""
import logging
import logging.handlers
from pathlib import Path

import config

_LOG_DIR: Path = config.BASE_DIR / "logs"
_LOG_FILE: Path = _LOG_DIR / "via.log"
_FMT = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
_BACKUP_COUNT = 3              # via.log  via.log.1  via.log.2


def setup() -> None:
    """Configure the root logger with a rotating file handler + stderr handler."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, config.LOG_LEVEL, logging.INFO)
    formatter = logging.Formatter(_FMT, datefmt=_DATEFMT)

    root = logging.getLogger()
    root.setLevel(level)

    # Rotating file — persists across restarts, won't eat disk
    fh = logging.handlers.RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    fh.setFormatter(formatter)
    root.addHandler(fh)

    # Console — useful during dev / SSH sessions
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    root.addHandler(ch)

    logging.getLogger(__name__).info(
        "Logging started — file: %s  level: %s", _LOG_FILE, config.LOG_LEVEL
    )
