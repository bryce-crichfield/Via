import QtQuick 2.15
import QtQuick.Layouts 2.15
import "../components"

Item {
    GridLayout {
        anchors.fill: parent
        anchors.margins: 20
        columns: 3
        rows: 2
        columnSpacing: 10
        rowSpacing: 10

        // RPM — large, spans 2 columns
        DataPanel {
            Layout.columnSpan: 2
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "RPM"
            value: engineController.rpm.toString()
            valueColor: "lime"
            labelSize: 16
            valueSize: 48
        }

        // Speed
        DataPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "SPEED (KPH)"
            value: engineController.speed.toString()
            valueColor: "lime"
            labelSize: 16
            valueSize: 48
        }

        // Coolant Temp
        DataPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "COOLANT"
            value: engineController.coolantTemp
            valueColor: engineController.coolantTemp !== "N/A" &&
                        parseInt(engineController.coolantTemp) > 100 ? "red" : "cyan"
            labelSize: 12
            valueSize: 28
        }

        // Throttle
        DataPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "THROTTLE"
            value: engineController.throttle
            valueColor: "orange"
            labelSize: 12
            valueSize: 28
        }

        // Engine Load
        DataPanel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            label: "LOAD"
            value: engineController.engineLoad
            valueColor: "yellow"
            labelSize: 12
            valueSize: 28
        }
    }
}
