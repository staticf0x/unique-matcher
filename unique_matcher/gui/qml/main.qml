import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels
import Matcher

Window {
    id: mainWindow
    width: 854
    height: 480
    visible: true
    title: "Unique Matcher v" + VERSION

    Matcher {
        id: matcher

        onNewResult: (value) => {
            resultsTable.model.appendRow(value);
        }
    }

    RowLayout {
        id: topRow

        Text {
            id: queueLength
            text: "Screenshots in queue: " + matcher.queue_length
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            id: processedLength
            text: " | Processed: " + matcher.processed_length
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            id: errorsLength
            text: " | Errors: " + matcher.errors_length
            Layout.alignment: Qt.AlignVCenter
        }

        Text {
            id: itemsInDB
            text: " | Items in DB: " + matcher.items
            Layout.alignment: Qt.AlignVCenter
        }
    }

    ColumnLayout {
        id: tableLayout
        anchors.top: topRow.bottom
        anchors.topMargin: 8

        RowLayout {
            Text {
                text: "Results"
                font.bold: true
                font.pointSize: 16
            }

            Item {
                Layout.fillWidth: true
            }

            Button {
                id: exportButton
                text: "Create snapshot"
                onClicked: {
                    matcher.snapshot();
                }
            }
        }

        Rectangle {
            border.width: 1
            width: mainWindow.width
            height: 350

            TableView {
                id: resultsTable
                Layout.alignment: Qt.AlignHCenter

                clip: true
                anchors.fill: parent

                model: TableModel {
                    TableModelColumn { display: "item" }
                    TableModelColumn { display: "base" }
                    TableModelColumn { display: "matched_by" }

                    rows: [
                        {
                            "item": "Item",
                            "base": "Base",
                            "matched_by": "Matched by",
                        },
                    ]
                }

                delegate: Rectangle {
                    implicitWidth: column == 0 || column == 2 ? 220 : 180
                    implicitHeight: 24
                    border.width: 1

                    Text {
                        text: display
                        anchors.centerIn: parent
                        font.bold: row == 0 ? true : false
                    }
                }
            }
        }
    }
}
