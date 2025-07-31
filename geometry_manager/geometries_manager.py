from PyQt5.QtCore import QObject, pyqtSignal

class GeometryItem:
    def __init__(self, name: str, data, geometry_type: str, file_path: str = None):
        self.name = name
        self.data = data
        self.geometry_type = geometry_type
        self.file_path = file_path
        self.visible = True
        self.selected = False

class GeometryManager(QObject):
    updated = pyqtSignal()
    selection_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.items: list[GeometryItem] = []

    def add(self, name: str, data, geometry_type: str, file_path: str = None):
        self.items.append(GeometryItem(name, data, geometry_type, file_path))
        self.updated.emit()

    def select(self, name: str):
        selection_changed = False
        for item in self.items:
            new_selected = (item.name == name)
            if item.selected != new_selected:
                selection_changed = True
            item.selected = new_selected
        
        if selection_changed:
            self.selection_changed.emit()

    def set_visibility(self, name: str, visible: bool):
        for item in self.items:
            if item.name == name:
                item.visible = visible     
        self.updated.emit()

    def get_visible_items(self):
        return [item for item in self.items if item.visible]

    def get_selected_items(self):
        return [item for item in self.items if item.selected]