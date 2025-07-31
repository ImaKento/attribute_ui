# usecase/io/load_model_usecase.py

import os
from pathlib import Path

from geometry_manager.geometries_manager import GeometryManager
from domain.repository.model_repository import IModelRepository

class LoadModelUsecase():
    def __init__(self, geometry_manager: GeometryManager, model_repository: IModelRepository):
        self.geometry_manager = geometry_manager
        self.model_repository = model_repository

    def exec(self, file_path: str):
        print(file_path)
        # ファイル拡張子を取得
        file_extension = Path(file_path).suffix.lower()
        
        if file_extension == '.obj':
            self._load_obj_model(file_path)
        else:
            # 従来の処理
            pcd = self.model_repository.load(file_path)
            name = os.path.basename(file_path)
            self.geometry_manager.add(name, pcd, "model")
    
    def _load_obj_model(self, obj_file_path: str):
        """OBJファイルとその関連テクスチャファイルを読み込む"""
        obj_path = Path(obj_file_path)
        obj_dir = obj_path.parent
        obj_name = obj_path.stem
        
        # 関連ファイルを検索
        related_files = self._find_related_files(obj_dir, obj_name)
        
        # OBJファイルを読み込み（メッシュデータを取得）
        mesh = self.model_repository.load_obj(obj_file_path)
        
        # テクスチャファイルがある場合
        if related_files['textures'] or related_files['mtl']:
            # テクスチャを読み込み・適用
            texture = self._load_texture(related_files)
            
            if texture is not None:
                # テクスチャ付きモデルとして追加
                textured_data = {
                    'mesh': mesh,
                    'texture': texture
                }
                self.geometry_manager.add(obj_name, textured_data, "textured_model")
                
                # ログ出力
                if isinstance(texture, dict):
                    print(f"Loaded textured OBJ model with {len(texture)} textures: {obj_name}")
                    for tex_name in texture.keys():
                        print(f"  - {tex_name}")
                else:
                    print(f"Loaded textured OBJ model: {obj_name}")
                
                if related_files['mtl']:
                    print(f"  - Material file: {os.path.basename(related_files['mtl'])}")
            else:
                # テクスチャの読み込みに失敗した場合は通常のモデルとして追加
                self.geometry_manager.add(obj_name, mesh, "model")
                print(f"Loaded OBJ model (texture failed): {obj_name}")
        else:
            # テクスチャファイルがない場合は通常のモデルとして追加
            self.geometry_manager.add(obj_name, mesh, "model")
            print(f"Loaded OBJ model: {obj_name}")
    
    def _find_related_files(self, obj_dir: Path, obj_name: str):
        """OBJファイルに関連するファイルを検索"""
        related_files = {
            'mtl': None,
            'textures': []
        }
        
        # MTLファイルを検索（同名のファイルを優先）
        mtl_patterns = [
            f"{obj_name}.mtl",
            "*.mtl"
        ]
        
        for pattern in mtl_patterns:
            mtl_files = list(obj_dir.glob(pattern))
            if mtl_files:
                related_files['mtl'] = str(mtl_files[0])
                break
        
        # テクスチャファイルを検索
        texture_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tga', '*.tiff']
        for ext in texture_extensions:
            texture_files = list(obj_dir.glob(ext))
            related_files['textures'].extend([str(f) for f in texture_files])
        
        return related_files
    
    def _load_texture(self, related_files: dict):
        """テクスチャファイルを読み込む（複数対応）"""
        try:
            texture_files = []
            
            # MTLファイルがある場合は、それを解析してテクスチャファイルを特定
            if related_files['mtl']:
                mtl_textures = self._parse_mtl_for_texture(related_files['mtl'])
                if mtl_textures:
                    texture_files.extend(mtl_textures)
            
            # MTLファイルで見つからなかった場合、またはMTLファイルがない場合は
            # ディレクトリ内の全テクスチャファイルを追加
            if not texture_files and related_files['textures']:
                texture_files = related_files['textures']
            
            if not texture_files:
                return None
            
            # 複数のテクスチャがある場合
            if len(texture_files) > 1:
                print(f"Found {len(texture_files)} texture files:")
                for i, tex_file in enumerate(texture_files):
                    print(f"  [{i}] {os.path.basename(tex_file)}")
                
                # 複数テクスチャの場合は辞書形式で返す
                textures = {}
                for i, tex_file in enumerate(texture_files):
                    try:
                        texture_name = f"texture_{i}" if i > 0 else "primary"
                        textures[texture_name] = self.model_repository.load_texture(tex_file)
                        print(f"  Loaded: {texture_name} from {os.path.basename(tex_file)}")
                    except Exception as e:
                        print(f"  Failed to load {os.path.basename(tex_file)}: {e}")
                
                return textures if textures else None
            else:
                # 単一テクスチャの場合
                return self.model_repository.load_texture(texture_files[0])
            
        except Exception as e:
            print(f"Warning: Failed to load texture: {e}")
            return None
    
    def _parse_mtl_for_texture(self, mtl_file_path: str):
        """MTLファイルを解析してテクスチャファイルのパスリストを取得"""
        try:
            mtl_dir = Path(mtl_file_path).parent
            texture_files = []
            
            with open(mtl_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # 各種テクスチャマップを探す
                    texture_keywords = ['map_Kd', 'map_Ka', 'map_Ks', 'map_Bump', 'map_d', 'bump']
                    
                    for keyword in texture_keywords:
                        if line.startswith(f'{keyword} '):
                            texture_filename = line.split(' ', 1)[1].strip()
                            # ファイル名から余分な引数を除去（例：-s 1 1 1）
                            texture_filename = texture_filename.split()[0]
                            texture_path = mtl_dir / texture_filename
                            if texture_path.exists() and str(texture_path) not in texture_files:
                                texture_files.append(str(texture_path))
                                print(f"Found texture in MTL: {keyword} -> {texture_filename}")
            
            return texture_files if texture_files else None
        except Exception as e:
            print(f"Warning: Failed to parse MTL file {mtl_file_path}: {e}")
            return None