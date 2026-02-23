from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot
from PyQt6.QtGui import QGuiApplication
from threading import Thread
import time
import obd


class EngineController(QObject):
    # Signals for QML binding
    connectedChanged = pyqtSignal(bool)
    connectionStatusChanged = pyqtSignal(str)
    rpmChanged = pyqtSignal(int)
    speedChanged = pyqtSignal(int)
    coolantTempChanged = pyqtSignal(str)
    throttleChanged = pyqtSignal(str)
    engineLoadChanged = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
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
        
    # Properties for QML binding
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
    
    @pyqtSlot()
    def attemptConnection(self):
        """Start connection attempt"""
        self.connectionStatus = "Connecting..."
        Thread(target=self._connect_obd, daemon=True).start()
    
    def _connect_obd(self):
        """Background thread to connect to OBD"""
        try:
            self.connection = obd.OBD()
            
            if self.connection.is_connected():
                self.connected = True
                self.connectionStatus = "Connected"
                # Start data reading
                self.obd_thread = Thread(target=self._obd_loop, daemon=True)
                self.obd_thread.start()
            else:
                self.connectionStatus = "No adapter found"
                
        except Exception as e:
            self.connectionStatus = f"Error: {str(e)}"
    
    def _obd_loop(self):
        """Background thread to read OBD data"""
        last_check = time.time()
        
        while self.running and self._connected:
            try:
                # Check connection status every 2 seconds
                if time.time() - last_check > 2:
                    if not self.connection.is_connected():
                        self.connected = False
                        self.connectionStatus = "Disconnected"
                        break
                    last_check = time.time()
                
                # Query PIDs
                rpm = self.connection.query(obd.commands.RPM)
                speed = self.connection.query(obd.commands.SPEED)
                coolant = self.connection.query(obd.commands.COOLANT_TEMP)
                throttle = self.connection.query(obd.commands.THROTTLE_POS)
                load = self.connection.query(obd.commands.ENGINE_LOAD)
                
                # Update properties
                if not rpm.is_null():
                    self.rpm = int(rpm.value.magnitude)
                if not speed.is_null():
                    self.speed = int(speed.value.magnitude)
                if not coolant.is_null():
                    self.coolantTemp = f"{int(coolant.value.magnitude)}°C"
                if not throttle.is_null():
                    self.throttle = f"{int(throttle.value.magnitude)}%"
                if not load.is_null():
                    self.engineLoad = f"{int(load.value.magnitude)}%"
                
                time.sleep(0.1)  # 10Hz update rate
                
            except Exception as e:
                print(f"Read error: {e}")
                self.connected = False
                self.connectionStatus = "Read error"
                break
    
    @pyqtSlot()
    def disconnect(self):
        """Disconnect from OBD"""
        self.connected = False
        if self.connection:
            self.connection.close()
            self.connection = None
        self.connectionStatus = "Not Connected"
        # Reset values
        self.rpm = 0
        self.speed = 0
        self.coolantTemp = "N/A"
        self.throttle = "N/A"
        self.engineLoad = "N/A"
    
    @pyqtSlot()
    def quit(self):
        """Clean shutdown"""
        self.running = False
        self.disconnect()
        QGuiApplication.quit()

