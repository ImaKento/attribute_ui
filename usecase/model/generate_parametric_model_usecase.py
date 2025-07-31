# usecase/io/generate_parametric_model_usecase.py

import numpy as np
import open3d as o3d

from utils.align_by_obb import align_by_obb
from utils.gicp import run_gicp
from geometry_manager.geometries_manager import GeometryManager
from domain.repository.model_repository import IModelRepository

class GenerateParametricModelUsecase():
    def __init__(self, geometry_manager: GeometryManager, model_repository: IModelRepository):
        self.geometry_manager = geometry_manager
        self.model_repository = model_repository
    
    def exec(self, geometry, dist_list) -> o3d.geometry.TriangleMesh:
        if len(dist_list) == 6:
            model = self.model_repository.Tpillar_generate_parametric_model(dist_list)

        model = align_by_obb(geometry.data, model)
        
        # メッシュを点群化してGICPで微調整
        model_pcd = model.sample_points_uniformly(10000)
        T = run_gicp(model_pcd, geometry.data)
        model.transform(T)

        return model
    
