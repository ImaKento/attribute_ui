from abc import ABC, abstractmethod
import open3d as o3d

class IModelRepository(ABC):
    @abstractmethod
    def load(self, path: str) -> o3d.geometry.TriangleMesh:
        pass

    @abstractmethod
    def load_obj(self, obj_file_path: str):
        pass
    
    @abstractmethod
    def load_texture(self, texture_file_path: str):
        pass


    @abstractmethod
    def save(self, path: str, mesh: o3d.geometry.TriangleMesh):
        pass

    @abstractmethod
    def Tpillar_generate_parametric_model(self, dist_list):
        pass