from PyQt5.QtCore import QObject, pyqtSignal

class GeometryItem:
    def __init__(self, name: str, data, geometry_type: str):
        self.name = name
        self.data = data
        self.geometry_type = geometry_type
        self.visible = True
        self.selected = False

class GeometryManager(QObject):
    updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.items: list[GeometryItem] = []

    def add(self, name: str, data, geometry_type: str):
        self.items.append(GeometryItem(name, data, geometry_type))
        self.updated.emit()

    def select(self, name: str):
        for item in self.items:
            item.selected = (item.name == name)

    def set_visibility(self, name: str, visible: bool):
        for item in self.items:
            if item.name == name:
                item.visible = visible     
        self.updated.emit()

    def get_visible_items(self):
        return [item for item in self.items if item.visible]

    def get_selected_items(self):
        return [item for item in self.items if item.selected]