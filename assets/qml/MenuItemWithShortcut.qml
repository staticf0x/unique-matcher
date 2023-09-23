import QtQuick
import QtQuick.Controls

MenuItem {
    id: control

    contentItem: Item {
        anchors.centerIn: parent

        Text {
            text: control.text
            anchors.left: parent.left
        }

        Text {
            text: control.action.shortcut ?? ""
            anchors.right: parent.right
        }
    }
}
