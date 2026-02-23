from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
import random


class NavigationController(QObject):
    """Controller for GPS navigation and map interaction"""
    
    gpsUpdated = pyqtSignal(float, float, float)  # lat, lon, accuracy
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Fake GPS state for now
        self._current_latitude = 37.7749
        self._current_longitude = -122.4194
        self._current_accuracy = 15.0
        
        # Setup timer for simulated GPS updates (remove when using real GPS)
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._simulate_gps_update)
        self._update_timer.start(2000)  # Update every 2 seconds
    
    @pyqtSlot()
    def requestGPSUpdate(self):
        """Request current GPS position"""
        self.gpsUpdated.emit(
            self._current_latitude,
            self._current_longitude,
            self._current_accuracy
        )
    
    def _simulate_gps_update(self):
        """Simulate GPS movement (for testing)"""
        # Random walk simulation
        self._current_latitude += random.uniform(-0.0001, 0.0001)
        self._current_longitude += random.uniform(-0.0001, 0.0001)
        self._current_accuracy = random.uniform(5.0, 20.0)
        
        self.gpsUpdated.emit(
            self._current_latitude,
            self._current_longitude,
            self._current_accuracy
        )
    
    # Methods for future Neo6 GPS integration
    def connect_gps(self, port: str, baudrate: int = 9600):
        """Connect to Neo6 GPS module"""
        # TODO: Implement serial connection to Neo6
        pass
    
    def _parse_nmea_sentence(self, sentence: str):
        """Parse NMEA sentences from GPS"""
        # TODO: Implement NMEA parsing (GPGGA, GPRMC, etc.)
        pass