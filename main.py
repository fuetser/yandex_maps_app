import sys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
import requests


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
        self.map_lable = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.map_lable)
        self.update_map()

    def update_map(self):
        self.set_map(self.get_map())

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

    def change_zoom(self, delta):
        if 1 <= self.current_zoom + delta <= 17:
            self.current_zoom += delta
            self.update_map()

    def keyPressEvent(self, event):
        if (key := event.key()) == Qt.Key_PageUp:
            self.change_zoom(+1)
        elif key == Qt.Key_PageDown:
            self.change_zoom(-1)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
