# ui/attribute_ui.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, 
                             QPushButton, QHBoxLayout, QHeaderView, QMessageBox, QInputDialog,
                             QFileDialog, QDialog, QScrollArea, QStyledItemDelegate, QMenu)
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QPixmap, QIcon
import os
import shutil
import time

from geometry_manager.geometries_manager import GeometryManager

class ImagePreviewDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("画像プレビュー")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # スクロールエリア
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 画像ラベル
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignCenter)
        
        # 画像を読み込み
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # 画像が大きすぎる場合はスケーリング
            if pixmap.width() > 500 or pixmap.height() > 400:
                pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
        else:
            image_label.setText("画像が見つかりません")
        
        scroll_area.setWidget(image_label)
        layout.addWidget(scroll_area)
        
        # 閉じるボタン
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class ImageTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, texts, image_path=None):
        super().__init__(texts)
        self.image_path = image_path
        self.thumbnail_size = 60  # サムネイルサイズ

class AttributeEditDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent

    def createEditor(self, parent, option, index):
        # 属性名の列（0列目）は編集不可
        if index.column() == 0:
            return None
        
        # 画像属性の場合は特別な処理
        item = self.parent_widget.attribute_tree.itemFromIndex(index)
        if item:
            attr_name = item.text(0)
            if self._is_image_attribute(attr_name):
                # ★ 修正: 直接画像選択ダイアログを表示
                self._select_image_directly(item)
                return None
        
        # 通常のテキスト編集
        return super().createEditor(parent, option, index)

    def _is_image_attribute(self, attr_name):
        """画像属性かどうかを判定"""
        image_keywords = ["画像", "写真", "損傷写真", "点検写真", "全体写真"]
        return any(keyword in attr_name for keyword in image_keywords)

    def _select_image_directly(self, item):
        """画像ファイル選択（直接実行）"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self.parent_widget,
            "画像ファイルを選択",
            "",
            "画像ファイル (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;すべてのファイル (*)"
        )
        
        if file_path:
            try:
                # プロジェクト内の画像フォルダにコピー
                project_image_path = self._copy_image_to_project(file_path)
                if project_image_path:
                    # ★ 修正: 実際のパスを内部的に保存し、表示は空にする
                    item.setData(1, Qt.UserRole, project_image_path)  # 実際のパスを保存
                    item.setText(1, "")  # 表示テキストは空
                    
                    # TreeWidgetの変更シグナルを発火
                    self.parent_widget.attribute_tree.itemChanged.emit(item, 1)
                    # 画像表示を更新
                    self.parent_widget._update_image_display_from_data(item)
            except Exception as e:
                QMessageBox.critical(self.parent_widget, "エラー", f"画像の選択に失敗しました：\n{e}")

    def _copy_image_to_project(self, source_path):
        """画像をプロジェクトフォルダにコピー"""
        if not hasattr(self.parent_widget, 'main_viewer') or not self.parent_widget.main_viewer:
            return None
        
        main_viewer = self.parent_widget.main_viewer
        if not hasattr(main_viewer, 'current_project_name') or not main_viewer.current_project_name:
            return None
        
        try:
            # プロジェクトフォルダ内に images フォルダを作成
            project_dir = os.path.dirname(main_viewer.project_file_path) if hasattr(main_viewer, 'project_file_path') else "."
            images_dir = os.path.join(project_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            
            # ファイル名を生成（タイムスタンプ付き）
            import time
            timestamp = str(int(time.time()))
            file_name = os.path.basename(source_path)
            name, ext = os.path.splitext(file_name)
            new_file_name = f"{name}_{timestamp}{ext}"
            
            # ファイルをコピー
            dest_path = os.path.join(images_dir, new_file_name)
            shutil.copy2(source_path, dest_path)
            
            return dest_path
            
        except Exception as e:
            print(f"画像コピーエラー: {e}")
            return None

class AttributeUi(QWidget):
    def __init__(self, manager: GeometryManager, main_viewer=None):
        super().__init__()
        self.manager = manager
        self.main_viewer = main_viewer
        self.current_folder_name = None
        self.current_folder_level = None
        self.current_parent_name = None
        self.current_model_name = None
        self.current_model_hierarchy = None

        self.label = QLabel("属性情報：")
        self.attribute_tree = QTreeWidget()
        self.attribute_tree.setHeaderLabels(["属性名", "値"])
        
        # TreeWidgetの設定
        self.attribute_tree.setIndentation(0)
        self.attribute_tree.setRootIsDecorated(False)
        self.attribute_tree.setAlternatingRowColors(True)
        
        # ★ 追加: 行の高さを画像表示用に調整
        self.attribute_tree.setStyleSheet("""
            QTreeWidget {
                gridline-color: #d0d0d0;
                alternate-background-color: #f5f5f5;
                background-color: white;
                selection-background-color: #3daee9;
                border: 1px solid #c0c0c0;
                show-decoration-selected: 1;
            }
            QTreeWidget::item {
                border-right: 1px solid #d0d0d0;
                border-bottom: 1px solid #e0e0e0;
                padding: 5px;
                min-height: 70px;  /* 画像表示用に高さを増加 */
            }
            QTreeWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 5px;
                font-weight: bold;
            }
        """)
        
        # カスタムデリゲートを設定
        delegate = AttributeEditDelegate(self)
        self.attribute_tree.setItemDelegate(delegate)
        
        # TreeWidgetを編集可能にする
        self.attribute_tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        
        # シグナル接続
        self.attribute_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.attribute_tree.itemChanged.connect(self._on_item_changed)
        # ★ 追加: クリックイベント
        self.attribute_tree.itemClicked.connect(self._on_item_clicked)
        
        # ヘッダーの幅を調整
        header = self.attribute_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 120)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        # 保存ボタン
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("属性を保存")
        self.save_button.clicked.connect(self._save_attributes)
        self.save_button.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.attribute_tree)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def show_folder_attributes(self, folder_name: str, folder_level: int, parent_name: str = None):
        """指定されたフォルダの属性情報を表示"""
        print(f"[AttributeUi] 属性表示開始: {folder_name}, レベル: {folder_level}, 親: {parent_name}")  # デバッグ用
        
        if not self.main_viewer:
            print("[AttributeUi] エラー: main_viewerが設定されていません")
            return
        
        self.current_folder_name = folder_name
        self.current_folder_level = folder_level
        self.current_parent_name = parent_name
        
        # TreeWidgetをクリア
        self.attribute_tree.clear()
        print(f"[AttributeUi] TreeWidgetをクリアしました")
        
        # ラベル更新
        if folder_level == 1:
            self.label.setText(f"属性情報： 第1階層フォルダ '{folder_name}'")
        elif folder_level == 2:
            self.label.setText(f"属性情報： 第2階層フォルダ '{folder_name}'")
        elif folder_level == 3:
            self.label.setText(f"属性情報： 第3階層フォルダ '{folder_name}'")
        
        print(f"[AttributeUi] ラベル更新完了")
        
        # 属性データを取得して表示
        attributes = self._get_folder_attributes(folder_name, folder_level, parent_name)
        print(f"[AttributeUi] 取得した属性: {attributes}")
        
        if attributes:
            self._populate_tree(attributes, folder_level)
            print(f"[AttributeUi] TreeWidgetに属性を追加しました")
        else:
            print(f"[AttributeUi] 警告: 属性データが空です")
        
        # 保存ボタンを有効化
        self.save_button.setEnabled(True)
        print(f"[AttributeUi] 属性表示完了")
    
    def show_placed_model_attributes(self, model_data: dict):
        """配置されたモデルの属性情報を表示"""
        print(f"[AttributeUi] 配置モデル属性表示開始: {model_data}")  # デバッグ用
        
        if not self.main_viewer:
            print("[AttributeUi] エラー: main_viewerが設定されていません")
            return
        
        model_name = model_data.get("name", "")
        first_level_parent = model_data.get("first_level_parent", "")
        second_level_parent = model_data.get("second_level_parent", "")
        third_level_parent = model_data.get("third_level_parent", "")
        
        # 現在のモデル情報を保存
        self.current_model_name = model_name
        self.current_model_hierarchy = {
            "first_level": first_level_parent,
            "second_level": second_level_parent,
            "third_level": third_level_parent
        }
        
        # ★ 修正: tree_widget → attribute_tree
        self.attribute_tree.clear()
        print(f"[AttributeUi] TreeWidgetをクリアしました")
        
        # ラベル更新
        self.label.setText(f"属性情報： モデル '{model_name}'")
        print(f"[AttributeUi] ラベル更新完了")
        
        # 配置モデルの属性データを取得して表示
        attributes = self._get_placed_model_attributes(model_data)
        print(f"[AttributeUi] 取得した配置モデル属性: {attributes}")
        
        if attributes:
            self._populate_tree(attributes, "model")
            print(f"[AttributeUi] TreeWidgetに配置モデル属性を追加しました")
        else:
            print(f"[AttributeUi] 警告: 配置モデル属性データが空です")
        
        # 保存ボタンを有効化
        self.save_button.setEnabled(True)
        print(f"[AttributeUi] 配置モデル属性表示完了")
    def hide_attributes(self):
        """属性表示をクリア"""
        self.label.setText("属性情報：")
        self.attribute_tree.clear()
        self.save_button.setEnabled(False)
        self.current_folder_name = None
        self.current_folder_level = None
        self.current_parent_name = None
        self.current_model_name = None
        self.current_model_hierarchy = None

    def _get_folder_attributes(self, folder_name: str, folder_level: int, parent_name: str = None):
        """フォルダの属性データを取得"""
        print(f"[AttributeUi] 属性データ取得開始: {folder_name}, レベル: {folder_level}")
        
        if not self.main_viewer:
            print(f"[AttributeUi] エラー: main_viewerが設定されていません")
            return {}
        
        if not hasattr(self.main_viewer, 'project_attributes'):
            print(f"[AttributeUi] エラー: project_attributesが存在しません")
            return {}
        
        project_attributes = self.main_viewer.project_attributes
        print(f"[AttributeUi] プロジェクト属性: {project_attributes}")
        
        folders = project_attributes.get("folders", {})
        print(f"[AttributeUi] フォルダデータ: {folders}")
        
        if folder_level == 1:
            # 第1階層フォルダの属性
            print(f"[AttributeUi] 第1階層フォルダの属性を取得中...")
            folder_data = folders.get(folder_name, {})
            print(f"[AttributeUi] フォルダデータ '{folder_name}': {folder_data}")
            
            attributes = folder_data.get("attributes", None)
            if attributes is None:
                print(f"[AttributeUi] 属性が見つからないため、デフォルト属性を使用")
                attributes = self._get_default_first_level_attributes()
            
            print(f"[AttributeUi] 第1階層属性: {attributes}")
            return attributes
            
        elif folder_level == 2:
            # 第2階層フォルダの属性
            print(f"[AttributeUi] 第2階層フォルダの属性を取得中...")
            if parent_name and parent_name in folders:
                second_level_folders = folders[parent_name].get("second_level_folders", {})
                print(f"[AttributeUi] 第2階層フォルダ一覧: {second_level_folders}")
                
                folder_data = second_level_folders.get(folder_name, {})
                print(f"[AttributeUi] 第2階層フォルダデータ '{folder_name}': {folder_data}")
                
                attributes = folder_data.get("attributes", None)
                if attributes is None:
                    print(f"[AttributeUi] 第2階層属性が見つからないため、デフォルト属性を使用")
                    attributes = self._get_default_second_level_attributes()
                
                print(f"[AttributeUi] 第2階層属性: {attributes}")
                return attributes
            else:
                print(f"[AttributeUi] 警告: 親フォルダ '{parent_name}' が見つかりません")
        elif folder_level == 3:
            # 第3階層フォルダの属性
            print(f"[AttributeUi] 第3階層フォルダの属性を取得中...")
            # parent_nameは "第1階層 > 第2階層" の形式
            if parent_name and " > " in parent_name:
                first_level_parent, second_level_parent = parent_name.split(" > ")
                
                if first_level_parent in folders:
                    second_level_folders = folders[first_level_parent].get("second_level_folders", {})
                    if second_level_parent in second_level_folders:
                        third_level_folders = second_level_folders[second_level_parent].get("third_level_folders", {})
                        print(f"[AttributeUi] 第3階層フォルダ一覧: {third_level_folders}")
                        
                        folder_data = third_level_folders.get(folder_name, {})
                        print(f"[AttributeUi] 第3階層フォルダデータ '{folder_name}': {folder_data}")
                        
                        attributes = folder_data.get("attributes", None)
                        if attributes is None:
                            print(f"[AttributeUi] 第3階層属性が見つからないため、デフォルト属性を使用")
                            attributes = self._get_default_third_level_attributes()
                        
                        print(f"[AttributeUi] 第3階層属性: {attributes}")
                        return attributes
                    else:
                        print(f"[AttributeUi] 警告: 第2階層フォルダ '{second_level_parent}' が見つかりません")
                else:
                    print(f"[AttributeUi] 警告: 第1階層フォルダ '{first_level_parent}' が見つかりません")
            else:
                print(f"[AttributeUi] 警告: 第3階層の親フォルダ情報が正しくありません: '{parent_name}'")
        
        print(f"[AttributeUi] 属性データが見つかりませんでした")
        return {}

    def _get_placed_model_attributes(self, model_data: dict):
        """配置モデルの属性データを取得"""
        print(f"[AttributeUi] 配置モデル属性データ取得開始: {model_data}")
        
        if not self.main_viewer:
            print(f"[AttributeUi] エラー: main_viewerが設定されていません")
            return {}
        
        if not hasattr(self.main_viewer, 'project_attributes'):
            print(f"[AttributeUi] エラー: project_attributesが存在しません")
            return {}
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        
        first_level = model_data.get("first_level_parent", "")
        second_level = model_data.get("second_level_parent", "")
        third_level = model_data.get("third_level_parent", "")
        model_name = model_data.get("name", "")
        
        print(f"[AttributeUi] 階層情報: {first_level} > {second_level} > {third_level} > {model_name}")
        print(f"[AttributeUi] プロジェクト属性全体: {project_attributes}")
        print(f"[AttributeUi] フォルダ一覧: {list(folders.keys())}")
        
        try:
            # 階層構造をたどって配置モデルの属性を取得
            if first_level in folders:
                print(f"[AttributeUi] 第1階層フォルダ '{first_level}' 見つかりました")
                first_level_data = folders[first_level]
                print(f"[AttributeUi] 第1階層データ: {first_level_data}")
                
                second_level_folders = first_level_data.get("second_level_folders", {})
                print(f"[AttributeUi] 第2階層フォルダ一覧: {list(second_level_folders.keys())}")
                
                if second_level in second_level_folders:
                    print(f"[AttributeUi] 第2階層フォルダ '{second_level}' 見つかりました")
                    second_level_data = second_level_folders[second_level]
                    print(f"[AttributeUi] 第2階層データ: {second_level_data}")
                    
                    third_level_folders = second_level_data.get("third_level_folders", {})
                    print(f"[AttributeUi] 第3階層フォルダ一覧: {list(third_level_folders.keys())}")
                    
                    if third_level in third_level_folders:
                        print(f"[AttributeUi] 第3階層フォルダ '{third_level}' 見つかりました")
                        third_level_data = third_level_folders[third_level]
                        print(f"[AttributeUi] 第3階層データ: {third_level_data}")
                        
                        models = third_level_data.get("models", {})
                        print(f"[AttributeUi] モデル一覧: {list(models.keys())}")
                        
                        if model_name in models:
                            print(f"[AttributeUi] モデル '{model_name}' 見つかりました")
                            model_info = models[model_name]
                            print(f"[AttributeUi] モデル情報: {model_info}")
                            
                            attributes = model_info.get("attributes", None)
                            print(f"[AttributeUi] 保存済み属性: {attributes}")
                            
                            if attributes is None or len(attributes) == 0:
                                print(f"[AttributeUi] 配置モデル属性が見つからないため、デフォルト属性を使用")
                                attributes = self._get_default_model_attributes(model_info)
                                print(f"[AttributeUi] デフォルト属性生成: {attributes}")
                            
                            print(f"[AttributeUi] 最終的な配置モデル属性: {attributes}")
                            return attributes
                        else:
                            print(f"[AttributeUi] エラー: モデル '{model_name}' が見つかりません")
                    else:
                        print(f"[AttributeUi] エラー: 第3階層フォルダ '{third_level}' が見つかりません")
                else:
                    print(f"[AttributeUi] エラー: 第2階層フォルダ '{second_level}' が見つかりません")
            else:
                print(f"[AttributeUi] エラー: 第1階層フォルダ '{first_level}' が見つかりません")
                
        except Exception as e:
            print(f"[AttributeUi] 配置モデル属性取得エラー: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[AttributeUi] 配置モデル属性データが見つかりませんでした")
        # ★ 修正: 見つからない場合でもデフォルト属性を返す
        print(f"[AttributeUi] デフォルト属性を生成します")
        default_attributes = self._get_default_model_attributes({
            "original_name": model_name,
            "file_path": "unknown",
            "geometry_type": "model",
            "placed_date": "unknown"
        })
        print(f"[AttributeUi] 生成したデフォルト属性: {default_attributes}")
        return default_attributes

    def _get_default_model_attributes(self, model_info: dict):
        """配置モデルのデフォルト属性"""
        geometry_type = model_info.get("geometry_type", "model")
        file_path = model_info.get("file_path", "unknown")
        placed_date = model_info.get("placed_date", "unknown")
        
        return {
            "要素番号": "Mg0101",
            "構造形式": "鋼橋鈑桁",
            "損傷種類": "腐食",
            "損傷画像": "―",
            "撮影日": "2025.05.06",
            "判定区分": "C",
            "モデル名": model_info.get("original_name", "unknown"),
            "ファイルパス": file_path,
            "ジオメトリタイプ": geometry_type,
            "配置日時": placed_date,
        }

    def _get_default_first_level_attributes(self):
        """第1階層フォルダのデフォルト属性"""
        return {
            "施設ID": "43.18167,14132556",
            "橋梁名": "○○橋",
            "路線名": "国道○○号",
            "所在地": "〇〇県△△市□□",
            "緯度・経度": "○°☓'△\"",
            "管理者": "〇〇県□□土木事務所",
            "点検実施日": "2025.○.△",
            "架設年度": "2016",
            "橋長": "107m",
            "幅員": "11.8m",
            "橋梁形式": "桁橋",
            "全景画像": "―"
        }
    
    def _get_default_second_level_attributes(self):
        """第2階層フォルダのデフォルト属性"""
        return {
            "構造種別": "RC桁",
            "要素番号": "第1径間",
            "画像": "―",
        }

    def _get_default_third_level_attributes(self):
        """第3階層フォルダのデフォルト属性"""
        return {
            "要素番号": "Mg0101",
            "構造形式": "鋼橋鈑桁",
            "損傷種類": "腐食",
            "損傷画像": "―",
            "撮影日": "2025.05.06",
            "判定区分": "C"
        }

    def _populate_tree(self, attributes, attribute_type):
        """TreeWidgetに属性情報を追加"""
        print(f"[AttributeUi] TreeWidget構築開始 - 属性数: {len(attributes)}, タイプ: {attribute_type}")
        
        if not attributes:
            print(f"[AttributeUi] 警告: 属性データが空です")
            return
        
        for attr_name, attr_value in attributes.items():
            print(f"[AttributeUi] 追加中: {attr_name} = {attr_value}")
            
            # ★ 修正: 画像属性の場合は特別な表示
            if self._is_image_attribute(attr_name):
                if attr_value and attr_value != "未設定" and os.path.exists(attr_value):
                    # ★ 修正: 画像が存在する場合は値欄を空にして画像のみ表示
                    item = QTreeWidgetItem([attr_name, ""])  # 値欄は空文字
                    
                    # サムネイル画像を設定
                    try:
                        pixmap = QPixmap(attr_value)
                        if not pixmap.isNull():
                            thumbnail = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            item.setIcon(1, QIcon(thumbnail))
                            item.setToolTip(1, f"ダブルクリックで画像選択\nクリックで拡大表示")
                    except Exception as e:
                        print(f"サムネイル作成エラー: {e}")
                    
                    # 実際のパスは内部的に保持（JSON保存用）
                    item.setData(1, Qt.UserRole, attr_value)
                else:
                    # 画像が未設定の場合
                    item = QTreeWidgetItem([attr_name, "未設定"])
                    item.setToolTip(1, "ダブルクリックで画像を選択")
                    item.setData(1, Qt.UserRole, attr_value)
            else:
                # 通常の属性
                item = QTreeWidgetItem([attr_name, str(attr_value)])
            
            # アイテムを編集可能にする
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.attribute_tree.addTopLevelItem(item)
        
        # TreeWidgetを展開
        self.attribute_tree.expandAll()
        
        # 追加されたアイテム数を確認
        item_count = self.attribute_tree.topLevelItemCount()
        print(f"[AttributeUi] TreeWidgetに追加されたアイテム数: {item_count}")
    
    def _is_image_attribute(self, attr_name):
        """画像属性かどうかを判定"""
        image_keywords = ["画像", "写真", "損傷写真", "点検写真", "全体写真"]
        return any(keyword in attr_name for keyword in image_keywords)

    def _on_item_double_clicked(self, item, column):
        """アイテムがダブルクリックされた時の処理"""
        if column == 0:  # 属性名の列がクリックされた場合
            # 属性名は編集不可なので何もしない
            return
        # 値の列（column == 1）の場合は編集を許可（デフォルト動作）
    
    def _on_item_clicked(self, item, column):
        """アイテムがクリックされた時の処理"""
        if column == 1:  # 値の列がクリックされた場合
            attr_name = item.text(0)
            if self._is_image_attribute(attr_name):
                # 画像属性の場合、画像を拡大表示
                image_path = item.data(1, Qt.UserRole) or item.text(1)
                if image_path and image_path != "未設定" and os.path.exists(image_path):
                    self._show_image_preview(image_path)
    
    def _show_image_preview(self, image_path):
        """画像プレビューを表示"""
        dialog = ImagePreviewDialog(image_path, self)
        dialog.exec_()

    def _on_item_changed(self, item, column):
        """TreeWidgetのアイテムが変更された時の処理"""
        if column == 1:  # 値の列が変更された場合
            attr_name = item.text(0)
            new_value = item.text(1)
            print(f"属性変更: {attr_name} = {new_value}")  # デバッグ用

    def _save_attributes(self):
        """属性データを保存"""
        if not self.main_viewer:
            QMessageBox.warning(self, "警告", "保存対象が選択されていません。")
            return
        
        try:
            # TreeWidgetから属性データを取得
            attributes = {}
            root = self.attribute_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                attr_name = item.text(0)
                
                # ★ 修正: 画像属性の場合は実際のパスを取得
                if self._is_image_attribute(attr_name):
                    # UserRoleに保存されている実際のパスを使用
                    attr_value = item.data(1, Qt.UserRole)
                    if attr_value is None:
                        attr_value = item.text(1)
                else:
                    attr_value = item.text(1)
                
                attributes[attr_name] = attr_value
            
            # フォルダの属性か配置モデルの属性かを判定
            if hasattr(self, 'current_model_name') and self.current_model_name:
                # 配置モデルの属性を更新
                self._update_placed_model_attributes(attributes)
                QMessageBox.information(self, "保存完了", f"モデル '{self.current_model_name}' の属性情報を保存しました。")
            elif self.current_folder_name:
                # フォルダの属性を更新（従来通り）
                self._update_folder_attributes(attributes)
                QMessageBox.information(self, "保存完了", f"'{self.current_folder_name}' の属性情報を保存しました。")
            else:
                QMessageBox.warning(self, "警告", "保存対象が特定できません。")
                return
            
            # プロジェクト属性を保存
            self.main_viewer._save_project_attributes()
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"属性の保存に失敗しました：\n{e}")

    def _update_folder_attributes(self, attributes):
        """フォルダの属性データを更新"""
        if not self.main_viewer:
            return
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        
        if self.current_folder_level == 1:
            # 第1階層フォルダの属性を更新
            if self.current_folder_name not in folders:
                folders[self.current_folder_name] = {}
            
            folders[self.current_folder_name]["attributes"] = attributes
            
        elif self.current_folder_level == 2:
            # 第2階層フォルダの属性を更新
            if self.current_parent_name and self.current_parent_name in folders:
                second_level_folders = folders[self.current_parent_name].get("second_level_folders", {})
                if self.current_folder_name in second_level_folders:
                    second_level_folders[self.current_folder_name]["attributes"] = attributes
                    
        elif self.current_folder_level == 3:
            # 第3階層フォルダの属性を更新
            if self.current_parent_name and " > " in self.current_parent_name:
                first_level_parent, second_level_parent = self.current_parent_name.split(" > ")
                
                if first_level_parent in folders:
                    second_level_folders = folders[first_level_parent].get("second_level_folders", {})
                    if second_level_parent in second_level_folders:
                        third_level_folders = second_level_folders[second_level_parent].get("third_level_folders", {})
                        if self.current_folder_name in third_level_folders:
                            third_level_folders[self.current_folder_name]["attributes"] = attributes
    
    def _update_placed_model_attributes(self, attributes):
        """配置モデルの属性データを更新"""
        if not self.main_viewer or not hasattr(self, 'current_model_hierarchy'):
            return
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        
        hierarchy = self.current_model_hierarchy
        first_level = hierarchy["first_level"]
        second_level = hierarchy["second_level"]
        third_level = hierarchy["third_level"]
        model_name = self.current_model_name
        
        try:
            # 階層構造をたどって配置モデルの属性を更新
            if first_level in folders:
                second_level_folders = folders[first_level].get("second_level_folders", {})
                if second_level in second_level_folders:
                    third_level_folders = second_level_folders[second_level].get("third_level_folders", {})
                    if third_level in third_level_folders:
                        models = third_level_folders[third_level].get("models", {})
                        if model_name in models:
                            models[model_name]["attributes"] = attributes
                            print(f"[AttributeUi] 配置モデル '{model_name}' の属性を更新しました")
        except Exception as e:
            print(f"[AttributeUi] 配置モデル属性更新エラー: {e}")
    
    def _update_image_display(self, item):
        """アイテムの画像表示を更新"""
        image_path = item.text(1)
        if os.path.exists(image_path):
            try:
                # ★ 修正: 値欄を空にして画像のみ表示
                item.setText(1, "      ")  # テキストを空にする
                
                # サムネイル画像を作成
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # サムネイルサイズにスケール
                    thumbnail = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # アイテムにアイコンとして設定
                    item.setIcon(10, QIcon(thumbnail))
                    # ツールチップを更新
                    item.setToolTip(1, f"ダブルクリックで画像選択\nクリックで拡大表示")
            except Exception as e:
                print(f"サムネイル作成エラー: {e}")
    
    def _update_image_display_from_data(self, item):
        """UserRoleのデータから画像表示を更新"""
        image_path = item.data(1, Qt.UserRole)
        if image_path and os.path.exists(image_path):
            try:
                # 値欄を空にして画像のみ表示
                item.setText(1, "")
                
                # サムネイル画像を作成
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # サムネイルサイズにスケール
                    thumbnail = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    # アイテムにアイコンとして設定
                    item.setIcon(1, QIcon(thumbnail))
                    # ツールチップを更新
                    item.setToolTip(1, f"ダブルクリックで画像選択\nクリックで拡大表示")
            except Exception as e:
                print(f"サムネイル作成エラー: {e}")

