import open3d as o3d
import numpy as np

def run_gicp(
    source: o3d.geometry.PointCloud,
    target: o3d.geometry.PointCloud,
    threshold: float = 0.05,
    max_iter: int = 200
) -> np.ndarray:
    """
    Generalized ICP により source → target の最適な剛体変換行列（4x4）を推定。
    """

    source.estimate_normals()
    target.estimate_normals()

    result = o3d.pipelines.registration.registration_generalized_icp(
        source, target, threshold, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationForGeneralizedICP(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iter)
    )

    return result.transformation
