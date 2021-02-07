import sys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
import requests


MAP_LAYOUT_TYPES = {
    "схема": "map",
    "спутник": "sat",
    "гибрид": "sat,skl"
}


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_zoom = 12  # [1; 17]
        self.current_longitude = 37.91
        self.current_latitude = 59.13
        self.map_layout_type = "map"
        self.server = "http://static-maps.yandex.ru/1.x/"
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yandex Maps")
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.map_layout_box = QtWidgets.QComboBox()
        self.map_layout_box.textActivated.connect(
            self.change_map_layout_type)
        self.map_layout_box.addItems(MAP_LAYOUT_TYPES.keys())
        self.main_layout.addWidget(self.map_layout_box)

        self.map_lable = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.map_lable)
        self.update_map()

    def change_map_layout_type(self, map_layout_type):
        self.map_layout_type = MAP_LAYOUT_TYPES[map_layout_type]
        self.update_map()

    def update_map(self):
        self.set_map(self.get_map())
        self.setFocus()

    def get_map(self):
        payload = {
            "ll": f"{self.current_longitude},{self.current_latitude}",
            "l": self.map_layout_type,
            "z": str(self.current_zoom),
        }
        responce = requests.get(self.server, params=payload)
        if responce.ok:
            return responce.content

    def set_map(self, image_bytes):
        image = QtGui.QPixmap()
        image.loadFromData(image_bytes)
        self.map_lable.setPixmap(image)

    def keyPressEvent(self, event):
        if (key := event.key()) == Qt.Key_PageUp:
            self.change_zoom(+1)
        elif key == Qt.Key_PageDown:
            self.change_zoom(-1)
        elif key == Qt.Key_Left:
            self.move_center(-self.move_delta, 0)
        elif key == Qt.Key_Right:
            self.move_center(+self.move_delta, 0)
        elif key == Qt.Key_Up:
            self.move_center(0, +self.move_delta / 2)
        elif key == Qt.Key_Down:
            self.move_center(0, -self.move_delta / 2)

    def change_zoom(self, delta):
        if 1 <= self.current_zoom + delta <= 17:
            self.current_zoom += delta
            self.update_map()

    @property
    def move_delta(self):
        return 0.001 * (18 - self.current_zoom) ** 2

    def move_center(self, x_shift, y_shift):
        if (
            -180 <= self.current_longitude + x_shift <= 180 and
            -90 <= self.current_latitude + y_shift <= 90
        ):
            self.current_longitude += x_shift
            self.current_latitude += y_shift
            self.update_map()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
