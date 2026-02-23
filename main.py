#!/usr/bin/env python3
import logging
import sys

from PyQt6.QtCore import QEvent, QObject, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtWebEngineQuick import QtWebEngineQuick

import config
import models
from controllers.device_controller import DeviceController
from controllers.engine_controller import EngineController
from controllers.media_controller import MusicPlayerController
from controllers.navigation_controller import NavigationController

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class KeyEventFilter(QObject):
    """Global keyboard shortcut handler (Escape / Ctrl+Q → quit)."""

    shutdownRequested = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.shutdownRequested.emit()
                return True
            if (
                event.key() == Qt.Key.Key_Q
                and event.modifiers() == Qt.KeyboardModifier.ControlModifier
            ):
                self.shutdownRequested.emit()
                return True
        return super().eventFilter(obj, event)


def main() -> None:
    models.init_db()

    QtWebEngineQuick.initialize()
    app = QGuiApplication(sys.argv)
    # app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    engine_controller = EngineController()
    music_controller = MusicPlayerController()
    device_controller = DeviceController()
    nav_controller = NavigationController()

    # Propagate the active session ID to controllers that log GPS data
    engine_controller.sessionIdChanged.connect(nav_controller.set_session_id)

    # Bridge BT connection state into the music controller (enables MPRIS polling)
    device_controller.hasConnectedDeviceChanged.connect(music_controller.set_bluetooth_connected)

    key_filter = KeyEventFilter()
    key_filter.shutdownRequested.connect(engine_controller.quit)
    app.installEventFilter(key_filter)

    qml_engine = QQmlApplicationEngine()
    qml_engine.rootContext().setContextProperty("engineController", engine_controller)
    qml_engine.rootContext().setContextProperty("musicController", music_controller)
    qml_engine.rootContext().setContextProperty("deviceController", device_controller)
    qml_engine.rootContext().setContextProperty("navigationController", nav_controller)

    qml_engine.load("views/MainView.qml")

    if not qml_engine.rootObjects():
        logger.critical("Failed to load QML root object — exiting.")
        sys.exit(-1)

    logger.info("Via dashboard started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
