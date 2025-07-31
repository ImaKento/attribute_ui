# usecase/io/load_point_cloude_usecase.py

import os

from geometry_manager.geometries_manager import GeometryManager
from domain.repository.point_cloud_repository import IPointCloudRepository

class LoadPointCloudUsecase():
    def __init__(self, geometry_manager: GeometryManager, point_cloud_repository: IPointCloudRepository):
        self.geometry_manager = geometry_manager
        self.point_cloud_repository = point_cloud_repository

    def exec(self, file_path: str):
        pcd =  self.point_cloud_repository.load(file_path)
        name = os.path.basename(file_path)
        self.geometry_manager.add(name, pcd, "pointcloud")
        