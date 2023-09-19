import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels
import Matcher
import Utils

ApplicationWindow {
    id: mainWindow
    width: 854
    height: 480
    visible: true
    title: "Unique Matcher v" + VERSION
    menuBar: mainMenu

    Matcher {
        id: matcher

        onNewResult: (value) => {
            resultsTable.model.appendRow(value);

            if (resultsTable.contentHeight > resultsTable.height) {
                resultsTable.contentY = resultsTable.contentHeight - resultsTable.height + 24;
            }
        }
    }

    Utils {
        id: utils
    }

    Dialog {
        id: confirmClearDialog
        title: "Clear results?"
        standardButtons: Dialog.Yes | Dialog.No
        modal: true
        anchors.centerIn: parent

        Text {
            text: "This will not erase the CSV file, only the displayed table."
        }

        onAccepted: {
            resultsTable.model.removeRow(1, resultsTable.model.rows.length - 1);
        }
    }

    Dialog {
        id: confirmSnapshotDialog
        title: "Create snapshot?"
        standardButtons: Dialog.Yes | Dialog.No
        modal: true
        anchors.centerIn: parent

        Text {
            text: "This will start writing results in a new CSV file\nand clear the results table."
        }

        onAccepted: {
            matcher.snapshot();
            resultsTable.model.removeRow(1, resultsTable.model.rows.length - 1);
        }
    }

    MenuBar {
        id: mainMenu

        Menu {
            id: fileMenu
            title: "&File"

            Action {
                text: "&Exit"
                onTriggered: {
                    Qt.callLater(Qt.quit);
                }
            }
        }

        Menu {
            id: resultsMenu
            title: "&Results"

            Action {
                text: "&Create snapshot"
                onTriggered: {
                    confirmSnapshotDialog.open();
                }
            }

            Action {
                text: "Clear results"
                onTriggered: {
                    confirmClearDialog.open();
                }
            }
        }

        Menu {
            id: helpMenu
            title: "&Help"

            Action {
                text: "How to use"
                shortcut: "F1"
                onTriggered: {
                    utils.open_help();
                }
            }
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
                    confirmSnapshotDialog.open();
                }
            }
        }

        Rectangle {
            border.width: 1
            width: mainWindow.width
            height: 350

            ScrollView {
                width: parent.width
                height: parent.height

                TableView {
                    id: resultsTable
                    Layout.alignment: Qt.AlignHCenter
                    boundsBehavior: Flickable.StopAtBounds

                    clip: true
                    anchors.fill: parent

                    model: TableModel {
                        TableModelColumn { display: "n" }
                        TableModelColumn { display: "item" }
                        TableModelColumn { display: "base" }
                        TableModelColumn { display: "matched_by" }

                        rows: [
                            {
                                "n": "#",
                                "item": "Item",
                                "base": "Base",
                                "matched_by": "Matched by",
                            },
                        ]
                    }

                    delegate: Rectangle {
                        implicitWidth: getColumnWidth(column)
                        implicitHeight: 24
                        border.width: 1

                        Text {
                            text: display
                            anchors.centerIn: parent
                            font.bold: row == 0 ? true : false
                            color: isRowError(row) ? "red" : "black"
                        }
                    }
                }
            }
        }
    }

    function getColumnWidth(col) {
        switch (col) {
            case 0: return 50;
            case 1: return 220;
            case 2: return 180;
            case 3: return 220;
            default: return 180;
        }
    }

    function isRowError(row) {
        if (resultsTable.model.rows.length == 0) {
            return false;
        }

        return resultsTable.model.rows[row].item == "Error"
    }
}
