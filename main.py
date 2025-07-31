# main.py

import os
import json
import sys
from PyQt5.QtWidgets import QApplication, QAction, QMainWindow, QFileDialog, QMessageBox, QWidget, QHBoxLayout, QInputDialog, QDialog
from PyQt5.QtCore import QDateTime

from di.container import load_point_cloud_usecase
from di.container import save_point_cloud_usecase
from di.container import load_model_usecase
from di.container import save_model_usecase
from ui.point_cloud_ui import PointCloudUi
from ui.sidebar_ui import SideBarUi
from ui.attribute_ui import AttributeUi
from geometry_manager.geometries_manager import GeometryManager

class MainViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bridge Cloud Drafter")
        # self.setGeometry(50, 70, 1700, 1100)
        self.setGeometry(100, 100, 1900, 1400)

        # 状態変数の管理クラスの初期化
        self.geometry_manager = GeometryManager()

        # ウィジェットの初期化
        self.point_cloud_ui = PointCloudUi(self.geometry_manager)
        self.sidebar_ui = SideBarUi(self.geometry_manager, self)
        self.attribute_ui = AttributeUi(self.geometry_manager, self)

        # self._atribute_ui_hide() # 初期状態では非表示

        # usecaseの初期化
        self.load_point_cloud_usecase = load_point_cloud_usecase(self.geometry_manager)
        self.save_point_cloud_usecase = save_point_cloud_usecase(self.geometry_manager)
        self.load_model_usecase = load_model_usecase(self.geometry_manager)
        self.save_model_usecase = save_model_usecase(self.geometry_manager)

        # トップメニュー作成
        self._create_menu_bar()

        # 中央ウィジェットとレイアウト
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # レイアウトに追加
        main_layout.addWidget(self.sidebar_ui,      1)  # 左は固定
        main_layout.addWidget(self.point_cloud_ui,  4)  # 中央
        main_layout.addWidget(self.attribute_ui,    1)  # 右

        self.setCentralWidget(central_widget)

        # プロジェクト管理用の変数
        self.current_project_name = None
        self.current_project_path = None
        self.project_attributes = {}  # プロジェクトの属性データ

    def _create_menu_bar(self):
        menu_bar = self.menuBar()

        # ファイルメニュー
        file_menu = menu_bar.addMenu("ファイル")

        # 点群を読み込む
        load_point_action = QAction("点群を読み込む", self)
        load_point_action.triggered.connect(self._on_click_load_point)
        file_menu.addAction(load_point_action)

        # 点群を保存する
        save_point_action = QAction("点群を保存する", self)
        save_point_action.triggered.connect(self._on_click_save_point)
        file_menu.addAction(save_point_action)

        # モデルを読み込む
        load_model_action = QAction("モデルを読み込む", self)
        load_model_action.triggered.connect(self._on_click_load_model)
        file_menu.addAction(load_model_action)

        # モデルを保存する
        save_model_action = QAction("モデルを保存する", self)
        save_model_action.triggered.connect(self._on_click_save_model)
        file_menu.addAction(save_model_action)

        # ツールメニュー
        tools_menu = menu_bar.addMenu("ツール")

        # テクスチャマッピング
        texture_mapping_action = QAction("テクスチャマッピング", self)

        # モデル生成メニュー
        generate_model_menu = menu_bar.addMenu("モデル生成")

        # パラメトリック生成
        parametric_action = QAction("パラメトリック生成", self)

        # プロジェクトメニュー（新規追加）
        project_menu = menu_bar.addMenu("プロジェクト")
        
        # プロジェクト作成
        create_project_action = QAction("プロジェクト作成", self)
        create_project_action.triggered.connect(self._on_click_create_project)
        project_menu.addAction(create_project_action)

        # プロジェクト読み込み
        load_project_action = QAction("プロジェクト読み込み", self)
        load_project_action.triggered.connect(self._on_click_load_project)
        project_menu.addAction(load_project_action)


    def _on_click_load_point(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "点群ファイルを選択", "", "PLY Files (*.ply);;All Files (*)")
        if file_path:
            try:
                self.load_point_cloud_usecase.exec(file_path)
                QMessageBox.information(self, "成功", f"点群を読み込みました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"読み込みに失敗しました：\n{e}")
        else:
            QMessageBox.critical(self, "エラー", f"ファイルを選択してください")
    
    def _on_click_save_point(self):
        items = self.geometry_manager.get_selected_items()
        if not items:
             QMessageBox.critical(self, "エラー", f"保存する点群を選択してください")
             return
        file_path, _ = QFileDialog.getSaveFileName(self, "点群を保存", "", "PLY Files (*.ply);;All Files (*)")
        if file_path:
            try:
                self.save_point_cloud_usecase.exec(file_path, items)
                QMessageBox.information(self, "保存完了", f"点群を保存しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました：\n{e}")
        else:
            QMessageBox.critical(self, "エラー", f"ファイルを選択してください")
    
    def _on_click_load_model(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "モデルファイルを選択", "", "3Dモデル (*.stl *.obj);;STL Files (*.stl);;OBJ Files (*.obj);;All Files (*)(*.stl *.obj);;STL Files (*.stl);;OBJ Files (*.obj);;All Files (*)")
        if file_path:
            try:
                self.load_model_usecase.exec(file_path)
                QMessageBox.information(self, "成功", f"モデルを読み込みました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"読み込みに失敗しました：\n{e}")
        else:
            QMessageBox.critical(self, "エラー", f"ファイルを選択してください")
    
    def _on_click_save_model(self):
        items = self.geometry_manager.get_selected_items()
        if not items:
             QMessageBox.critical(self, "エラー", f"保存するモデルを選択してください")
             return
        file_path, _ = QFileDialog.getSaveFileName(self, "モデルを保存", "", "3Dモデル (*.stl *.obj);;STL Files (*.stl);;OBJ Files (*.obj);;All Files (*)")
        if file_path:
            try:
                self.save_model_usecase.exec(file_path, items)
                QMessageBox.information(self, "保存完了", f"モデルを保存しました")
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"保存に失敗しました：\n{e}")
        else:
            QMessageBox.critical(self, "エラー", f"ファイルを選択してください")
        
    def _point_cloud_ui_show(self):
        self.point_cloud_ui.show()

    def _point_cloud_ui_hide(self):
        self.point_cloud_ui.hide()
    
    def _sidebar_ui_show(self):
        self.sidebar_ui.show()

    def _sidebar_ui_hide(self):
        self.sidebar_ui.hide()

    def _atribute_ui_show(self):
        self.attribute_ui.show()
    
    def _atribute_ui_hide(self):
        self.attribute_ui.hide()
    
    def _on_click_create_project(self):
        """プロジェクト作成ボタンが押された時の処理"""
        try:
            # プロジェクト名の入力ダイアログ
            project_name, ok = QInputDialog.getText(
                self, 
                "プロジェクト作成", 
                "プロジェクト名を入力してください:"
            )
            
            if not ok or not project_name.strip():
                return
            
            # プロジェクトフォルダの選択
            project_dir = QFileDialog.getExistingDirectory(
                self, 
                "プロジェクトを保存するフォルダを選択"
            )
            
            if not project_dir:
                return
            
            # プロジェクトフォルダを作成
            self.current_project_name = project_name.strip()
            self.current_project_path = os.path.join(project_dir, self.current_project_name)
            
            if not os.path.exists(self.current_project_path):
                os.makedirs(self.current_project_path)
            
            # プロジェクト属性ファイルの初期化
            self._initialize_project_attributes()
            
            # UIレイアウトを変更
            self._atribute_ui_show()
            self.sidebar_ui.enable_project_mode()
            
            # ウィンドウタイトルを更新
            self.setWindowTitle(f"Bridge Cloud Drafter - {self.current_project_name}")
            
            QMessageBox.information(self, "プロジェクト作成", f"プロジェクト '{self.current_project_name}' が作成されました")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"プロジェクト作成に失敗しました：\n{e}")

    def _on_click_load_project(self):
        """プロジェクト読み込みボタンが押された時の処理"""
        try:
            # プロジェクトフォルダの選択
            project_dir = QFileDialog.getExistingDirectory(
                self, 
                "読み込むプロジェクトフォルダを選択"
            )
            
            if not project_dir:
                return
            
            # project_attributes.jsonファイルの存在確認
            attributes_file = os.path.join(project_dir, "project_attributes.json")
            if not os.path.exists(attributes_file):
                QMessageBox.warning(self, "警告", "選択されたフォルダにproject_attributes.jsonが見つかりません。")
                return
            
            # プロジェクト属性を読み込み
            try:
                with open(attributes_file, 'r', encoding='utf-8') as f:
                    self.project_attributes = json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"プロジェクトファイルの読み込みに失敗しました：\n{e}")
                return
            
            # プロジェクト情報を設定
            project_info = self.project_attributes.get("project_info", {})
            self.current_project_name = project_info.get("name", os.path.basename(project_dir))
            self.current_project_path = project_dir
            
            # UIをプロジェクトモードに変更
            self._atribute_ui_show()
            self.sidebar_ui.enable_project_mode()
            
            # ウィンドウタイトルを更新
            self.setWindowTitle(f"Bridge Cloud Drafter - {self.current_project_name}")
            
            # 成功メッセージ
            QMessageBox.information(self, "プロジェクト読み込み", 
                                f"プロジェクト '{self.current_project_name}' を読み込みました\n"
                                f"作成日: {project_info.get('created_date', '不明')}\n"
                                f"バージョン: {project_info.get('version', '不明')}")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"プロジェクトの読み込みに失敗しました：\n{e}")

    def _on_click_close_project(self):
        """プロジェクトを閉じる処理"""
        if not self.current_project_name:
            QMessageBox.information(self, "情報", "現在開いているプロジェクトはありません。")
            return
        
        # 確認ダイアログ
        reply = QMessageBox.question(self, "プロジェクトを閉じる", 
                                    f"プロジェクト '{self.current_project_name}' を閉じますか？",
                                    QMessageBox.Yes | QMessageBox.No, 
                                    QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # プロジェクト情報をクリア
            self.current_project_name = None
            self.current_project_path = None
            self.project_attributes = {}
            
            # UIを通常モードに戻す
            self.sidebar_ui.disable_project_mode()
            self._atribute_ui_hide()
            
            # ウィンドウタイトルを元に戻す
            self.setWindowTitle("Bridge Cloud Drafter")
            
            QMessageBox.information(self, "プロジェクト終了", "プロジェクトを閉じました。")

    def _initialize_project_attributes(self):
        """プロジェクト属性データの初期化"""
        self.project_attributes = {
            "project_info": {
                "name": self.current_project_name,
                "created_date": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss"),
                "version": "1.0"
            },
            "folders": {},  # 追加：第1階層フォルダ管理
            "objects": {}  # オブジェクトごとの属性データ
        }
        self._save_project_attributes()

    def _save_project_attributes(self):
        """プロジェクト属性をJSONファイルに保存"""
        if not self.current_project_path:
            return
        
        attributes_file = os.path.join(self.current_project_path, "project_attributes.json")
        try:
            with open(attributes_file, 'w', encoding='utf-8') as f:
                json.dump(self.project_attributes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"属性データの保存に失敗しました：\n{e}")

    def _load_project_attributes(self, project_path=None):
        """プロジェクト属性をJSONファイルから読み込み"""
        if not project_path:
            project_path = self.current_project_path
        
        if not project_path:
            return
        
        attributes_file = os.path.join(project_path, "project_attributes.json")
        try:
            if os.path.exists(attributes_file):
                with open(attributes_file, 'r', encoding='utf-8') as f:
                    self.project_attributes = json.load(f)
                    return True
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"属性データの読み込みに失敗しました：\n{e}")
        return False

    def get_object_attributes(self, object_name: str):
        """指定されたオブジェクトの属性データを取得"""
        return self.project_attributes.get("objects", {}).get(object_name, {})

    def set_object_attributes(self, object_name: str, attributes: dict):
        """指定されたオブジェクトの属性データを設定"""
        if "objects" not in self.project_attributes:
            self.project_attributes["objects"] = {}
        
        self.project_attributes["objects"][object_name] = attributes
        self._save_project_attributes()

def main():
    app = QApplication(sys.argv)
    viewer = MainViewer()
    viewer.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
