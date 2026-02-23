import logging

from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

import config

try:
    import dbus
    import dbus.service
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

logger = logging.getLogger(__name__)

_BLUEZ_SERVICE = "org.bluez"
_DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
_DEVICE_IFACE = "org.bluez.Device1"
_MEDIA_CONTROL_IFACE = "org.bluez.MediaControl1"
_AGENT_IFACE = "org.bluez.Agent1"
_AGENT_PATH = "/org/bluez/via_agent"


class _PairingAgent(dbus.service.Object):
    """NoInputNoOutput pairing agent — auto-accepts all pairing requests."""

    @dbus.service.method(_AGENT_IFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        logger.info("PairingAgent: auto-authorizing device %s", device)

    @dbus.service.method(_AGENT_IFACE, in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        logger.info("PairingAgent: auto-authorizing service %s on %s", uuid, device)

    @dbus.service.method(_AGENT_IFACE, in_signature="", out_signature="")
    def Cancel(self):
        logger.info("PairingAgent: Cancel called")

    @dbus.service.method(_AGENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        logger.info("PairingAgent: Release called")


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
                self._RegisterPairingAgent()
                self._pollTimer = QTimer(self)
                self._pollTimer.timeout.connect(self._PollConnectedDevice)
                self._pollTimer.start(config.BT_POLL_INTERVAL_MS)
                self._PollConnectedDevice()
            except Exception:
                logger.exception("BlueZ init failed")
        else:
            logger.warning("dbus not available — Bluetooth device detection disabled")

    # ------------------------------------------------------------------
    # Adapter setup
    # ------------------------------------------------------------------

    def _SetupAdapter(self):
        """Make the Bluetooth adapter always discoverable and pairable."""
        try:
            manager = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/"),
                _DBUS_OM_IFACE,
            )
            objects = manager.GetManagedObjects()

            adapter_path = next(
                (p for p, ifaces in objects.items() if "org.bluez.Adapter1" in ifaces),
                None,
            )
            if not adapter_path:
                logger.warning("No Bluetooth adapter found")
                return

            adapter = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, adapter_path),
                "org.freedesktop.DBus.Properties",
            )
            adapter.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "Discoverable", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "Pairable", dbus.Boolean(True))
            adapter.Set("org.bluez.Adapter1", "DiscoverableTimeout", dbus.UInt32(0))
            logger.info("Bluetooth adapter %s is discoverable", adapter_path)

        except Exception:
            logger.exception("Adapter setup failed")

    # ------------------------------------------------------------------
    # Pairing agent
    # ------------------------------------------------------------------

    def _RegisterPairingAgent(self):
        """Register a NoInputNoOutput pairing agent so new devices can pair."""
        try:
            self._agent = _PairingAgent(self._bus, _AGENT_PATH)
            agent_mgr = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/org/bluez"),
                "org.bluez.AgentManager1",
            )
            agent_mgr.RegisterAgent(_AGENT_PATH, "NoInputNoOutput")
            agent_mgr.RequestDefaultAgent(_AGENT_PATH)
            logger.info("Bluetooth pairing agent registered at %s", _AGENT_PATH)
        except Exception:
            logger.exception("Pairing agent registration failed")

    # ------------------------------------------------------------------
    # Qt properties
    # ------------------------------------------------------------------

    @pyqtProperty(str, constant=True)
    def adapterName(self):
        try:
            import socket
            return socket.gethostname()
        except Exception:
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

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

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
                _DEVICE_IFACE,
            )
            device.Disconnect()
        except Exception:
            logger.exception("Bluetooth disconnect failed")

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    def _PollConnectedDevice(self):
        try:
            manager = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/"),
                _DBUS_OM_IFACE,
            )
            objects = manager.GetManagedObjects()

            found_path = found_name = found_address = found_type = ""

            # Two-pass: prefer audio (MediaControl1) devices over plain connected devices.
            audio_candidate = plain_candidate = None
            for path, interfaces in objects.items():
                if _DEVICE_IFACE not in interfaces:
                    continue
                props = interfaces[_DEVICE_IFACE]
                if not props.get("Connected", False):
                    continue
                candidate = (
                    str(path),
                    str(props.get("Name", props.get("Address", "Unknown"))),
                    str(props.get("Address", "")),
                    str(props.get("Icon", "")),
                )
                if _MEDIA_CONTROL_IFACE in interfaces:
                    audio_candidate = candidate
                    break  # audio device found — no need to keep scanning
                elif plain_candidate is None:
                    plain_candidate = candidate

            best = audio_candidate or plain_candidate
            if best:
                found_path, found_name, found_address, found_type = best

            found = bool(found_path)

            if found:
                self._devicePath = found_path
                if found_name != self._deviceName:
                    self._deviceName = found_name
                    self.deviceNameChanged.emit(found_name)
                if found_address != self._deviceAddress:
                    self._deviceAddress = found_address
                    self.deviceAddressChanged.emit(found_address)
                if found_type != self._deviceType:
                    self._deviceType = found_type
                    self.deviceTypeChanged.emit(found_type)
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
                logger.info(
                    "Bluetooth device %s: %s",
                    "connected" if found else "disconnected",
                    found_name or self._deviceName or "unknown",
                )

        except Exception:
            logger.exception("Bluetooth poll error")
