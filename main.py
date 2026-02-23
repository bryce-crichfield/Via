#!/usr/bin/env python3
import sys
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt, QEvent
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine

from controllers.engine_controller import EngineController
from controllers.media_controller import MusicPlayerController
from controllers.device_controller import DeviceController
from controllers.navigation_controller import NavigationController


class KeyEventFilter(QObject):
    """Event filter to catch keyboard events globally"""
    shutdownRequested = pyqtSignal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.shutdownRequested.emit()
                return True
            elif event.key() == Qt.Key.Key_Q and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.shutdownRequested.emit()
                return True
        return super().eventFilter(obj, event)


def main():
    app = QGuiApplication(sys.argv)
    # app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    engine_controller = EngineController()
    music_controller = MusicPlayerController()
    device_controller = DeviceController()
    nav_controller = NavigationController()

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
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
