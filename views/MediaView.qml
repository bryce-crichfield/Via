import QtQuick 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls 2.15

Item {
    id: root

    required property var controller

    // Background album art with darkening overlay
    Rectangle {
        anchors.fill: parent
        color: "#1a1a1a"

        Image {
            anchors.fill: parent
            source: controller.albumArtUrl
            fillMode: Image.PreserveAspectCrop
            visible: controller.albumArtUrl !== ""
            opacity: 0.3
        }

        Rectangle {
            anchors.fill: parent
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#aa000000" }
                GradientStop { position: 1.0; color: "#dd000000" }
            }
        }
    }

    Item {
        anchors.fill: parent
        anchors.margins: 20

        // Track info — left half
        ColumnLayout {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.right: parent.horizontalCenter
            anchors.rightMargin: 40
            spacing: 4

            Text {
                Layout.fillWidth: true
                text: controller.trackTitle
                font.pixelSize: 24
                font.bold: true
                color: "#ffffff"
                elide: Text.ElideRight
                style: Text.Outline
                styleColor: "#000000"
            }

            Text {
                Layout.fillWidth: true
                text: controller.artistName
                font.pixelSize: 18
                color: "#e0e0e0"
                elide: Text.ElideRight
                visible: controller.artistName !== ""
                style: Text.Outline
                styleColor: "#000000"
            }

            Text {
                Layout.fillWidth: true
                text: controller.albumName
                font.pixelSize: 14
                color: "#c0c0c0"
                elide: Text.ElideRight
                visible: controller.albumName !== ""
                style: Text.Outline
                styleColor: "#000000"
            }
        }

        // Playback controls — right side, vertically centered
        RowLayout {
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: -30
            spacing: 24

            Button {
                flat: true
                text: "⏮"
                font.pixelSize: 28
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle { color: "transparent" }
                onClicked: controller.previousRequested()
            }

            Button {
                flat: true
                text: controller.isPlaying ? "⏸" : "▶"
                font.pixelSize: 36
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "cyan"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle { color: "transparent" }
                onClicked: controller.playPauseRequested()
            }

            Button {
                flat: true
                text: "⏭"
                font.pixelSize: 28
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "white"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle { color: "transparent" }
                onClicked: controller.nextRequested()
            }
        }

        // Progress bar + timestamps — bottom
        ColumnLayout {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            spacing: 6

            RowLayout {
                Layout.fillWidth: true

                Text {
                    text: formatTime(controller.currentTime)
                    font.pixelSize: 12
                    color: "#aaaaaa"
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: formatTime(controller.totalTime)
                    font.pixelSize: 12
                    color: "#aaaaaa"
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 12
                color: "#3a3a3a"
                radius: 6
                border.color: "#555555"
                border.width: 1

                Rectangle {
                    width: parent.width * controller.progress
                    height: parent.height
                    color: "cyan"
                    radius: 6
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: (mouse) => {
                        controller.seekRequested(mouse.x / width)
                    }
                }
            }
        }

        // Bluetooth button — top right
        Button {
            anchors.right: parent.right
            anchors.top: parent.top
            width: 40
            height: 40
            flat: true

            contentItem: Text {
                text: "🔵"
                font.pixelSize: 22
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                opacity: deviceController.hasConnectedDevice ? 1.0 : 0.4
            }

            background: Rectangle { color: "transparent" }

            onClicked: deviceController.toggleDeviceView()
        }
    }

    function formatTime(seconds) {
        var mins = Math.floor(seconds / 60)
        var secs = seconds % 60
        return mins + ":" + (secs < 10 ? "0" : "") + secs
    }
}
