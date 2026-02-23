import json
import logging
import threading
import urllib.parse
import urllib.request

from PyQt6.QtCore import QObject, QTimer, pyqtProperty, pyqtSignal, pyqtSlot

try:
    import dbus
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

logger = logging.getLogger(__name__)

_BLUEZ_SERVICE = "org.bluez"
_DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
_MEDIA_PLAYER_IFACE = "org.bluez.MediaPlayer1"
_DBUS_PROPS_IFACE = "org.freedesktop.DBus.Properties"


class MusicPlayerController(QObject):
    # Property-change signals
    trackTitleChanged = pyqtSignal(str)
    artistNameChanged = pyqtSignal(str)
    albumNameChanged = pyqtSignal(str)
    albumArtUrlChanged = pyqtSignal(str)
    isPlayingChanged = pyqtSignal(bool)
    progressChanged = pyqtSignal(float)
    currentTimeChanged = pyqtSignal(int)
    totalTimeChanged = pyqtSignal(int)
    bluetoothConnectedChanged = pyqtSignal(bool)

    # Internal: carries iTunes art URL back to main thread from worker thread
    _artFetched = pyqtSignal(str)

    # Control-request signals (consumed by future MPRIS/dbus integration)
    playPauseRequested = pyqtSignal()
    nextRequested = pyqtSignal()
    previousRequested = pyqtSignal()
    seekRequested = pyqtSignal(float)  # position 0.0–1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._track_title = "No Track Playing"
        self._artist_name = ""
        self._album_name = ""
        self._album_art_url = ""
        self._is_playing = False
        self._progress = 0.0
        self._current_time = 0
        self._total_time = 0
        self._bluetoothConnected = False

        self._media_player_path: str | None = None
        self._poll_miss_count: int = 0
        self._art_search_key: tuple[str, str] = ("", "")  # (title, artist) last searched
        self._bus = dbus.SystemBus() if _DBUS_AVAILABLE else None

        self._mpris_timer = QTimer(self)
        self._mpris_timer.setInterval(1000)
        self._mpris_timer.timeout.connect(self._poll_mpris)

        # Wire control signals to MPRIS forwarding
        self.playPauseRequested.connect(self._mpris_play_pause)
        self.nextRequested.connect(self._mpris_next)
        self.previousRequested.connect(self._mpris_previous)
        # seekRequested is a no-op: BlueZ MediaPlayer1 has no absolute seek

        # Marshal iTunes art URL from worker thread back to Qt main thread
        self._artFetched.connect(self._on_art_fetched)

    # ------------------------------------------------------------------
    # Qt properties
    # ------------------------------------------------------------------

    @pyqtProperty(str, notify=trackTitleChanged)
    def trackTitle(self):
        return self._track_title

    @trackTitle.setter
    def trackTitle(self, value):
        if self._track_title != value:
            self._track_title = value
            self.trackTitleChanged.emit(value)

    @pyqtProperty(str, notify=artistNameChanged)
    def artistName(self):
        return self._artist_name

    @artistName.setter
    def artistName(self, value):
        if self._artist_name != value:
            self._artist_name = value
            self.artistNameChanged.emit(value)

    @pyqtProperty(str, notify=albumNameChanged)
    def albumName(self):
        return self._album_name

    @albumName.setter
    def albumName(self, value):
        if self._album_name != value:
            self._album_name = value
            self.albumNameChanged.emit(value)

    @pyqtProperty(str, notify=albumArtUrlChanged)
    def albumArtUrl(self):
        return self._album_art_url

    @albumArtUrl.setter
    def albumArtUrl(self, value):
        if self._album_art_url != value:
            self._album_art_url = value
            self.albumArtUrlChanged.emit(value)
            logger.info("albumArtUrl → %s", value if value else "(cleared)")

    @pyqtProperty(bool, notify=isPlayingChanged)
    def isPlaying(self):
        return self._is_playing

    @isPlaying.setter
    def isPlaying(self, value):
        if self._is_playing != value:
            self._is_playing = value
            self.isPlayingChanged.emit(value)

    @pyqtProperty(float, notify=progressChanged)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        if self._progress != value:
            self._progress = value
            self.progressChanged.emit(value)

    @pyqtProperty(int, notify=currentTimeChanged)
    def currentTime(self):
        return self._current_time

    @currentTime.setter
    def currentTime(self, value):
        if self._current_time != value:
            self._current_time = value
            self.currentTimeChanged.emit(value)

    @pyqtProperty(int, notify=totalTimeChanged)
    def totalTime(self):
        return self._total_time

    @totalTime.setter
    def totalTime(self, value):
        if self._total_time != value:
            self._total_time = value
            self.totalTimeChanged.emit(value)

    @pyqtProperty(bool, notify=bluetoothConnectedChanged)
    def bluetoothConnected(self):
        return self._bluetoothConnected

    @bluetoothConnected.setter
    def bluetoothConnected(self, value):
        if self._bluetoothConnected != value:
            self._bluetoothConnected = value
            self.bluetoothConnectedChanged.emit(value)

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------

    @pyqtSlot(str, str, str, str)
    def updateTrackInfo(self, title, artist, album, art_url):
        """Update all track metadata at once."""
        self.trackTitle = title
        self.artistName = artist
        self.albumName = album
        self.albumArtUrl = art_url
        logger.info("Track changed → %s – %s", artist, title)

    @pyqtSlot(bool, int, int)
    def updatePlaybackState(self, playing, current_sec, total_sec):
        """Update playback state and derived progress."""
        self.isPlaying = playing
        self.currentTime = current_sec
        self.totalTime = total_sec
        self.progress = current_sec / total_sec if total_sec > 0 else 0.0

    @pyqtSlot()
    def play(self):
        self.isPlaying = True
        logger.info("Playback started")

    @pyqtSlot()
    def pause(self):
        self.isPlaying = False
        logger.info("Playback paused")

    @pyqtSlot()
    def stop(self):
        self.isPlaying = False
        self.currentTime = 0
        self.progress = 0.0
        logger.info("Playback stopped")

    @pyqtSlot()
    def manageBluetoothRequested(self):
        """Handle Bluetooth management request from QML."""
        logger.info("Bluetooth management requested")

    @pyqtSlot(bool)
    def set_bluetooth_connected(self, connected: bool):
        """Called by DeviceController when BT connection state changes."""
        self.bluetoothConnected = connected
        if connected:
            self._media_player_path = None
            self._mpris_timer.start()
            logger.info("MPRIS polling started")
        else:
            self._mpris_timer.stop()
            self._media_player_path = None
            self._poll_miss_count = 0
            self._art_search_key = ("", "")
            self._reset_track_state()
            logger.info("MPRIS polling stopped — device disconnected")

    # ------------------------------------------------------------------
    # MPRIS / BlueZ MediaPlayer1 internals
    # ------------------------------------------------------------------

    def _reset_track_state(self):
        self.trackTitle = "No Track Playing"
        self.artistName = ""
        self.albumName = ""
        self.albumArtUrl = ""
        self.isPlaying = False
        self.currentTime = 0
        self.totalTime = 0
        self.progress = 0.0

    def _find_media_player(self) -> "str | None":
        """Return the D-Bus object path of the first BlueZ MediaPlayer1, or None."""
        if not _DBUS_AVAILABLE or self._bus is None:
            return None
        try:
            manager = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, "/"),
                _DBUS_OM_IFACE,
            )
            objects = manager.GetManagedObjects()
            for path, interfaces in objects.items():
                if _MEDIA_PLAYER_IFACE in interfaces:
                    return str(path)
        except Exception:
            logger.exception("Error searching for MediaPlayer1")
        return None

    def _poll_mpris(self):
        if not _DBUS_AVAILABLE or self._bus is None:
            return

        if self._media_player_path is None:
            self._media_player_path = self._find_media_player()
            if self._media_player_path is None:
                self._poll_miss_count += 1
                if self._poll_miss_count % 10 == 1:
                    logger.info(
                        "No BlueZ MediaPlayer1 found yet (poll #%d) — "
                        "is music playing on the phone?",
                        self._poll_miss_count,
                    )
                return
            logger.info("MediaPlayer1 found at %s", self._media_player_path)
            self._poll_miss_count = 0

        try:
            props_iface = dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, self._media_player_path),
                _DBUS_PROPS_IFACE,
            )
            all_props = props_iface.GetAll(_MEDIA_PLAYER_IFACE)

            track = all_props.get("Track", {})
            logger.debug("Track dict keys from BlueZ: %s", list(track.keys()))
            title = str(track.get("Title", "")) or "No Track Playing"
            artist = str(track.get("Artist", ""))
            album = str(track.get("Album", ""))
            duration_ms = int(track.get("Duration", 0))

            # --- Album art: prefer BlueZ AVRCP, fall back to iTunes API ---
            raw_art = track.get("AlbumArt", None)
            bluez_art = ""
            if raw_art is not None:
                bluez_art = str(raw_art)
                if bluez_art and not bluez_art.startswith("file://"):
                    bluez_art = "file://" + bluez_art
                if bluez_art:
                    logger.info("BlueZ AlbumArt: %s", bluez_art)

            search_key = (title, artist)
            if bluez_art:
                # BlueZ provided art directly — use it
                self.albumArtUrl = bluez_art
                self._art_search_key = search_key
            elif search_key != self._art_search_key and title != "No Track Playing" and artist:
                # New track, no BlueZ art — query iTunes in background
                self._art_search_key = search_key
                self.albumArtUrl = ""  # clear stale art while fetching
                logger.info("No BlueZ art for %r / %r — querying iTunes", title, artist)
                threading.Thread(
                    target=self._fetch_itunes_art,
                    args=(title, artist),
                    daemon=True,
                ).start()
            # else: same track, leave albumArtUrl alone (iTunes fetch may be in progress)

            status = str(all_props.get("Status", "stopped"))
            position_ms = int(all_props.get("Position", 0))

            total_sec = duration_ms // 1000
            current_sec = position_ms // 1000

            self.trackTitle = title
            self.artistName = artist
            self.albumName = album
            self.isPlaying = status == "playing"
            self.totalTime = total_sec
            self.currentTime = current_sec
            self.progress = current_sec / total_sec if total_sec > 0 else 0.0

        except dbus.DBusException:
            logger.warning("MediaPlayer1 gone — clearing path")
            self._media_player_path = None
        except Exception:
            logger.exception("MPRIS poll error")

    @pyqtSlot(str)
    def _on_art_fetched(self, url: str):
        """Receives iTunes art URL on the Qt main thread and updates the property."""
        self.albumArtUrl = url

    def _fetch_itunes_art(self, title: str, artist: str):
        """Worker thread: query iTunes Search API and emit art URL if found."""
        try:
            query = urllib.parse.urlencode({
                "term": f"{artist} {title}",
                "entity": "song",
                "limit": "5",
            })
            req_url = f"https://itunes.apple.com/search?{query}"
            with urllib.request.urlopen(req_url, timeout=8) as resp:
                data = json.loads(resp.read())
            results = data.get("results", [])
            if results:
                art_url = results[0].get("artworkUrl100", "")
                if art_url:
                    # Upgrade from 100×100 thumbnail to 600×600
                    art_url = art_url.replace("100x100bb", "600x600bb")
                    logger.info("iTunes art found: %s", art_url)
                    self._artFetched.emit(art_url)
                    return
            logger.info("iTunes art: no results for %r / %r", title, artist)
        except Exception:
            logger.exception("iTunes art fetch failed for %r / %r", title, artist)

    def _mpris_play_pause(self):
        player = self._get_media_player_iface()
        if player is None:
            return
        try:
            if self._is_playing:
                player.Pause()
            else:
                player.Play()
        except Exception:
            logger.exception("MPRIS play/pause failed")

    def _mpris_next(self):
        player = self._get_media_player_iface()
        if player is None:
            return
        try:
            player.Next()
        except Exception:
            logger.exception("MPRIS next failed")

    def _mpris_previous(self):
        player = self._get_media_player_iface()
        if player is None:
            return
        try:
            player.Previous()
        except Exception:
            logger.exception("MPRIS previous failed")

    def _get_media_player_iface(self):
        if not _DBUS_AVAILABLE or self._bus is None or self._media_player_path is None:
            return None
        try:
            return dbus.Interface(
                self._bus.get_object(_BLUEZ_SERVICE, self._media_player_path),
                _MEDIA_PLAYER_IFACE,
            )
        except Exception:
            logger.exception("Could not get MediaPlayer1 interface")
            return None
