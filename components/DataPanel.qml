import QtQuick
import QtQuick.Layouts

Rectangle {
    id: panel
    color: "#1a1a1a"
    border.color: "#333333"
    border.width: 2
    radius: 5
    
    property string label: ""
    property string value: "N/A"
    property color valueColor: "lime"
    property int labelSize: 12
    property int valueSize: 28
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 5
        
        Text {
            text: panel.label
            font.pixelSize: panel.labelSize
            color: "gray"
            Layout.alignment: Qt.AlignHCenter
        }
        
        Text {
            text: panel.value
            font.pixelSize: panel.valueSize
            font.bold: true
            color: panel.valueColor
            Layout.alignment: Qt.AlignHCenter
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}
