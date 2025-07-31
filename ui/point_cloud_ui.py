# ui/point_cloud_ui.py

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QDialog, QMessageBox
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt
from pyvistaqt import QtInteractor
import pyvista as pv
import vtk
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera

from di.container import generate_parametric_model_usecase
from geometry_manager.geometries_manager import GeometryManager

class PointCloudInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, plotter, on_point_picked_callback):
        super().__init__()
        self.plotter = plotter
        self.on_point_picked = on_point_picked_callback
        self.AddObserver("RightButtonPressEvent", self.on_right_click)

    def on_right_click(self, obj, event):
        pos = self.GetInteractor().GetEventPosition()
        picker = vtk.vtkPointPicker()
        picker.Pick(pos[0], pos[1], 0, self.plotter.renderer)

        point_id = picker.GetPointId()
        if point_id == -1:
            print("[!] 近くに点がありませんでした。")
            return

        picked = picker.GetPickPosition()
        self.on_point_picked(picked)

class PointCloudUi(QWidget):
    def __init__(self, manager: GeometryManager):
        super().__init__()

        self.geometry_manager = manager
        self.geometry_manager.updated.connect(self._refresh_entire_scene)

        self.generate_parametric_model_usecase = generate_parametric_model_usecase(self.geometry_manager)

        # === 中身（メインビュー） ===
        self.plotter = QtInteractor(self)

        # === レイアウト構築 ===
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 余白なしで最大限使う
        layout.addWidget(self.plotter)
        self.setLayout(layout)

    def _refresh_entire_scene(self):
        self.plotter.clear()
        self.plotter.enable_lightkit()
        for geometry in self.geometry_manager.get_visible_items():
            if geometry.geometry_type == "pointcloud":
                points = np.asarray(geometry.data.points)
                colors = np.asarray(geometry.data.colors) if geometry.data.has_colors() else None
                cloud = pv.PolyData(points)

                if colors is not None:
                    cloud['colors'] = colors
                    self.plotter.add_points(cloud, scalars='colors', rgb=True, point_size=5)
                else:
                    self.plotter.add_points(cloud, color='white', point_size=5)
            elif geometry.geometry_type == "model":
                vertices = np.asarray(geometry.data.vertices)
                triangles = np.asarray(geometry.data.triangles)

                if len(vertices) == 0 or len(triangles) == 0:
                    print(f"[WARNING] モデルに頂点または三角形が含まれていません: {geometry}")
                    continue

                # PyVista用の三角形配列は各セルの先頭に「3」が必要
                faces = np.hstack([
                    np.full((triangles.shape[0], 1), 3),  # 3頂点を示す
                    triangles
                ]).flatten()

                mesh = pv.PolyData(vertices, faces)

                # 色がある場合
                if geometry.data.has_vertex_colors():
                    colors = np.asarray(geometry.data.vertex_colors)
                    mesh['colors'] = colors
                    self.plotter.add_mesh(
                        mesh,
                        scalars='colors',
                        rgb=True,
                        show_edges=False,
                        lighting=True,
                        smooth_shading=True,
                        interpolation='phong',
                        specular=0.5,
                        specular_power=20
                    )
                else:
                    self.plotter.add_mesh(
                        mesh,
                        color='lightgray',
                        show_edges=False,
                        lighting=True,
                        smooth_shading=True,
                        interpolation='phong',
                        specular=0.5,
                        specular_power=20
                    )
            elif geometry.geometry_type == 'textured_model':
                mesh = geometry.data['mesh']
                texture = geometry.data['texture']
                
                # テクスチャが辞書形式（複数テクスチャ）の場合
                if isinstance(texture, dict):
                    # プライマリテクスチャを取得（primaryがなければ最初のテクスチャを使用）
                    primary_texture = texture.get('primary', list(texture.values())[0])
                    self.plotter.add_mesh(
                        mesh,
                        texture=primary_texture,
                        smooth_shading=True,
                    )
                    print(f"Displayed mesh with primary texture (total textures: {len(texture)})")
                    
                    # 他のテクスチャも表示したい場合は、追加で処理
                    # for tex_name, tex_obj in texture.items():
                    #     if tex_name != 'primary':
                    #         # 必要に応じて別の方法で表示
                    
                else:
                    # 単一テクスチャの場合（従来通り）
                    self.plotter.add_mesh(
                        mesh,
                        texture=texture,
                        smooth_shading=True,
                    )

        self.plotter.render()