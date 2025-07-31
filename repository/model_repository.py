import open3d as o3d
import numpy as np
import pyvista as pv

from domain.repository.model_repository import IModelRepository

class ModelRepository(IModelRepository):
    def load(self, path: str) -> o3d.geometry.TriangleMesh:
        return o3d.io.read_triangle_mesh(path)
    
    def load_obj(self, obj_file_path: str):
        """OBJファイルをメッシュとして読み込む"""
        mesh = pv.read(obj_file_path)
        return mesh

    def load_texture(self, texture_file_path: str):
        """テクスチャファイルを読み込む"""
        return pv.read_texture(texture_file_path)

    def save(self, path: str, mesh: o3d.geometry.TriangleMesh):
        o3d.io.write_triangle_mesh(path, mesh)

    def Tpillar_generate_parametric_model(self, dist_list) -> o3d.geometry.TriangleMesh:
        p1, p2, p3, p4, p5, p6 = dist_list

        #表面点
        vertices = np.array([\
            [0, 0, 0],#0
            [p5, 0, 0],#1
            [0, 0, p4],#2
            [p5, 0, p4],#3
            [-(p1-p5)/2, 0, p2-p3],#4
            [0, 0, p2-p3],#5
            [p5, 0, p2-p3],#6
            [p5+((p1-p5)/2), 0, p2-p3],#7
            [-(p1-p5)/2, 0, p2],#8
            [0, 0, p2],#9
            [p5, 0, p2],#10
            [p5+((p1-p5)/2), 0, p2]#11
            ])
        #裏面点
        back_vertices =[]
        for pnt in vertices:
            p = [pnt[0], pnt[1] + p6, pnt[2]]
            back_vertices = np.append(back_vertices, p)
        vertices = np.append(vertices, back_vertices)
        vertices = np.reshape(vertices,[int(len(vertices) / 3), 3])

        #表面
        faces = np.array([\
            [0, 1, 2],
            [1, 3, 2],
            [2, 5, 4],
            [3, 7, 6],
            [2, 3, 9],
            [3, 10, 9],
            [4, 5, 8],
            [5, 9, 8],
            [6, 7, 10],
            [7, 11, 10]])
        #裏面
        back_faces = []
        for face in faces:
            f = [int(face[2] + 12), int(face[1] +12), int(face[0] + 12)]
            back_faces = np.append(back_faces, f)

        #左側面
        left_side_faces = np.array([\
            [0, 2, 12],
            [12, 2, 14],
            [4, 14, 2],
            [4, 16, 14],
            [4, 8, 20],
            [4, 20, 16]])
        
        #右側面
        right_side_faces = np.array([\
            [1, 13, 3],
            [13, 15, 3],
            [7, 3, 15],
            [7, 15, 19],
            [7, 23, 11],
            [7, 19, 23]])
        

        upper_under_faces = np.array([\
            [ 8, 11, 20],
            [20, 11, 23],
            [ 0, 12, 13],
            [ 0, 13, 1]
            ])
        
        faces = np.append(faces, back_faces)
        faces = np.reshape(faces,[int(len(faces) / 3), 3])
        faces = np.append(faces, left_side_faces)
        faces = np.reshape(faces,[int(len(faces) / 3), 3])
        faces = np.append(faces, right_side_faces)
        faces = np.reshape(faces,[int(len(faces) / 3), 3])
        faces = np.append(faces, upper_under_faces)
        faces = np.reshape(faces,[int(len(faces) / 3), 3])

        corner = np.array([\
            0, 1, 2, 3, 4, 7, 8, 11, 12, 13, 14, 15, 16, 19, 20, 23
            ])
        edge = np.array([\
            [0, 2],#表面
            [2, 4],
            [4, 8],
            [8, 11],
            [11, 7],
            [7, 3],
            [3, 1],
            [1, 0],
            [12, 14],#裏面
            [14, 16],
            [16, 20],
            [20, 23],
            [23, 19],
            [19, 15],
            [15, 13],
            [13, 12],
            [0, 12],#奥行き面
            [2, 14],
            [4, 16],
            [8, 20],
            [1, 13],
            [3, 15],
            [7, 19],
            [11, 23]
            ])

        faces = faces.astype(int)
        corner = corner.astype(int)
        edge = edge.astype(int)

        # Open3Dのメッシュとして返す
        model = o3d.geometry.TriangleMesh()
        model.vertices = o3d.utility.Vector3dVector(vertices)
        model.triangles = o3d.utility.Vector3iVector(faces)
        model.compute_vertex_normals()

        return model
