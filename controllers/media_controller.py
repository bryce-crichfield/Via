from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot


class MusicPlayerController(QObject):
    # Signals for property changes
    trackTitleChanged = pyqtSignal(str)
    artistNameChanged = pyqtSignal(str)
    albumNameChanged = pyqtSignal(str)
    albumArtUrlChanged = pyqtSignal(str)
    isPlayingChanged = pyqtSignal(bool)
    progressChanged = pyqtSignal(float)
    currentTimeChanged = pyqtSignal(int)
    totalTimeChanged = pyqtSignal(int)
    bluetoothConnectedChanged = pyqtSignal(bool)
    
    # Signals for control requests from UI
    playPauseRequested = pyqtSignal()
    nextRequested = pyqtSignal()
    previousRequested = pyqtSignal()
    seekRequested = pyqtSignal(float)  # position 0.0-1.0
    
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
    
    # Track Title
    @pyqtProperty(str, notify=trackTitleChanged)
    def trackTitle(self):
        return self._track_title
    
    @trackTitle.setter
    def trackTitle(self, value):
        if self._track_title != value:
            self._track_title = value
            self.trackTitleChanged.emit(value)
    
    # Artist Name
    @pyqtProperty(str, notify=artistNameChanged)
    def artistName(self):
        return self._artist_name
    
    @pyqtProperty(bool, notify=bluetoothConnectedChanged)
    def bluetoothConnected(self):
        return self._bluetoothConnected

    @artistName.setter
    def artistName(self, value):
        if self._artist_name != value:
            self._artist_name = value
            self.artistNameChanged.emit(value)
    
    # Album Name
    @pyqtProperty(str, notify=albumNameChanged)
    def albumName(self):
        return self._album_name
    
    @albumName.setter
    def albumName(self, value):
        if self._album_name != value:
            self._album_name = value
            self.albumNameChanged.emit(value)
    
    # Album Art URL
    @pyqtProperty(str, notify=albumArtUrlChanged)
    def albumArtUrl(self):
        return self._album_art_url
    
    @albumArtUrl.setter
    def albumArtUrl(self, value):
        if self._album_art_url != value:
            self._album_art_url = value
            self.albumArtUrlChanged.emit(value)
    
    # Is Playing
    @pyqtProperty(bool, notify=isPlayingChanged)
    def isPlaying(self):
        return self._is_playing
    
    @isPlaying.setter
    def isPlaying(self, value):
        if self._is_playing != value:
            self._is_playing = value
            self.isPlayingChanged.emit(value)
    
    # Progress
    @pyqtProperty(float, notify=progressChanged)
    def progress(self):
        return self._progress
    
    @progress.setter
    def progress(self, value):
        if self._progress != value:
            self._progress = value
            self.progressChanged.emit(value)
    
    # Current Time
    @pyqtProperty(int, notify=currentTimeChanged)
    def currentTime(self):
        return self._current_time
    
    @currentTime.setter
    def currentTime(self, value):
        if self._current_time != value:
            self._current_time = value
            self.currentTimeChanged.emit(value)
    
    # Total Time
    @pyqtProperty(int, notify=totalTimeChanged)
    def totalTime(self):
        return self._total_time
    
    @totalTime.setter
    def totalTime(self, value):
        if self._total_time != value:
            self._total_time = value
            self.totalTimeChanged.emit(value)
    
    # Public methods for updating state
    @pyqtSlot(str, str, str, str)
    def updateTrackInfo(self, title, artist, album, art_url):
        """Update all track information at once"""
        self.trackTitle = title
        self.artistName = artist
        self.albumName = album
        self.albumArtUrl = art_url
    
    @pyqtSlot(bool, int, int)
    def updatePlaybackState(self, playing, current_sec, total_sec):
        """Update playback state"""
        self.isPlaying = playing
        self.currentTime = current_sec
        self.totalTime = total_sec
        self.progress = current_sec / total_sec if total_sec > 0 else 0.0
    
    @pyqtSlot()
    def play(self):
        """Start playback"""
        self.isPlaying = True
    
    @pyqtSlot()
    def pause(self):
        """Pause playback"""
        self.isPlaying = False
    
    @pyqtSlot()
    def stop(self):
        """Stop playback and reset position"""
        self.isPlaying = False
        self.currentTime = 0
        self.progress = 0.0

    @pyqtSlot()
    def manageBluetoothRequested(self):
        """Handle Bluetooth management request"""
        print("Bluetooth management requested")
        # Implement Bluetooth management logic here (e.g., open Bluetooth settings)