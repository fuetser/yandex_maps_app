from PyQt5 import QtWidgets, QtGui
import requests
import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_zoom = 12  # [1; 17]
        self.current_longitude = 39
        self.current_latitude = 59
        self.map_layout = "map"
        self.server = "http://static-maps.yandex.ru/1.x/"
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.map_lable = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.map_lable)
        self.set_map(self.get_map())
        self.setWindowTitle("Yandex Maps")

    def get_map(self):
        payload = {
            "ll": ",".join(map(
                str, (self.current_longitude, self.current_latitude))),
            "l": self.map_layout,
            "z": str(self.current_zoom),
        }
        responce = requests.get(self.server, params=payload)
        if responce.ok:
            return responce.content

    def set_map(self, bytes_io):
        image = QtGui.QPixmap()
        image.loadFromData(bytes_io)
        self.map_lable.setPixmap(image)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
