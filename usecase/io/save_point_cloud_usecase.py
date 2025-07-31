# usecase/io/save_point_cloude_usecase.py

from geometry_manager.geometries_manager import GeometryManager
from domain.repository.point_cloud_repository import IPointCloudRepository

class SavePointCloudUsecase():
    def __init__(self, geometry_manager: GeometryManager, point_cloud_repository: IPointCloudRepository):
        self.geometry_manager = geometry_manager
        self.point_cloud_repository = point_cloud_repository

    def exec(self, file_path: str, items):
        for item in items:
            if item.geometry_type == 'pointcloud':
                pcd = item.data
                self.point_cloud_repository.save(file_path, pcd)
