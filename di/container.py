from usecase.io.load_point_cloud_usecase import LoadPointCloudUsecase
from usecase.io.save_point_cloud_usecase import SavePointCloudUsecase
from usecase.io.load_model_usecase import LoadModelUsecase
from usecase.io.save_model_usecase import SaveModelUsecase
from usecase.model.generate_parametric_model_usecase import GenerateParametricModelUsecase
from repository.point_cloud_repository import PointCloudRepository
from repository.model_repository import ModelRepository
from geometry_manager.geometries_manager import GeometryManager

def load_point_cloud_usecase(manager: GeometryManager) -> LoadPointCloudUsecase:
    repository = PointCloudRepository()
    usecase = LoadPointCloudUsecase(manager, repository)
    return usecase

def save_point_cloud_usecase(manager: GeometryManager) -> SavePointCloudUsecase:
    repository = PointCloudRepository()
    usecase = SavePointCloudUsecase(manager, repository)
    return usecase

def load_model_usecase(manager: GeometryManager) -> LoadModelUsecase:
    repository = ModelRepository()
    usecase = LoadModelUsecase(manager, repository)
    return usecase

def save_model_usecase(manager: GeometryManager) -> SaveModelUsecase:
    repository = ModelRepository()
    usecase = SaveModelUsecase(manager, repository)
    return usecase

def generate_parametric_model_usecase(manager: GeometryManager) -> GenerateParametricModelUsecase:
    repository = ModelRepository()
    usecase = GenerateParametricModelUsecase(manager, repository)
    return usecase