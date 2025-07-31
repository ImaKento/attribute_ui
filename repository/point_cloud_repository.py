# repository/point_cloud_repository.py

import open3d as o3d
from domain.repository.point_cloud_repository import IPointCloudRepository

class PointCloudRepository(IPointCloudRepository):
    def load(self, path: str) -> o3d.geometry.PointCloud:
        return o3d.io.read_point_cloud(path)
    
    def save(self, path: str, pcd): 
        o3d.io.write_point_cloud(path, pcd)