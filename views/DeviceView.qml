import QtQuick 2.15
import QtQuick.Layouts 2.15
import QtQuick.Controls 2.15

Item {
    id: root

    Rectangle {
        anchors.fill: parent
        color: "#121212"

        // Close button — top left
        Button {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: 16
            flat: true
            width: 100
            height: 40

            contentItem: Text {
                text: "← BACK"
                font.pixelSize: 14
                font.bold: true
                color: "#888888"
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }

            background: Rectangle { color: "transparent" }
            onClicked: deviceController.closeDeviceView()
        }

        // Center content
        ColumnLayout {
            anchors.centerIn: parent
            spacing: 16
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Look for '" + deviceController.adapterName + "' in Bluetooth settings"
                font.pixelSize: 13
                color: "#555555"
                visible: !deviceController.hasConnectedDevice
            }
            Image {
                Layout.alignment: Qt.AlignHCenter
                source: root.iconForType(
                    deviceController.hasConnectedDevice ? deviceController.deviceType : "")
                width: 72
                height: 72
                fillMode: Image.PreserveAspectFit
                opacity: deviceController.hasConnectedDevice ? 1.0 : 0.3
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: deviceController.hasConnectedDevice
                      ? deviceController.deviceName
                      : "No Device Connected"
                font.pixelSize: 26
                font.bold: true
                color: "#ffffff"
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: deviceController.deviceAddress
                font.pixelSize: 13
                color: "#666666"
                font.family: "monospace"
                visible: deviceController.hasConnectedDevice
            }

            Item { Layout.preferredHeight: 16 }

            Button {
                Layout.alignment: Qt.AlignHCenter
                visible: deviceController.hasConnectedDevice
                implicitWidth: 200
                implicitHeight: 52

                contentItem: Text {
                    text: "DISCONNECT"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                background: Rectangle {
                    color: parent.pressed ? "#990000" : "#cc0000"
                    radius: 4
                }

                onClicked: deviceController.disconnectDevice()
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "Pair from your device's Bluetooth settings"
                font.pixelSize: 13
                color: "#555555"
                visible: !deviceController.hasConnectedDevice
            }
        }
    }

    function iconForType(type) {
        if (type === "phone") return "../assets/icons/phone.svg"
        if (type && type.indexOf("audio") !== -1) return "../assets/icons/headphones.svg"
        if (type === "computer") return "../assets/icons/laptop.svg"
        return "../assets/icons/bluetooth.svg"
    }
}
