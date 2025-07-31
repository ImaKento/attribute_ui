# ui/attribute_ui.py

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTreeWidget, 
                             QTreeWidgetItem, QHeaderView, QSplitter, 
                             QPushButton, QMessageBox, QHBoxLayout, QStyledItemDelegate)

from geometry_manager.geometries_manager import GeometryManager

class AttributeEditDelegate(QStyledItemDelegate):
    """属性値のみ編集可能にするデリゲート"""
    def createEditor(self, parent, option, index):
        if index.column() == 0:  # 属性名の列は編集不可
            return None
        return super().createEditor(parent, option, index)

class AttributeUi(QWidget):
    def __init__(self, manager: GeometryManager, main_viewer=None):
        super().__init__()
        self.manager = manager
        self.main_viewer = main_viewer  # MainViewerの参照を保持
        self.current_folder_name = None  # 現在選択中のフォルダ名
        self.current_folder_level = None  # 現在選択中のフォルダレベル
        self.current_parent_name = None  # 現在選択中のフォルダの親名

        self.label = QLabel("属性情報：")
        self.attribute_tree = QTreeWidget()
        self.attribute_tree.setHeaderLabels(["属性名", "値"])
        
        # TreeWidgetの左側の余白（インデント）を削除
        self.attribute_tree.setIndentation(0)  # インデントを0に設定
        self.attribute_tree.setRootIsDecorated(False)  # ルートの装飾を無効化
        
        # グリッド線を表示してセルの境界を明確にする
        self.attribute_tree.setAlternatingRowColors(True)  # 行の色を交互に変更
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
                min-height: 25px;
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
        
        # カスタムデリゲートを設定（値の列のみ編集可能）
        delegate = AttributeEditDelegate()
        self.attribute_tree.setItemDelegate(delegate)
        
        # TreeWidgetを編集可能にする
        self.attribute_tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        
        # 編集開始時のシグナル接続
        self.attribute_tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # アイテム編集完了時のシグナル接続
        self.attribute_tree.itemChanged.connect(self._on_item_changed)
        
        # ヘッダーの幅を調整
        header = self.attribute_tree.header()
        header.setStretchLastSection(True)
        # 属性名の列幅を固定値に設定（白い空白を削減）
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 120)  # 属性名列の幅を120pxに固定
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # 値の列は残りスペースを使用

        # 保存ボタン
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("属性を保存")
        self.save_button.clicked.connect(self._save_attributes)
        self.save_button.setEnabled(False)  # 初期状態では無効
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

    def hide_attributes(self):
        """属性表示をクリア"""
        self.label.setText("属性情報：")
        self.attribute_tree.clear()
        self.save_button.setEnabled(False)
        self.current_folder_name = None
        self.current_folder_level = None
        self.current_parent_name = None

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

    def _get_default_third_level_attributes(self):
        """第3階層フォルダのデフォルト属性"""
        return {
            "部材種別": "主桁",
            "材質": "鋼材",
            "断面形状": "I形断面",
            "設計基準": "道路橋示方書",
            "製作年": "2016",
            "検査結果": "良好"
        }

    def _get_default_second_level_attributes(self):
        """第2階層フォルダのデフォルト属性"""
        return {
            "構造種別": "RC桁",
            "設計荷重": "B活荷重",
            "材料強度": "Fc=24N/mm²",
            "施工年度": "2016",
            "点検履歴": "未実施",
            "損傷状況": "軽微"
        }

    def _populate_tree(self, attributes, folder_level):
        """TreeWidgetに属性情報を追加"""
        print(f"[AttributeUi] TreeWidget構築開始 - 属性数: {len(attributes)}")
        
        if not attributes:
            print(f"[AttributeUi] 警告: 属性データが空です")
            return
        
        for attr_name, attr_value in attributes.items():
            print(f"[AttributeUi] 追加中: {attr_name} = {attr_value}")
            item = QTreeWidgetItem([attr_name, str(attr_value)])
            # アイテムを編集可能にする
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.attribute_tree.addTopLevelItem(item)
        
        # TreeWidgetを展開
        self.attribute_tree.expandAll()
        
        # 追加されたアイテム数を確認
        item_count = self.attribute_tree.topLevelItemCount()
        print(f"[AttributeUi] TreeWidgetに追加されたアイテム数: {item_count}")

    def _on_item_double_clicked(self, item, column):
        """アイテムがダブルクリックされた時の処理"""
        if column == 0:  # 属性名の列がクリックされた場合
            # 属性名は編集不可なので何もしない
            return
        # 値の列（column == 1）の場合は編集を許可（デフォルト動作）

    def _on_item_changed(self, item, column):
        """TreeWidgetのアイテムが変更された時の処理"""
        if column == 1:  # 値の列が変更された場合
            attr_name = item.text(0)
            new_value = item.text(1)
            print(f"属性変更: {attr_name} = {new_value}")  # デバッグ用

    def _save_attributes(self):
        """属性データを保存"""
        if not self.main_viewer or not self.current_folder_name:
            QMessageBox.warning(self, "警告", "保存対象のフォルダが選択されていません。")
            return
        
        try:
            # TreeWidgetから属性データを取得
            attributes = {}
            root = self.attribute_tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                attr_name = item.text(0)
                attr_value = item.text(1)
                attributes[attr_name] = attr_value
            
            # プロジェクト属性を更新
            self._update_folder_attributes(attributes)
            
            # プロジェクト属性を保存
            self.main_viewer._save_project_attributes()
            
            QMessageBox.information(self, "保存完了", f"'{self.current_folder_name}' の属性情報を保存しました。")
            
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

