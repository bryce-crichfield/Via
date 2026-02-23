import QtQuick
import QtWebEngine

WebEngineView {
    id: navigationView
    
    property var controller  // Will be set from Python
    
    url: Qt.resolvedUrl("../assets/navigation/map.html")
    
    // Enable JavaScript communication
    settings.javascriptEnabled: true
    settings.localContentCanAccessRemoteUrls: true
    
    // Called when GPS data updates
    function updateGPSData(latitude, longitude, accuracy) {
        const gpsData = {
            latitude: latitude,
            longitude: longitude,
            accuracy: accuracy
        };
        
        runJavaScript(
            `window.updateGPS(${JSON.stringify(gpsData)});`
        );
    }
    
    // Handle page load completion
    onLoadingChanged: function(loadRequest) {
        if (loadRequest.status === WebEngineView.LoadSucceededStatus) {
            console.log("Map loaded successfully");
            // Send initial GPS position
            if (controller) {
                controller.requestGPSUpdate();
            }
        }
    }
}