from abc import ABC, abstractmethod
import open3d as o3d

class IPointCloudRepository(ABC):
    @abstractmethod
    def load(self, path: str) -> o3d.geometry.PointCloud:
        pass

    @abstractmethod
    def save(self, path: str, pcd: o3d.geometry.PointCloud):
        pass
