import QtQuick
import QtQuick.Layouts

Rectangle {
    id: button
    color: active ? "#2a2a2a" : "#1a1a1a"
    border.color: active ? "cyan" : "#333333"
    border.width: active ? 2 : 1
    
    property string icon: ""
    property string label: ""
    property bool active: false
    signal clicked()
    
    ColumnLayout {
        anchors.centerIn: parent
        spacing: 5
        
        Text {
            text: button.icon
            font.pixelSize: 24
            Layout.alignment: Qt.AlignHCenter
        }
        
        Text {
            text: button.label
            font.pixelSize: 11
            font.bold: true
            color: button.active ? "cyan" : "gray"
            Layout.alignment: Qt.AlignHCenter
        }
    }
    
    MouseArea {
        anchors.fill: parent
        onClicked: button.clicked()
    }
}