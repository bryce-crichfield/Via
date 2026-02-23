from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QTimer

try:
    import dbus
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

_BLUEZ_SERVICE = "org.bluez"
_DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
_DEVICE_IFACE = "org.bluez.Device1"


class DeviceController(QObject):
    hasConnectedDeviceChanged = pyqtSignal(bool)
    deviceNameChanged = pyqtSignal(str)
    deviceAddressChanged = pyqtSignal(str)
    deviceTypeChanged = pyqtSignal(str)
    showDeviceViewChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hasConnectedDevice = False
        self._deviceName = ""
        self._deviceAddress = ""
        self._deviceType = ""
        self._devicePath = ""
        self._showDeviceView = False
        self._bus = None

        if _DBUS_AVAILABLE:
            try:
                self._bus = dbus.SystemBus()
                self._SetupAdapter()
                self._pollTimer = QTimer(self)
                self._pollTimer.timeout.connect(self._PollConnectedDevice)
                self._pollTimer.start(2000)
                self._PollConnectedDevice()
            except Exception as e:
                print(f"[DeviceController] BlueZ init failed: {e}")
    def _SetupAdapter(self):
        """Make adapter discoverable and pairable on startup"""
        try:
            # Find the Bluetooth adapter (usually hci0)
            manager = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/"),
                _DBUS_OM_IFACE
            )
            objects = manager.GetManagedObjects()
            
            adapter_path = None
            for path in objects:
                if "org.bluez.Adapter1" in objects[path]:
                    adapter_path = path
                    break
            
            if not adapter_path:
                print("[DeviceController] No Bluetooth adapter found")
                return
                
            # Get adapter interface
            adapter = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, adapter_path),
                "org.freedesktop.DBus.Properties"
            )
            
            # Make discoverable and pairable
            adapter.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))  # Always discoverable
            
            print(f"[DeviceController] Adapter {adapter_path} is now discoverable")
            
        except Exception as e:
            print(f"[DeviceController] Adapter setup failed: {e}")
    @pyqtProperty(str, constant=True)
    def adapterName(self):
        """Return the Bluetooth adapter name users should look for"""
        try:
            # Get from adapter properties, or fallback to hostname
            import socket
            return socket.gethostname()
        except:
            return "Audio Receiver"
    @pyqtProperty(bool, notify=hasConnectedDeviceChanged)
    def hasConnectedDevice(self):
        return self._hasConnectedDevice

    @pyqtProperty(str, notify=deviceNameChanged)
    def deviceName(self):
        return self._deviceName

    @pyqtProperty(str, notify=deviceAddressChanged)
    def deviceAddress(self):
        return self._deviceAddress

    @pyqtProperty(str, notify=deviceTypeChanged)
    def deviceType(self):
        return self._deviceType

    @pyqtProperty(bool, notify=showDeviceViewChanged)
    def showDeviceView(self):
        return self._showDeviceView

    @pyqtSlot()
    def toggleDeviceView(self):
        self._showDeviceView = not self._showDeviceView
        self.showDeviceViewChanged.emit(self._showDeviceView)

    @pyqtSlot()
    def closeDeviceView(self):
        if self._showDeviceView:
            self._showDeviceView = False
            self.showDeviceViewChanged.emit(False)

    @pyqtSlot()
    def disconnectDevice(self):
        if not self._devicePath or not _DBUS_AVAILABLE or not self._bus:
            return
        try:
            device = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, self._devicePath),
                _DEVICE_IFACE
            )
            device.Disconnect()
        except Exception as e:
            print(f"[DeviceController] Disconnect error: {e}")

    def _PollConnectedDevice(self):
        try:
            manager = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/"),
                _DBUS_OM_IFACE
            )
            objects = manager.GetManagedObjects()

            foundPath = ""
            foundName = ""
            foundAddress = ""
            foundType = ""

            for path, interfaces in objects.items():
                if _DEVICE_IFACE not in interfaces:
                    continue
                props = interfaces[_DEVICE_IFACE]
                if props.get("Connected", False):
                    foundPath = str(path)
                    foundName = str(props.get("Name", props.get("Address", "Unknown")))
                    foundAddress = str(props.get("Address", ""))
                    foundType = str(props.get("Icon", ""))
                    break  # take first connected device

            found = bool(foundPath)

            if found:
                self._devicePath = foundPath
                if foundName != self._deviceName:
                    self._deviceName = foundName
                    self.deviceNameChanged.emit(foundName)
                if foundAddress != self._deviceAddress:
                    self._deviceAddress = foundAddress
                    self.deviceAddressChanged.emit(foundAddress)
                if foundType != self._deviceType:
                    self._deviceType = foundType
                    self.deviceTypeChanged.emit(foundType)
            else:
                self._devicePath = ""
                if self._deviceName:
                    self._deviceName = ""
                    self.deviceNameChanged.emit("")
                if self._deviceAddress:
                    self._deviceAddress = ""
                    self.deviceAddressChanged.emit("")
                if self._deviceType:
                    self._deviceType = ""
                    self.deviceTypeChanged.emit("")

            if found != self._hasConnectedDevice:
                self._hasConnectedDevice = found
                self.hasConnectedDeviceChanged.emit(found)

        except Exception as e:
            print(f"[DeviceController] Poll error: {e}")
