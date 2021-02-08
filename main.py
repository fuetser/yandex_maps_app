import math
import sys

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
import requests


MAP_LAYOUT_TYPES = {
    "Схема": "map",
    "Спутник": "sat",
    "Гибрид": "sat,skl"
}


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.current_zoom = 12  # [1; 17]
        self.current_longitude = 37.91
        self.current_latitude = 59.13
        self.current_mark = None
        self.current_address = None
        self.current_postal_code = None
        self.show_postal_code = False
        self.map_layout_type = "map"
        self.static_server = "http://static-maps.yandex.ru/1.x/"
        self.geocode_server = "http://geocode-maps.yandex.ru/1.x/"
        self.orgs_server = "https://search-maps.yandex.ru/v1/"
        self.apikey = "40d1649f-0493-4b70-98ba-98533de7710b"
        self.orgs_apikey = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"
        self.organizations = ("магазин", "аптека", "банк", "кафе", "ресторан",
                              "споривный зал", "авто", "стадион", "рынок")
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Yandex Maps")
        self.main_layout = QtWidgets.QVBoxLayout(self)

        self.map_layout_box = QtWidgets.QComboBox(self)
        self.map_layout_box.textActivated.connect(
            self.change_map_layout_type)
        self.map_layout_box.addItems(MAP_LAYOUT_TYPES.keys())
        self.main_layout.addWidget(self.map_layout_box)

        self.map_lable = QtWidgets.QLabel(self)
        self.main_layout.addWidget(self.map_lable)
        self.update_map()

        search_button = QtWidgets.QPushButton("Искать", self)
        search_button.clicked.connect(self.search_place)
        reset_search_button = QtWidgets.QPushButton("Сброс", self)
        reset_search_button.clicked.connect(self.remove_mark)

        self.geocode_field = QtWidgets.QLineEdit(self)

        search_layout = QtWidgets.QHBoxLayout()
        search_layout.addWidget(search_button)
        search_layout.addWidget(reset_search_button)
        search_layout.addWidget(self.geocode_field)
        self.main_layout.addLayout(search_layout)

        self.address_field = QtWidgets.QLineEdit()
        self.address_field.setReadOnly(True)

        self.postal_code_button = QtWidgets.QRadioButton("Индекс")
        self.postal_code_button.toggled.connect(self.postal_button_change)

        address_layout = QtWidgets.QHBoxLayout()
        address_layout.addWidget(self.address_field)
        address_layout.addWidget(self.postal_code_button)
        self.main_layout.addLayout(address_layout)

    def change_map_layout_type(self, map_layout_type):
        self.map_layout_type = MAP_LAYOUT_TYPES[map_layout_type]
        self.update_map()

    def update_map(self):
        self.set_map(self.get_map())
        self.setFocus()

    def remove_mark(self):
        self.current_mark = None
        self.address_field.clear()
        self.update_map()

    def postal_button_change(self, show_postal_code):
        self.show_postal_code = show_postal_code
        self.address_field.setText(self.format_address())

    def get_map(self):
        payload = {
            "ll": f"{self.current_longitude},{self.current_latitude}",
            "l": self.map_layout_type,
            "z": str(self.current_zoom),
        }
        if self.current_mark is not None:
            payload["pt"] = "{},{},pm2dom".format(*self.current_mark)

        response = requests.get(self.static_server, params=payload)
        if response.ok:
            return response.content

    def set_map(self, image_bytes):
        image = QtGui.QPixmap()
        image.loadFromData(image_bytes)
        self.map_lable.setPixmap(image)

    def search_place(self, from_mark=False):
        if from_mark:
            geocode = "{},{}".format(*self.current_mark)
        else:
            geocode = self.geocode_field.text().strip()

        if geocode:
            self.current_mark, self.current_address, \
                self.current_postal_code = self.parse_geocode(geocode)
            self.address_field.setText(self.format_address())
            if self.current_mark is not None and not from_mark:
                self.current_longitude, self.current_latitude = self.current_mark
            self.update_map()

    def parse_geocode(self, geocode):
        try:
            payload = {
                "apikey": self.apikey,
                "geocode": geocode,
                "format": "json",
            }
            response = requests.get(self.geocode_server, params=payload).json()
            geobject = response["response"][
                "GeoObjectCollection"]["featureMember"][0]["GeoObject"]
            pos = tuple(map(float, geobject["Point"]["pos"].split()))
            metadata = geobject["metaDataProperty"]["GeocoderMetaData"]
            address = metadata["text"]
            postal_code = metadata["Address"].get("postal_code")
            return pos, address, postal_code

        except Exception:
            return self.current_mark, "Не найдено", None

    def format_address(self):
        if self.show_postal_code and self.current_postal_code is not None:
            return f"{self.current_address}, {self.current_postal_code}"
        return self.current_address

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

    def mousePressEvent(self, event):
        if (button := event.button()) == Qt.LeftButton:
            self.mark_mouse_click(
                event.pos().x() - self.map_lable.x(),
                event.pos().y() - self.map_lable.y())
            self.search_place(from_mark=True)
        elif button == Qt.RightButton:
            self.find_organizations(
                event.pos().x() - self.map_lable.x(),
                event.pos().y() - self.map_lable.y())

    def find_click_coords(self, x, y):
        center_x = self.map_lable.width() // 2
        center_y = self.map_lable.height() // 2
        fov_x = (360 / 2 ** self.current_zoom)
        fov_y = (180 / 2 ** self.current_zoom)
        x_shift = (x - center_x) * 0.44 * fov_x / 111
        y_shift = (y - center_y) * 0.44 * fov_y / 111
        return (self.current_longitude + x_shift,
                self.current_latitude - y_shift)

    def mark_mouse_click(self, x, y):
        self.current_mark = self.find_click_coords(x, y)
        self.update_map()

    def find_organizations(self, x, y):
        lon, lat = self.find_click_coords(x, y)
        for org in self.organizations:
            payload = {
                "apikey": self.orgs_apikey,
                "text": org,
                "ll": f"{lon},{lat}",
                "lang": "ru_RU",
                "type": "biz",
                "spn": "0.0009,0.0009",
                "rspn": "1"
            }
            response = requests.get(self.orgs_server, params=payload)
            if response.ok and len((data := response.json())["features"]):
                self.parse_organizations(data)
                break

    def parse_organizations(self, data):
        props = data["features"][0]["properties"]
        self.address_field.setText(f"{props['name']}, {props['description']}")
        self.current_address = f"{props['name']}, {props['description']}"
        self.current_postal_code = None

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
