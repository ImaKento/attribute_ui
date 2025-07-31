# usecase/io/save_model_usecase.py

from geometry_manager.geometries_manager import GeometryManager
from domain.repository.model_repository import IModelRepository

class SaveModelUsecase():
    def __init__(self, geometry_manager: GeometryManager, model_repository: IModelRepository):
        self.geometry_manager = geometry_manager
        self.model_repository = model_repository

    def exec(self, file_path: str, items):
        for item in items:
            if item.geometry_type == 'model':
                pcd = item.data
                self.model_repository.save(file_path, pcd)
