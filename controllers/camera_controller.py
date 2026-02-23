import logging

from PyQt6.QtCore import QObject, pyqtProperty, pyqtSignal, pyqtSlot

logger = logging.getLogger(__name__)


class CameraController(QObject):
    """Placeholder controller for future camera integration."""

    isActiveChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_active = False
        logger.debug("CameraController initialised (no hardware attached)")

    @pyqtProperty(bool, notify=isActiveChanged)
    def isActive(self):
        return self._is_active

    @pyqtSlot()
    def start(self):
        """Start camera capture — not yet implemented."""
        logger.info("CameraController.start() called — not yet implemented")

    @pyqtSlot()
    def stop(self):
        """Stop camera capture — not yet implemented."""
        logger.info("CameraController.stop() called — not yet implemented")
