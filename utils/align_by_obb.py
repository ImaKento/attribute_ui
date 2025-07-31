import open3d as o3d
import numpy as np

def align_by_obb(
    pcd: o3d.geometry.PointCloud,
    model: o3d.geometry.TriangleMesh
) -> o3d.geometry.TriangleMesh:
    """
    点群とモデルのOriented Bounding Box (OBB) を使って、モデルを点群に大まかに位置合わせ。
    """
    # 点群とモデルのOBBを取得
    pcd_obb: o3d.geometry.OrientedBoundingBox = pcd.get_oriented_bounding_box()
    model_obb: o3d.geometry.OrientedBoundingBox = model.get_oriented_bounding_box()

    # 回転行列を計算（点群のOBBにモデルのOBBを揃える）
    R: np.ndarray = pcd_obb.R @ model_obb.R.T

    # 鏡映チェック：Z軸の符号が反転している場合は修正
    if np.linalg.det(R) > 0:
        print("⚠️ 鏡映検出：Z軸反転で修正")
        R[:, 2] *= -1  # Z軸を反転

    # 回転と並進の適用
    model.rotate(R, center=model_obb.center)
    translation: np.ndarray = pcd_obb.center - model.get_oriented_bounding_box().center
    model.translate(translation)

    return model