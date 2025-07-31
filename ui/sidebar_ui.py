# ui/sidebar_ui.py

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QLabel, 
                             QListWidgetItem, QInputDialog, QMessageBox, QMenu, QTreeWidget, QTreeWidgetItem)

from geometry_manager.geometries_manager import GeometryManager

class SideBarUi(QWidget):
    def __init__(self, manager: GeometryManager, main_viewer=None):
        super().__init__()
        self.manager = manager
        self.main_viewer = main_viewer  # MainViewerの参照を保持
        self.manager.updated.connect(self._refresh_list)
        self.is_project_mode = False  # プロジェクトモードフラグを初期化

        self.label = QLabel("読み込まれたデータ一覧：")
        self.list_widget = QListWidget()
        
        # TreeWidget形式に変更して真の階層構造を実現
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)  # ヘッダーを非表示
        self.tree_widget.setExpandsOnDoubleClick(True)  # ダブルクリックで展開
        
        # 右クリックメニューを有効にする
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self._show_context_menu)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)

        self.tree_widget.itemChanged.connect(self._on_item_check_changed)
        self.tree_widget.itemClicked.connect(self._on_item_clicked)

    def enable_project_mode(self):
        """プロジェクトモードを有効にする"""
        print("プロジェクトモードを有効化")  # デバッグ用
        self.is_project_mode = True
        self.label.setText("プロジェクト構造：")
        self._refresh_list()

    def disable_project_mode(self):
        """プロジェクトモードを無効にする"""
        self.is_project_mode = False
        self.label.setText("読み込まれたデータ一覧：")
        self._refresh_list()

    def _show_context_menu(self, position):
        """右クリックメニューを表示"""
        print(f"右クリックが検出されました。プロジェクトモード: {self.is_project_mode}")  # デバッグ用
        
        if not self.is_project_mode:
            print("プロジェクトモードではないため、メニューを表示しません")  # デバッグ用
            return  # プロジェクトモードでない場合は何もしない
        
        # 右クリックされた位置のアイテムを取得
        clicked_item = self.tree_widget.itemAt(position)
        
        menu = QMenu(self)
        
        # アイテムが選択されている場合の処理
        if clicked_item:
            item_data = clicked_item.data(0, Qt.UserRole)
            if item_data and item_data.get("type") == "folder":
                folder_name = item_data["name"]
                level = item_data.get("level", 1)
                parent = item_data.get("parent", None)
                
                if level == 1:
                    print(f"第1階層フォルダ '{folder_name}' が選択されています")  # デバッグ用
                    # 第2階層作成メニューを追加
                    add_second_level_action = menu.addAction("第2階層作成")
                    add_second_level_action.triggered.connect(
                        lambda: self._on_add_second_level_clicked(folder_name)
                    )
                elif level == 2:
                    print(f"第2階層フォルダ '{folder_name}' が選択されています")  # デバッグ用
                    # 第3階層作成メニューを追加
                    add_third_level_action = menu.addAction("第3階層作成")
                    add_third_level_action.triggered.connect(
                        lambda: self._on_add_third_level_clicked(parent, folder_name)
                    )
            else:
                # 通常のアイテムまたはデータが選択されている場合
                print("通常のアイテムが選択されています")  # デバッグ用
        
        # 常に第1階層作成オプションを表示
        add_first_level_action = menu.addAction("第1階層作成")
        add_first_level_action.triggered.connect(self._on_add_first_level_clicked)
        
        print("右クリックメニューを表示します")  # デバッグ用
        # メニューを表示
        menu.exec_(self.tree_widget.mapToGlobal(position))

    def _on_add_third_level_clicked(self, first_level_parent: str, second_level_parent: str):
        """第3階層フォルダ作成メニューがクリックされた時の処理"""
        print(f"第3階層作成が選択されました。第1階層: {first_level_parent}, 第2階層: {second_level_parent}")  # デバッグ用
        
        if not self.main_viewer or not self.main_viewer.current_project_name:
            QMessageBox.warning(self, "警告", "プロジェクトが作成されていません。")
            return

        # フォルダ名の入力ダイアログ
        folder_name, ok = QInputDialog.getText(
            self, 
            "第3階層フォルダ作成", 
            f"'{first_level_parent} > {second_level_parent}' 内に作成するフォルダ名を入力してください:"
        )
        
        if not ok or not folder_name.strip():
            return
        
        folder_name = folder_name.strip()
        
        # 既存フォルダ名と重複チェック（同じ第2階層フォルダ内で）
        if self._is_duplicate_third_level_folder_name(first_level_parent, second_level_parent, folder_name):
            QMessageBox.warning(self, "警告", f"フォルダ名 '{folder_name}' は既に存在します。")
            return
        
        try:
            # プロジェクト属性に第3階層フォルダ情報を追加
            self._add_third_level_folder_to_project(first_level_parent, second_level_parent, folder_name)
            
            # リストを更新
            self._refresh_list()
            
            QMessageBox.information(self, "成功", f"第3階層フォルダ '{folder_name}' を '{first_level_parent} > {second_level_parent}' 内に作成しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フォルダの作成に失敗しました：\n{e}")

    def _on_add_second_level_clicked(self, parent_folder_name: str):
        """第2階層フォルダ作成メニューがクリックされた時の処理"""
        print(f"第2階層作成が選択されました。親フォルダ: {parent_folder_name}")  # デバッグ用
        
        if not self.main_viewer or not self.main_viewer.current_project_name:
            QMessageBox.warning(self, "警告", "プロジェクトが作成されていません。")
            return

        # フォルダ名の入力ダイアログ
        folder_name, ok = QInputDialog.getText(
            self, 
            "第2階層フォルダ作成", 
            f"'{parent_folder_name}' 内に作成するフォルダ名を入力してください:"
        )
        
        if not ok or not folder_name.strip():
            return
        
        folder_name = folder_name.strip()
        
        # 既存フォルダ名と重複チェック（同じ親フォルダ内で）
        if self._is_duplicate_second_level_folder_name(parent_folder_name, folder_name):
            QMessageBox.warning(self, "警告", f"フォルダ名 '{folder_name}' は既に存在します。")
            return
        
        try:
            # プロジェクト属性に第2階層フォルダ情報を追加
            self._add_second_level_folder_to_project(parent_folder_name, folder_name)
            
            # リストを更新
            self._refresh_list()
            
            QMessageBox.information(self, "成功", f"第2階層フォルダ '{folder_name}' を '{parent_folder_name}' 内に作成しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フォルダの作成に失敗しました：\n{e}")

    def _on_add_first_level_clicked(self):
        """第1階層フォルダ作成メニューがクリックされた時の処理"""
        print("第1階層作成が選択されました")  # デバッグ用
        
        if not self.main_viewer or not self.main_viewer.current_project_name:
            QMessageBox.warning(self, "警告", "プロジェクトが作成されていません。")
            return

        # フォルダ名の入力ダイアログ
        folder_name, ok = QInputDialog.getText(
            self, 
            "第1階層フォルダ作成", 
            "フォルダ名を入力してください:"
        )
        
        if not ok or not folder_name.strip():
            return
        
        folder_name = folder_name.strip()
        
        # 既存フォルダ名と重複チェック
        if self._is_duplicate_folder_name(folder_name):
            QMessageBox.warning(self, "警告", f"フォルダ名 '{folder_name}' は既に存在します。")
            return
        
        try:
            # プロジェクト属性にフォルダ情報を追加
            self._add_folder_to_project(folder_name)
            
            # リストを更新
            self._refresh_list()
            
            QMessageBox.information(self, "成功", f"第1階層フォルダ '{folder_name}' を作成しました。")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"フォルダの作成に失敗しました：\n{e}")

    def _is_duplicate_third_level_folder_name(self, first_level_parent: str, second_level_parent: str, folder_name: str) -> bool:
        """第3階層フォルダ名の重複をチェック"""
        if not self.main_viewer:
            return False
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        
        # 第1階層フォルダが存在するかチェック
        if first_level_parent not in folders:
            return False
        
        # 第2階層フォルダが存在するかチェック
        second_level_folders = folders[first_level_parent].get("second_level_folders", {})
        if second_level_parent not in second_level_folders:
            return False
        
        # 第2階層フォルダ内の第3階層フォルダをチェック
        third_level_folders = second_level_folders[second_level_parent].get("third_level_folders", {})
        return folder_name in third_level_folders

    def _add_third_level_folder_to_project(self, first_level_parent: str, second_level_parent: str, folder_name: str):
        """プロジェクト属性に第3階層フォルダを追加"""
        if not self.main_viewer:
            return
        
        # プロジェクト属性にfoldersキーがない場合は作成
        if "folders" not in self.main_viewer.project_attributes:
            self.main_viewer.project_attributes["folders"] = {}
        
        # 第1階層フォルダが存在しない場合はエラー
        if first_level_parent not in self.main_viewer.project_attributes["folders"]:
            raise Exception(f"第1階層フォルダ '{first_level_parent}' が見つかりません")
        
        # 第2階層フォルダが存在しない場合はエラー
        second_level_folders = self.main_viewer.project_attributes["folders"][first_level_parent].get("second_level_folders", {})
        if second_level_parent not in second_level_folders:
            raise Exception(f"第2階層フォルダ '{second_level_parent}' が見つかりません")
        
        # 第2階層フォルダに第3階層フォルダ用のキーがない場合は作成
        if "third_level_folders" not in second_level_folders[second_level_parent]:
            second_level_folders[second_level_parent]["third_level_folders"] = {}
        
        # 新しい第3階層フォルダを追加
        second_level_folders[second_level_parent]["third_level_folders"][folder_name] = {
            "type": "third_level",
            "first_level_parent": first_level_parent,
            "second_level_parent": second_level_parent,
            "created_date": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
            "objects": {}  # このフォルダに属するオブジェクト
        }
        
        # プロジェクト属性を保存
        self.main_viewer._save_project_attributes()

    def _is_duplicate_second_level_folder_name(self, parent_folder_name: str, folder_name: str) -> bool:
        """第2階層フォルダ名の重複をチェック"""
        if not self.main_viewer:
            return False
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        
        # 親フォルダが存在するかチェック
        if parent_folder_name not in folders:
            return False
        
        # 親フォルダ内の第2階層フォルダをチェック
        second_level_folders = folders[parent_folder_name].get("second_level_folders", {})
        return folder_name in second_level_folders

    def _add_second_level_folder_to_project(self, parent_folder_name: str, folder_name: str):
        """プロジェクト属性に第2階層フォルダを追加"""
        if not self.main_viewer:
            return
        
        # プロジェクト属性にfoldersキーがない場合は作成
        if "folders" not in self.main_viewer.project_attributes:
            self.main_viewer.project_attributes["folders"] = {}
        
        # 親フォルダが存在しない場合はエラー
        if parent_folder_name not in self.main_viewer.project_attributes["folders"]:
            raise Exception(f"親フォルダ '{parent_folder_name}' が見つかりません")
        
        # 親フォルダに第2階層フォルダ用のキーがない場合は作成
        if "second_level_folders" not in self.main_viewer.project_attributes["folders"][parent_folder_name]:
            self.main_viewer.project_attributes["folders"][parent_folder_name]["second_level_folders"] = {}
        
        # 新しい第2階層フォルダを追加
        self.main_viewer.project_attributes["folders"][parent_folder_name]["second_level_folders"][folder_name] = {
            "type": "second_level",
            "parent": parent_folder_name,
            "created_date": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
            "objects": {}  # このフォルダに属するオブジェクト
        }
        
        # プロジェクト属性を保存
        self.main_viewer._save_project_attributes()

    def _is_duplicate_folder_name(self, folder_name: str) -> bool:
        """フォルダ名の重複をチェック"""
        if not self.main_viewer:
            return False
        
        project_attributes = self.main_viewer.project_attributes
        folders = project_attributes.get("folders", {})
        return folder_name in folders

    def _add_folder_to_project(self, folder_name: str):
        """プロジェクト属性にフォルダを追加"""
        if not self.main_viewer:
            return
        
        # プロジェクト属性にfoldersキーがない場合は作成
        if "folders" not in self.main_viewer.project_attributes:
            self.main_viewer.project_attributes["folders"] = {}
        
        # 新しいフォルダを追加
        self.main_viewer.project_attributes["folders"][folder_name] = {
            "type": "first_level",
            "created_date": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
            "objects": {}  # このフォルダに属するオブジェクト
        }
        
        # プロジェクト属性を保存
        self.main_viewer._save_project_attributes()

    def _refresh_list(self): 
        print(f"リスト更新開始 - プロジェクトモード: {self.is_project_mode}")  # デバッグ用
        print(f"main_viewer: {self.main_viewer is not None}")  # デバッグ用
        if self.main_viewer:
            print(f"プロジェクト名: {self.main_viewer.current_project_name}")  # デバッグ用
        
        self.tree_widget.blockSignals(True)
        self.tree_widget.clear()

        # プロジェクトモードの場合はフォルダ構造を表示
        if (self.main_viewer and 
            self.main_viewer.current_project_name and 
            self.is_project_mode):
            print("プロジェクト構造を表示します")  # デバッグ用
            self._refresh_project_structure()
        else:
            # 通常モードの場合は従来通りの表示
            print("通常モードで表示します")  # デバッグ用
            self._refresh_normal_mode()
        
        self.tree_widget.blockSignals(False)
        print(f"リスト更新完了 - アイテム数: {self.tree_widget.topLevelItemCount()}")  # デバッグ用

    def _refresh_project_structure(self):
        """プロジェクト構造を表示"""
        print(f"プロジェクト構造を更新中...")  # デバッグ用
        
        if not self.main_viewer:
            print("main_viewerが設定されていません")
            return
        
        project_attributes = self.main_viewer.project_attributes
        print(f"プロジェクト属性: {project_attributes}")  # デバッグ用
        
        folders = project_attributes.get("folders", {})
        print(f"フォルダ数: {len(folders)}")  # デバッグ用
        
        # 第1階層フォルダを表示
        for folder_name, folder_data in folders.items():
            print(f"フォルダ処理中: {folder_name}, データ: {folder_data}")  # デバッグ用
            
            if folder_data.get("type") == "first_level":
                print(f"第1階層フォルダを追加: {folder_name}")  # デバッグ用
                
                # 第1階層アイテムを作成
                first_level_item = QTreeWidgetItem([f"📁 {folder_name}"])
                first_level_item.setCheckState(0, Qt.Checked)
                first_level_item.setData(0, Qt.UserRole, {"type": "folder", "name": folder_name, "level": 1})
                self.tree_widget.addTopLevelItem(first_level_item)
                
                # 第2階層フォルダを追加
                second_level_folders = folder_data.get("second_level_folders", {})
                print(f"第2階層フォルダ数: {len(second_level_folders)}")  # デバッグ用
                
                for second_folder_name, second_folder_data in second_level_folders.items():
                    print(f"第2階層フォルダを追加: {second_folder_name}")  # デバッグ用
                    
                    # 第2階層アイテムを作成
                    second_level_item = QTreeWidgetItem([f"📂 {second_folder_name}"])
                    second_level_item.setCheckState(0, Qt.Checked)
                    second_level_item.setData(0, Qt.UserRole, {
                        "type": "folder", 
                        "name": second_folder_name, 
                        "level": 2,
                        "parent": folder_name
                    })
                    first_level_item.addChild(second_level_item)
                    
                    # 第3階層フォルダを追加
                    third_level_folders = second_folder_data.get("third_level_folders", {})
                    print(f"第3階層フォルダ数: {len(third_level_folders)}")  # デバッグ用
                    
                    for third_folder_name, third_folder_data in third_level_folders.items():
                        print(f"第3階層フォルダを追加: {third_folder_name}")  # デバッグ用
                        
                        # 第3階層アイテムを作成
                        third_level_item = QTreeWidgetItem([f"📂 {third_folder_name}"])
                        third_level_item.setCheckState(0, Qt.Checked)
                        third_level_item.setData(0, Qt.UserRole, {
                            "type": "folder", 
                            "name": third_folder_name, 
                            "level": 3,
                            "first_level_parent": folder_name,
                            "second_level_parent": second_folder_name
                        })
                        second_level_item.addChild(third_level_item)
                
                # 第1階層アイテムをデフォルトで展開
                first_level_item.setExpanded(True)
        
        # 通常のデータアイテムも表示
        data_items_count = len(self.manager.items)
        print(f"データアイテム数: {data_items_count}")  # デバッグ用
        
        for item in self.manager.items:
            data_item = QTreeWidgetItem([f"📄 {item.name}"])
            data_item.setCheckState(0, Qt.Checked if item.visible else Qt.Unchecked)
            data_item.setData(0, Qt.UserRole, {"type": "data", "name": item.name})
            self.tree_widget.addTopLevelItem(data_item)

    def _refresh_normal_mode(self):
        """通常モードのリスト表示"""
        for item in self.manager.items:
            tree_item = QTreeWidgetItem([item.name])
            tree_item.setCheckState(0, Qt.Checked if item.visible else Qt.Unchecked)
            self.tree_widget.addTopLevelItem(tree_item)

    def _on_item_check_changed(self, tree_item, column):
        # プロジェクトモードの場合
        if (self.main_viewer and 
            self.main_viewer.current_project_name and 
            self.is_project_mode):
            item_data = tree_item.data(0, Qt.UserRole)
            if item_data and item_data.get("type") == "data":
                name = item_data["name"]
                visible = tree_item.checkState(0) == Qt.Checked
                print(f"🔁 {name} -> {'表示' if visible else '非表示'}")
                self.manager.set_visibility(name, visible)
        else:
            # 通常モードの場合（従来通り）
            name = tree_item.text(0)
            visible = tree_item.checkState(0) == Qt.Checked
            print(f"🔁 {name} -> {'表示' if visible else '非表示'}")
            self.manager.set_visibility(name, visible)

    def _on_item_clicked(self, tree_item, column):
        if tree_item is None: 
            return
        
        print(f"[SideBar] アイテムクリック: {tree_item.text(0)}")  # デバッグ用
        
        # プロジェクトモードの場合
        if (self.main_viewer and 
            self.main_viewer.current_project_name and 
            self.is_project_mode):
            print(f"[SideBar] プロジェクトモードで処理中")  # デバッグ用
            
            item_data = tree_item.data(0, Qt.UserRole)
            print(f"[SideBar] アイテムデータ: {item_data}")  # デバッグ用
            
            if item_data:
                if item_data.get("type") == "folder":
                    folder_name = item_data["name"]
                    level = item_data.get("level", 1)
                    parent = item_data.get("parent", None)
                    
                    print(f"[SideBar] フォルダ選択: {folder_name}, レベル: {level}, 親: {parent}")  # デバッグ用
                    
                    if level == 1:
                        print(f"[SideBar] 📁 第1階層フォルダ選択: {folder_name}")
                        # attribute_uiに第1階層フォルダの属性情報を表示
                        if hasattr(self.main_viewer, 'attribute_ui'):
                            print(f"[SideBar] attribute_uiに属性表示を要求")
                            self.main_viewer.attribute_ui.show_folder_attributes(folder_name, level)
                        else:
                            print(f"[SideBar] エラー: attribute_uiが見つかりません")
                    elif level == 2:
                        print(f"[SideBar] 📂 第2階層フォルダ選択: {folder_name} (親: {parent})")
                        # attribute_uiに第2階層フォルダの属性情報を表示
                        if hasattr(self.main_viewer, 'attribute_ui'):
                            print(f"[SideBar] attribute_uiに第2階層属性表示を要求")
                            self.main_viewer.attribute_ui.show_folder_attributes(folder_name, level, parent)
                        else:
                            print(f"[SideBar] エラー: attribute_uiが見つかりません")
                    elif level == 3:
                        first_level_parent = item_data.get("first_level_parent", "")
                        second_level_parent = item_data.get("second_level_parent", "")
                        print(f"[SideBar] 📄 第3階層フォルダ選択: {folder_name} (親: {first_level_parent} > {second_level_parent})")
                        # attribute_uiに第3階層フォルダの属性情報を表示
                        if hasattr(self.main_viewer, 'attribute_ui'):
                            print(f"[SideBar] attribute_uiに第3階層属性表示を要求")
                            self.main_viewer.attribute_ui.show_folder_attributes(folder_name, level, f"{first_level_parent} > {second_level_parent}")
                        else:
                            print(f"[SideBar] エラー: attribute_uiが見つかりません")
                    
                elif item_data.get("type") == "data":
                    name = item_data["name"]
                    print(f"[SideBar] 🎯 データ選択: {name}")
                    self.manager.select(name)
                    # データ選択時は属性表示をクリア
                    if hasattr(self.main_viewer, 'attribute_ui'):
                        self.main_viewer.attribute_ui.hide_attributes()
            else:
                print(f"[SideBar] 警告: アイテムデータがありません")
                # アイテムデータがない場合は属性表示をクリア
                if hasattr(self.main_viewer, 'attribute_ui'):
                    self.main_viewer.attribute_ui.hide_attributes()
        else:
            # 通常モードの場合（従来通り）
            name = tree_item.text(0)
            print(f"[SideBar] 🎯 通常モード選択: {name}")
            self.manager.select(name)
