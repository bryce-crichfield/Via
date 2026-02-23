import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "../components"

ApplicationWindow {
    id: window
    visible: true
    width: 800
    height: 480
    title: "EscapeDash"
    color: "black"

    // Connection Screen — shown when NOT connected
    Item {
        id: connectionScreen
        anchors.fill: parent
        visible: engineController.connected

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 20

            Text {
                text: "OBD-II DASHBOARD"
                font.pixelSize: 36
                font.bold: true
                color: "cyan"
                Layout.alignment: Qt.AlignHCenter
            }

            Rectangle {
                width: 20
                height: 20
                radius: 10
                color: engineController.connectionStatus === "Connected" ? "lime" :
                       engineController.connectionStatus === "Connecting..." ? "yellow" : "red"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: engineController.connectionStatus
                font.pixelSize: 20
                color: engineController.connectionStatus === "Connected" ? "lime" :
                       engineController.connectionStatus === "Connecting..." ? "yellow" : "red"
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Waiting for OBD-II adapter...\nPlug in ELM327 or check connection"
                font.pixelSize: 14
                color: "gray"
                horizontalAlignment: Text.AlignHCenter
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 10
            }

            Button {
                text: "CONNECT"
                font.pixelSize: 18
                font.bold: true
                Layout.preferredWidth: 200
                Layout.preferredHeight: 60
                Layout.alignment: Qt.AlignHCenter
                Layout.topMargin: 30
                enabled: engineController.connectionStatus !== "Connecting..."

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color: parent.enabled ? (parent.pressed ? "#006600" : "green") : "gray"
                    radius: 5
                }

                onClicked: engineController.attemptConnection()
            }

            Button {
                text: "QUIT"
                font.pixelSize: 14
                Layout.preferredWidth: 150
                Layout.preferredHeight: 40
                Layout.alignment: Qt.AlignHCenter

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color: parent.pressed ? "#990000" : "red"
                    radius: 5
                }

                onClicked: engineController.quit()
            }
        }
    }

    // Dashboard Screen — shown when connected
    Item {
        id: dashboardScreen
        anchors.fill: parent
        visible: !engineController.connected

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // Top status bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                color: "#1a1a1a"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 20
                    spacing: 20

                    Row {
                        spacing: 10

                        Rectangle {
                            width: 12
                            height: 12
                            radius: 6
                            color: engineController.connected ? "lime" : "red"
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        Text {
                            text: "OBD"
                            font.pixelSize: 12
                            font.bold: true
                            color: engineController.connected ? "lime" : "red"
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: ["ENGINE", "MEDIA", "NAVIGATION", "CAMERA"][tabBar.currentIndex]
                        font.pixelSize: 18
                        font.bold: true
                        color: "cyan"
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        id: clockText
                        font.pixelSize: 16
                        font.bold: true
                        color: "white"

                        Timer {
                            interval: 1000
                            running: true
                            repeat: true
                            onTriggered: {
                                var now = new Date()
                                clockText.text = Qt.formatTime(now, "hh:mm:ss")
                            }
                            Component.onCompleted: triggered()
                        }
                    }
                }
            }

            // Main content area
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                EngineView {
                    anchors.fill: parent
                    visible: tabBar.currentIndex === 0
                }

                MediaView {
                    anchors.fill: parent
                    visible: tabBar.currentIndex === 1
                    controller: musicController
                }

                NavigationView {
                    id: navigationView
                    anchors.fill: parent
                    visible: tabBar.currentIndex === 2
                    controller: navigationController
                }

                Rectangle {
                    anchors.fill: parent
                    visible: tabBar.currentIndex === 3
                    color: "black"
                    Text {
                        anchors.centerIn: parent
                        text: "CAMERA\n(Coming Soon)"
                        font.pixelSize: 32
                        color: "gray"
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                DeviceView {
                    anchors.fill: parent
                    visible: deviceController.showDeviceView
                    z: 1
                }
            }

            // Bottom tab bar
            Rectangle {
                id: tabBar
                Layout.fillWidth: true
                Layout.preferredHeight: 70
                color: "#0d0d0d"

                property int currentIndex: 0

                RowLayout {
                    anchors.fill: parent
                    spacing: 0

                    TabButton {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        icon: "🔧"
                        label: "ENGINE"
                        active: tabBar.currentIndex === 0
                        onClicked: tabBar.currentIndex = 0
                    }

                    TabButton {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        icon: "🎵"
                        label: "MEDIA"
                        active: tabBar.currentIndex === 1
                        onClicked: tabBar.currentIndex = 1
                    }

                    TabButton {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        icon: "🗺️"
                        label: "NAV"
                        active: tabBar.currentIndex === 2
                        onClicked: tabBar.currentIndex = 2
                    }

                    TabButton {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        icon: "📷"
                        label: "CAMERA"
                        active: tabBar.currentIndex === 3
                        onClicked: tabBar.currentIndex = 3
                    }
                }
            }
        }
    }
}
