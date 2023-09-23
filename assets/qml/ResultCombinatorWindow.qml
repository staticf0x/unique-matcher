import QtCore
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import Qt.labs.qmlmodels
import ResultCombinator

Window {
    width: 854
    height: 480
    title: "Combine results"
    color: "#faf9f8"

    ResultCombinator {
        id: resultCombinator

        property var files;

        onResultsLoaded: (files) => {
            this.files = files;

            for (var i = 0; i < files.length; i++) {
                fileList.model.appendRow({"n": files[i].n, "file": files[i].file});
            }
        }

        onPreviewLoaded: (items) => {
            if (previewTable.model.rows.length > 1) {
                previewTable.model.removeRow(1, previewTable.model.rows.length - 1);
            }

            for (var i = 0; i < items.length; i++) {
                previewTable.model.appendRow(items[i]);
            }
        }

        onCombinedChanged: (items) => {
            if (combinedTable.model.rows.length > 1) {
                combinedTable.model.removeRow(1, combinedTable.model.rows.length - 1);
            }

            for (var i = 0; i < items.length; i++) {
                combinedTable.model.appendRow(items[i]);
            }
        }

        Component.onCompleted: {
            resultCombinator.load_results();
        }

        function getCheckedFiles() {
            var file_names = [];

            for (var i = 0; i < resultCombinator.files.length; i++) {
                if (resultCombinator.files[i].checked) {
                    file_names.push(resultCombinator.files[i].file);
                }
            }

            return file_names;
        }
    }

    Dialog {
        id: noFileSelectedDialog
        title: "No file selected"
        standardButtons: Dialog.Ok
        modal: true
        anchors.centerIn: parent

        Text {
            text: "Select at least one CSV to be combined."
        }
    }

    FileDialog {
        id: saveCombinedDialog
        fileMode: FileDialog.SaveFile

        currentFolder: StandardPaths.standardLocations(StandardPaths.DocumentsLocation)[0]
        defaultSuffix: "csv"
        selectedFile: currentFolder + "/combined.csv"
        nameFilters: ["CSV files (*.csv)"]

        onAccepted: {
            resultCombinator.save_combined(resultCombinator.getCheckedFiles(), selectedFile);
        }
    }

    Rectangle {
        id: fileListWrapper
        width: 250
        height: parent.height

        Text {
            id: tableLabel
            text: "Results:"
        }

        Rectangle {
            width: parent.width
            anchors.top: tableLabel.bottom
            anchors.bottom: parent.bottom

            ScrollView {
                anchors.fill: parent

                TableView {
                    id: fileList
                    boundsBehavior: Flickable.StopAtBounds

                    clip: true
                    reuseItems: false
                    anchors.fill: parent

                    property int previewRow;

                    model: TableModel {
                        TableModelColumn { display: "n" }
                        TableModelColumn { display: "file" }

                        rows: [
                            {"n": 0, "file": "File"},
                        ]
                    }

                    delegate: Rectangle {
                        implicitWidth: column == 0 ? 50 : 200
                        implicitHeight: 24
                        border.width: 1
                        color: getRowColor(row)

                        CheckBox {
                            visible: column == 0
                            anchors.centerIn: parent
                            checked: getChecked(row)

                            onToggled: {
                                if (row == 0) {
                                    setCheckedAll(checked);
                                } else {
                                    filePreview(row);
                                    setChecked(row);
                                    resetColors();
                                }
                            }
                        }

                        Text {
                            visible: column == 1
                            text: display
                            anchors.centerIn: parent
                            font.bold: row == 0
                        }

                        MouseArea {
                            enabled: column == 1
                            anchors.fill: parent
                            propagateComposedEvents: true
                            onClicked: (mouse) => {
                                filePreview(row);
                                resetColors();
                            }
                        }
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.left: fileListWrapper.right
        anchors.leftMargin: 8
        anchors.right: parent.right
        anchors.bottom: exportButton.top
        anchors.bottomMargin: exportButton.height
        anchors.top: parent.top

        RowLayout {
            anchors.fill: parent

            Rectangle {
                Layout.alignment: Qt.AlignTop

                Text {
                    id: previewLabel
                    text: "Preview:"
                }

                Rectangle {
                    width: 300
                    height: parent.parent.height
                    anchors.top: previewLabel.bottom

                    ScrollView {
                        anchors.fill: parent

                        TableView {
                            id: previewTable
                            boundsBehavior: Flickable.StopAtBounds

                            clip: true
                            reuseItems: false
                            anchors.fill: parent

                            model: TableModel {
                                TableModelColumn { display: "item" }
                                TableModelColumn { display: "count" }

                                rows: [
                                    {"item": "Item", "count": "Count"},
                                ]
                            }

                            delegate: Rectangle {
                                implicitWidth: column == 0 ? 220 : 72
                                implicitHeight: 24
                                border.width: 1

                                Text {
                                    text: display
                                    anchors.centerIn: parent
                                    font.bold: row == 0
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.alignment: Qt.AlignTop

                Text {
                    id: combinedLabel
                    text: "Combined:"
                }

                Rectangle {
                    width: 300
                    height: parent.parent.height
                    anchors.top: combinedLabel.bottom

                    ScrollView {
                        anchors.fill: parent

                        TableView {
                            id: combinedTable
                            boundsBehavior: Flickable.StopAtBounds

                            clip: true
                            reuseItems: false
                            anchors.fill: parent

                            model: TableModel {
                                TableModelColumn { display: "item" }
                                TableModelColumn { display: "count" }

                                rows: [
                                    {"item": "Item", "count": "Count"},
                                ]
                            }

                            delegate: Rectangle {
                                implicitWidth: column == 0 ? 220 : 72
                                implicitHeight: 24
                                border.width: 1

                                Text {
                                    text: display
                                    anchors.centerIn: parent
                                    font.bold: row == 0
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    Button {
        id: exportButton
        text: "Save combined"

        anchors.bottom: parent.bottom
        anchors.right: parent.right
        anchors.bottomMargin: 2
        anchors.rightMargin: 2

        onClicked: {
            if (resultCombinator.getCheckedFiles().length > 0) {
                saveCombinedDialog.open();
            } else {
                noFileSelectedDialog.open();
            }
        }
    }

    function resetColors() {
        for (var row = 1; row < fileList.rows; row++) {
            var checkbox_cell = fileList.itemAtIndex(fileList.index(row, 0));
            var file_cell = fileList.itemAtIndex(fileList.index(row, 1));

            if (checkbox_cell == null) {
                continue;
            }

            var color = row == fileList.previewRow ? "#d9f0fc" : getRowColor(row);

            checkbox_cell.color = color;
            file_cell.color = color;
        }
    }

    function filePreview(row) {
        fileList.previewRow = row;

        var file = resultCombinator.files[row - 1];

        resultCombinator.load_preview(file.file);
    }

    function getRowColor(row) {
        if (row == 0) {
            return "white";
        }

        return getChecked(row) ? "#ddfcd9" : "white";
    }

    function getChecked(row) {
        if (row == 0) {
            return false;
        }

        return resultCombinator.files[row - 1]["checked"] == true;
    }

    function setChecked(row) {
        resultCombinator.files[row - 1]["checked"] = !resultCombinator.files[row - 1]["checked"];
        resultCombinator.combine_results(resultCombinator.getCheckedFiles());
    }

    function setCheckedAll(checked) {
        for (var row = 1; row < fileList.rows; row++) {
            resultCombinator.files[row - 1]["checked"] = checked;
            var checkbox_cell = fileList.itemAtIndex(fileList.index(row, 0));
            checkbox_cell.children[0].checked = checked;
        }

        resultCombinator.combine_results(resultCombinator.getCheckedFiles());
        resetColors();
    }
}
