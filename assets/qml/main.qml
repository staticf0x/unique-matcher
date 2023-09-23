import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels
import Matcher
import Utils
import Config

ApplicationWindow {
    id: mainWindow
    width: 854
    height: 480
    visible: true
    title: "Unique Matcher v" + VERSION
    menuBar: mainMenu

    property variant window;

    Matcher {
        id: matcher

        onNewResult: (value) => {
            resultsTable.model.appendRow(value);

            if (resultsTable.contentHeight > resultsTable.height) {
                resultsTable.contentY = resultsTable.contentHeight - resultsTable.height + 24;
            }
        }
    }

    Config {
        id: config

        onShortcutLoaded: function(mod_key, key) {
            shortcutPicker.loadCurrent(mod_key, key);
        }
    }

    Utils {
        id: utils
    }

    ResultCombinatorWindow {
        id: resultCombinatorWindow
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
            clearResults();
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
            clearResults();
        }
    }


    Dialog {
        id: confirmZipDialog
        title: "Create test data set"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        Text {
            text: "This will create a ZIP file with all the processed screenshots for\n"
                + "the developer to improve accuracy of the detection algorithm.\n\n"
                + "You can then upload it to your Google Drive, Dropbox, One Drive or similar\n"
                + "and send it either via #tooldev-chat on Prohibited Library's Discord server\n"
                + "or to the GitHub repository."
        }

        onAccepted: {
            utils.zip_done();
        }
    }

    Dialog {
        id: shortcutPicker
        title: "Choose screenshot shortcut"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        anchors.centerIn: parent

        ColumnLayout {
            RowLayout {
                ComboBox {
                    id: modKeyPicker
                    model: ["None", "Ctrl", "Alt", "Shift", "Win"]
                }

                Text {
                    text: "+"
                }

                ComboBox {
                    id: keyPicker
                    model: [
                        "MouseL",
                        "MouseM",
                        "MouseR",
                        "Mouse4",
                        "Mouse5",
                        "Enter",
                        "Tab",
                        "CapsLock",
                        "F1",
                        "F2",
                        "F3",
                        "F4",
                        "F5",
                        "F6",
                        "F7",
                        "F8",
                        "F9",
                        "F10",
                        "F11",
                        "F12",
                        "A", "B", "C", "D", "E", "F", "G", "H",
                        "I", "J", "K", "L", "M", "N", "O", "P",
                        "Q", "R", "S", "T", "U", "V", "W", "X",
                        "Y", "Z"]
                }
            }

            CheckBox {
                id: restartAHKCheckBox
                checked: true
                text: "Restart AHK script"
            }

            Text {
                text: "Note: this will overwrite your screenshot.ahk"
            }
        }

        onAccepted: {
            var modKey = modKeyPicker.currentText;
            var key = keyPicker.currentText;

            config.change_shortcut(modKey, key);

            if (restartAHKCheckBox.checked) {
                config.restart_ahk();
            }
        }

        function loadCurrent(mod_key, key) {
            modKeyPicker.currentIndex = modKeyPicker.find(mod_key);
            keyPicker.currentIndex = keyPicker.find(key);
        }
    }

    MenuBar {
        id: mainMenu

        Menu {
            id: fileMenu
            title: "&File"

            Action {
                text: "Start AHK script"
                onTriggered: {
                    config.restart_ahk();
                }
            }

            MenuSeparator {}

            Action {
                text: "&Exit"
                onTriggered: {
                    Qt.callLater(Qt.quit);
                }
            }
        }

        Menu {
            id: editMenu
            title: "&Edit"

            Action {
                text: "&Change screenshot shortcut"
                onTriggered: {
                    config.load_current();
                    shortcutPicker.open();
                }
            }
        }

        Menu {
            id: resultsMenu
            title: "&Results"

            Action {
                text: "&Open CSV"
                onTriggered: {
                    utils.open_csv();
                }
            }

            Action {
                text: "&Combine CSVs"
                onTriggered: {
                    resultCombinatorWindow.show();
                }
            }

            MenuSeparator {}

            Action {
                text: "Show results"
                onTriggered: {
                    utils.open_folder("results");
                }
            }

            Action {
                text: "Show processed screenshots"
                onTriggered: {
                    utils.open_folder("done");
                }
            }

            Action {
                text: "Show error screenshots"
                onTriggered: {
                    utils.open_folder("errors");
                }
            }

            MenuSeparator {}

            Action {
                text: "Create snapshot"
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
                text: "Usage guide"
                shortcut: "F1"
                onTriggered: {
                    utils.open_help();
                }
            }

            Action {
                text: "Report issue"
                onTriggered: {
                    utils.report_issue();
                }
            }

            MenuSeparator {}

            Action {
                text: "Show logs"
                onTriggered: {
                    utils.open_folder("logs");
                }
            }

            Action {
                text: "Create test data set"
                onTriggered: {
                    confirmZipDialog.open();
                }
            }

            MenuSeparator {}

            Action {
                text: "Changelog"
                onTriggered: {
                    utils.open_changelog();
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
            id: titleRow
            width: mainWindow.width

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
            height: mainWindow.height - 100

            ScrollView {
                anchors.fill: parent

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
                            font.bold: row == 0
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

    function clearResults() {
        if (resultsTable.model.rows.length > 1) {
            resultsTable.model.removeRow(1, resultsTable.model.rows.length - 1);
        }
    }
}
