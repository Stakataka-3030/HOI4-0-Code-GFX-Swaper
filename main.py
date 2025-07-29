import os
import re
import json
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSplitter, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QFileDialog, QTreeWidget, 
                            QTreeWidgetItem, QTextEdit, QGraphicsView, QGraphicsScene, 
                            QGraphicsPixmapItem, QSizePolicy, QMessageBox, QGraphicsLineItem,
                            QFrame, QDialog)
from PyQt5.QtCore import Qt, QDir, QSize, QFileInfo, QMimeData
from PyQt5.QtGui import (QPixmap, QImage, QImageReader, QColor, QFont, 
                        QDragEnterEvent, QDropEvent)

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("使用说明和介绍")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setStyleSheet("font-size: 12px;")
        
        # 设置帮助文本内容
        help_content = """
        <h2>文件查看器工具</h2>
        <p><b>作者：</b>Stakataka_3030</p>
        <p><b>Github地址：</b><a href="https://github.com/Stakataka-3030/HOI4-0-Code-GFX-Swaper/">https://github.com/Stakataka-3030/HOI4-0-Code-GFX-Swaper/</a></p>
        <p>此工具基于GPL2.0开源</p>
        
        <h3>使用说明：</h3>
        <ul>
            <li>点选特定文件可快速替换对应文件，您不需要手动保持名称或格式一致，工具会自动完成替换和格式修改</li>
            <li>导出和导入配置功能会记录绝对路径，因此请不要移动图片文件或mod文件，否则将不得不重新选择</li>
            <li>用文件资源管理器导航到steam安装路径\steamapps\workshop\content\394360\modid（您可以在创意工坊链接的末尾找到modid，应当是一串9位或10位数字）</li>
            <li>点选"导出mod文件"会要求您选择一个文件夹。工具会在该文件夹下生成gfx文件夹。您应当将gfx文件夹复制到您在启动器创建的mod的文件夹中。并在您mod的descriptor.mod中加入dependencies={"xxx"}，其中xxx为屏幕上方显示的mod名称。</li>
            <li>然后，您可以启动游戏进行测试。</li>
        </ul>

        <p>如果您的文件转化成dds时报错，请安装nvidia texture tools exporter</p>
        """
        
        self.help_text.setHtml(help_content)
        layout.addWidget(self.help_text)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

class DropContainer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 5px;
            }
            QFrame:hover {
                background-color: #e0e0e0;
                border: 2px dashed #888;
            }
        """)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.label = QLabel("拖放替换文件到这里")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont("Arial", 10))
        self.layout.addWidget(self.label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: #e0f0ff;
                    border: 2px dashed #0066cc;
                    border-radius: 5px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 5px;
            }
            QFrame:hover {
                background-color: #e0e0e0;
                border: 2px dashed #888;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 2px dashed #aaa;
                border-radius: 5px;
            }
            QFrame:hover {
                background-color: #e0e0e0;
                border: 2px dashed #888;
            }
        """)
        
        if not self.parent_app.current_selected_file:
            QMessageBox.warning(self, "警告", "请先选择要替换的文件")
            return
        
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ('.png', '.dds', '.tga'):
                    self.parent_app.replacement_files[self.parent_app.current_selected_file] = file_path
                    self.parent_app.display_file_info(self.parent_app.current_selected_file)
                    self.parent_app.update_file_tree_colors()
                    break
                else:
                    QMessageBox.warning(self, "错误", "只支持.png, .dds和.tga格式的图片文件")

class FileViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (之前的初始化代码保持不变)
        
        # 在顶部控制栏添加导出MOD按钮
        self.export_mod_btn = QPushButton("导出MOD文件")
        self.export_mod_btn.clicked.connect(self.export_mod_files)
        self.top_layout.addWidget(self.export_mod_btn)
        
        # ... (其余初始化代码保持不变)

    def export_mod_files(self):
        if not self.replacement_files:
            QMessageBox.warning(self, "警告", "没有可导出的替换文件")
            return
        
        # 让用户选择导出路径
        export_dir = QFileDialog.getExistingDirectory(
            self, "选择导出目录", "", QFileDialog.ShowDirsOnly
        )
        
        if not export_dir:
            return
        
        # 创建gfx文件夹
        gfx_dir = os.path.join(export_dir, "gfx")
        try:
            os.makedirs(gfx_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建gfx文件夹失败: {str(e)}")
            return
        
        success_count = 0
        fail_count = 0
        
        for orig_path, repl_path in self.replacement_files.items():
            try:
                # 获取相对于gfx文件夹的相对路径
                if not orig_path.startswith(self.gfx_folder_path):
                    print(f"跳过非gfx文件夹下的文件: {orig_path}")
                    fail_count += 1
                    continue
                
                rel_path = os.path.relpath(orig_path, self.gfx_folder_path)
                target_path = os.path.join(gfx_dir, rel_path)
                
                # 创建目标文件夹结构
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 获取原始文件扩展名和目标文件扩展名
                orig_ext = os.path.splitext(orig_path)[1].lower()
                repl_ext = os.path.splitext(repl_path)[1].lower()
                
                # 如果扩展名相同，直接复制
                if orig_ext == repl_ext:
                    shutil.copy2(repl_path, target_path)
                else:
                    # 需要转换格式
                    self.convert_image_format(repl_path, target_path, orig_ext)
                
                success_count += 1
            except Exception as e:
                print(f"导出文件失败: {orig_path} -> {target_path}, 错误: {str(e)}")
                fail_count += 1
        
        # 显示导出结果
        msg = f"导出完成!\n成功: {success_count} 个文件\n失败: {fail_count} 个文件"
        if fail_count > 0:
            msg += "\n\n失败的文件请查看控制台输出"
        
        QMessageBox.information(self, "导出结果", msg)
    
    def convert_image_format(self, src_path, dst_path, target_ext):
        """转换图片格式到目标扩展名"""
        target_ext = target_ext.lower()
        
        if target_ext == '.dds':
            # 使用Pillow转换为DDS格式，ARGB8，无mipmap
            from PIL import Image
            img = Image.open(src_path)
            
            # 确保图像是RGBA模式
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 保存为DDS格式，ARGB8，无mipmap
            try:
                # 使用Pillow的DDS插件保存
                img.save(dst_path, format='DDS', 
                        dds_format='ARGB8', 
                        mipmap=False)
            except Exception as e:
                # 如果直接保存失败，尝试通过中间转换
                temp_path = dst_path + '.png'
                img.save(temp_path, format='PNG')
                
                # 使用外部工具转换
                try:
                    self.convert_to_dds_with_external_tool(temp_path, dst_path)
                    os.remove(temp_path)
                except Exception as e:
                    raise Exception(f"DDS转换失败: {str(e)}")
                    
        elif target_ext == '.tga':
            # 转换为TGA格式
            from PIL import Image
            img = Image.open(src_path)
            img.save(dst_path, format='TGA')
        else:
            # 对于其他格式(PNG)，使用Qt的转换功能
            reader = QImageReader(src_path)
            image = reader.read()
            if image.isNull():
                raise Exception("无法读取源图片")
            
            # 根据目标格式保存
            if target_ext == '.png':
                image.save(dst_path, 'PNG')
            else:
                raise Exception(f"不支持的转换格式: {target_ext}")
    
    def convert_to_dds_with_external_tool(self, src_path, dst_path):
        from PIL import Image
        img = Image.open(src_path)
        img.save(dst_path, format='DDS', dds_format='ARGB8', mipmap=False)

    def show_help(self):
        """显示使用说明对话框"""
        help_dialog = HelpDialog(self)
        help_dialog.exec_()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HOI4 0代码萌化和和谐工具")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主窗口部件
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 顶部控制栏
        self.top_bar = QWidget()
        self.top_layout = QHBoxLayout()
        self.top_bar.setLayout(self.top_layout)
        
        # 添加使用说明按钮
        self.help_btn = QPushButton("使用说明和介绍")
        self.help_btn.clicked.connect(self.show_help)
        self.top_layout.addWidget(self.help_btn)
        
        self.select_file_btn = QPushButton("选择 descriptor.mod 文件")
        self.select_file_btn.clicked.connect(self.select_file)
        self.top_layout.addWidget(self.select_file_btn)
        
        # 导入导出按钮
        self.import_export_container = QWidget()
        self.import_export_layout = QHBoxLayout()
        self.import_export_container.setLayout(self.import_export_layout)
        
        self.export_btn = QPushButton("导出替换配置")
        self.export_btn.clicked.connect(self.export_replacements)
        self.import_btn = QPushButton("导入替换配置")
        self.import_btn.clicked.connect(self.import_replacements)
        
        self.import_export_layout.addWidget(self.export_btn)
        self.import_export_layout.addWidget(self.import_btn)
        self.top_layout.addWidget(self.import_export_container)
        
        # 导出MOD按钮
        self.export_mod_btn = QPushButton("导出MOD文件")
        self.export_mod_btn.clicked.connect(self.export_mod_files)
        self.top_layout.addWidget(self.export_mod_btn)
        
        # 顶部信息显示区域
        self.info_container = QWidget()
        self.info_layout = QVBoxLayout()
        self.info_container.setLayout(self.info_layout)
        
        self.file_info_label = QLabel("未选择文件")
        self.mod_info_label = QLabel("名称: 未读取 | 版本: 未读取")
        self.mod_info_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.info_layout.addWidget(self.file_info_label)
        self.info_layout.addWidget(self.mod_info_label)
        
        self.top_layout.addWidget(self.info_container, 1)
        
        self.main_layout.addWidget(self.top_bar)
        
        # 中间分割区域
        self.middle_splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.middle_splitter, 1)
        
        # 左侧文件树
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_panel.setLayout(self.left_layout)
        
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("文件结构")
        self.file_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #e0e0e0;
            }
        """)
        self.file_tree.itemClicked.connect(self.on_file_selected)
        
        self.left_layout.addWidget(self.file_tree)
        self.middle_splitter.addWidget(self.left_panel)
        
        # 右侧预览区域
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_panel.setLayout(self.right_layout)
        
        # 文件信息显示
        self.file_info_text = QTextEdit()
        self.file_info_text.setReadOnly(True)
        self.file_info_text.setStyleSheet("font-size: 12px;")
        self.right_layout.addWidget(self.file_info_text, 1)
        
        # 预览区域
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout()
        self.preview_container.setLayout(self.preview_layout)
        
        # 原始文件预览 (缩小显示)
        self.original_container = QWidget()
        self.original_layout = QVBoxLayout()
        self.original_container.setLayout(self.original_layout)
        
        self.original_label = QLabel("原始文件")
        self.original_label.setAlignment(Qt.AlignCenter)
        self.original_layout.addWidget(self.original_label)
        
        self.original_preview = QGraphicsView()
        self.original_scene = QGraphicsScene()
        self.original_preview.setScene(self.original_scene)
        self.original_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_preview.setMinimumSize(300, 300)
        self.original_layout.addWidget(self.original_preview)
        
        # 箭头容器
        self.arrow_container = QWidget()
        self.arrow_container.setFixedWidth(120)
        self.arrow_layout = QVBoxLayout()
        self.arrow_container.setLayout(self.arrow_layout)
        self.arrow_layout.addStretch()
        
        # 添加箭头图形
        self.arrow_scene = QGraphicsScene()
        self.arrow_view = QGraphicsView(self.arrow_scene)
        self.arrow_view.setStyleSheet("background: transparent; border: none;")
        self.arrow_layout.addWidget(self.arrow_view)
        self.arrow_layout.addStretch()
        
        # 替换按钮和拖放区域
        self.replace_container = QWidget()
        self.replace_layout = QVBoxLayout()
        self.replace_container.setLayout(self.replace_layout)
        
        self.replace_btn = QPushButton("选择替换文件")
        self.replace_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.replace_btn.clicked.connect(self.select_replacement_file)
        self.replace_btn.setEnabled(False)
        self.replace_layout.addWidget(self.replace_btn)
        
        # 添加拖放区域
        self.drop_area = DropContainer(self)
        self.drop_area.setFixedHeight(100)
        self.replace_layout.addWidget(self.drop_area)
        
        # 替换文件预览 (放大显示)
        self.replacement_container = QWidget()
        self.replacement_layout = QVBoxLayout()
        self.replacement_container.setLayout(self.replacement_layout)
        
        self.replacement_label = QLabel("替换文件")
        self.replacement_label.setAlignment(Qt.AlignCenter)
        self.replacement_layout.addWidget(self.replacement_label)
        
        self.replacement_preview = QGraphicsView()
        self.replacement_scene = QGraphicsScene()
        self.replacement_preview.setScene(self.replacement_scene)
        self.replacement_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.replacement_preview.setMinimumSize(400, 400)
        self.replacement_layout.addWidget(self.replacement_preview)
        
        # 组装预览区域
        self.preview_layout.addWidget(self.original_container, 1)
        self.preview_layout.addWidget(self.arrow_container)
        self.preview_layout.addWidget(self.replace_container)
        self.preview_layout.addWidget(self.replacement_container, 2)
        
        self.right_layout.addWidget(self.preview_container, 2)
        
        self.middle_splitter.addWidget(self.right_panel)

        self.export_mod_btn = QPushButton("导出MOD文件")
        self.export_mod_btn.clicked.connect(self.export_mod_files)
        self.top_layout.addWidget(self.export_mod_btn)
        
        # 初始化变量
        self.current_file_path = ""
        self.gfx_folder_path = ""
        self.mod_folder = ""
        self.replacement_files = {}  # 存储替换文件路径 {原文件路径: 替换文件路径}
        self.current_selected_file = None
        self.all_files = []  # 存储所有文件路径
        
        # 设置分割器初始比例
        self.middle_splitter.setSizes([350, 1050])
    
    def export_replacements(self):
        if not self.replacement_files:
            QMessageBox.warning(self, "警告", "没有可导出的替换配置")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出替换配置", "", "JSON 文件 (*.json)"
        )
        
        if file_path:
            try:
                # 构建导出数据，包含替换配置和当前mod路径
                export_data = {
                    "descriptor_path": os.path.normpath(self.current_file_path),
                    "replacements": {
                        os.path.normpath(k): os.path.normpath(v) 
                        for k, v in self.replacement_files.items()
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "成功", "替换配置已成功导出")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出替换配置时出错: {str(e)}")
    
    def import_replacements(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入替换配置", "", "JSON 文件 (*.json)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # 检查是否包含descriptor路径
                if "descriptor_path" not in import_data:
                    QMessageBox.warning(self, "警告", "配置文件不完整，缺少descriptor.mod路径")
                    return
                
                # 询问用户是否加载关联的mod
                reply = QMessageBox.question(
                    self, "确认", 
                    f"是否加载关联的mod文件?\n路径: {import_data['descriptor_path']}",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    # 尝试加载关联的mod文件
                    if os.path.exists(import_data["descriptor_path"]):
                        self.current_file_path = import_data["descriptor_path"]
                        self.process_descriptor_file(self.current_file_path)
                    else:
                        QMessageBox.warning(self, "警告", "无法找到关联的mod文件，请手动选择")
                
                # 处理替换配置
                valid_replacements = {}
                for orig, repl in import_data.get("replacements", {}).items():
                    orig_path = os.path.normpath(orig)
                    repl_path = os.path.normpath(repl)
                    
                    if os.path.exists(repl_path):
                        valid_replacements[orig_path] = repl_path
                    else:
                        print(f"警告: 替换文件不存在: {repl_path}")
                
                self.replacement_files = valid_replacements
                
                # 更新UI
                if self.current_selected_file:
                    self.display_file_info(self.current_selected_file)
                self.update_file_tree_colors()
                
                QMessageBox.information(self, "成功", f"已导入 {len(valid_replacements)} 个替换配置")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入替换配置时出错: {str(e)}")
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 descriptor.mod 文件", "", "MOD 文件 (*.mod)"
        )
        
        if file_path and os.path.basename(file_path) == "descriptor.mod":
            self.current_file_path = file_path
            self.process_descriptor_file(file_path)
        elif file_path:
            QMessageBox.warning(self, "错误", "请选择名为 descriptor.mod 的文件")
    
    def process_descriptor_file(self, file_path):
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析名称和版本
            name_match = re.search(r'name\s*=\s*"([^"]+)"', content)
            version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
            
            name = name_match.group(1) if name_match else "未找到"
            version = version_match.group(1) if version_match else "未找到"
            
            # 更新顶部信息显示
            self.mod_info_label.setText(f"名称: {name} | 版本: {version}")
            
            # 获取MOD文件夹
            self.mod_folder = os.path.dirname(file_path)
            self.file_info_label.setText(f"MOD路径: {self.mod_folder}")
            
            # 查找gfx文件夹
            self.gfx_folder_path = os.path.join(self.mod_folder, "gfx")
            if os.path.exists(self.gfx_folder_path):
                self.load_folder_structure(self.gfx_folder_path)
            else:
                self.file_info_text.setText("未找到gfx文件夹")
            
        except Exception as e:
            self.file_info_text.setText(f"处理文件时出错: {str(e)}")
    
    def load_folder_structure(self, folder_path):
        self.file_tree.clear()
        self.all_files = []
        
        # 创建根节点
        root_item = QTreeWidgetItem(self.file_tree)
        root_item.setText(0, os.path.basename(folder_path))
        root_item.setData(0, Qt.UserRole, folder_path)
        
        # 递归加载文件夹结构
        self.build_tree(folder_path, root_item)
        
        # 展开所有节点
        self.file_tree.expandAll()
    
    def build_tree(self, folder_path, parent_item):
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                
                if os.path.isdir(item_path):
                    # 如果是文件夹，创建子节点并递归
                    dir_item = QTreeWidgetItem(parent_item)
                    dir_item.setText(0, item)
                    dir_item.setData(0, Qt.UserRole, item_path)
                    self.build_tree(item_path, dir_item)
                elif item.lower().endswith(('.png', '.dds', '.tga')):
                    # 如果是图片文件，添加到列表
                    file_item = QTreeWidgetItem(parent_item)
                    file_item.setText(0, item)
                    file_item.setData(0, Qt.UserRole, item_path)
                    self.all_files.append(item_path)
                    
                    # 如果是替换文件，设置为红色
                    if item_path in self.replacement_files:
                        file_item.setForeground(0, QColor(255, 0, 0))
        except Exception as e:
            print(f"加载文件夹时出错: {str(e)}")
    
    def on_file_selected(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        
        if os.path.isfile(file_path):
            self.current_selected_file = file_path
            self.replace_btn.setEnabled(True)
            self.display_file_info(file_path)
    
    def display_file_info(self, file_path):
        file_info = f"当前文件: {os.path.basename(file_path)}\n"
        file_info += f"路径: {file_path}\n"
        file_info += f"大小: {os.path.getsize(file_path)/1024:.2f} KB\n"
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # 清除所有场景
        self.original_scene.clear()
        self.replacement_scene.clear()
        self.arrow_scene.clear()
        
        # 显示原始文件
        if ext in ('.png', '.dds', '.tga'):
            try:
                # 显示原始文件 (缩小)
                self.display_image(file_path, self.original_scene, is_original=True)
                
                # 如果有替换文件，显示替换文件 (放大)
                if file_path in self.replacement_files:
                    self.display_image(self.replacement_files[file_path], self.replacement_scene, is_original=False)
                    self.draw_arrow()
                    file_info += f"\n已选择替换文件: {os.path.basename(self.replacement_files[file_path])}"
                
                # 获取图片尺寸
                width, height = self.get_image_size(file_path)
                file_info += f"\n尺寸: {width} x {height} 像素"
            except Exception as e:
                file_info += f"\n读取图片时出错: {str(e)}"
                QMessageBox.warning(self, "图片读取错误", f"无法读取图片文件: {str(e)}")
        
        self.file_info_text.setText(file_info)
    
    def get_image_size(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ('.dds', '.tga'):
            from PIL import Image
            with Image.open(file_path) as img:
                return img.width, img.height
        else:
            reader = QImageReader(file_path)
            size = reader.size()
            return size.width(), size.height()
    
    def display_image(self, file_path, scene, is_original=True):
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ('.dds', '.tga'):
            from PIL import Image
            pil_image = Image.open(file_path)
            
            # 转换为QImage
            if pil_image.mode == "RGBA":
                qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QImage.Format_RGBA8888)
            elif pil_image.mode == "RGB":
                qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QImage.Format_RGB888)
            else:
                pil_image = pil_image.convert("RGB")
                qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
        else:
            reader = QImageReader(file_path)
            image = reader.read()
            if image.isNull():
                raise Exception("Qt无法读取此图片")
            pixmap = QPixmap.fromImage(image)
        
        scene.clear()
        scene.addItem(QGraphicsPixmapItem(pixmap))
        
        # 调整视图大小
        if is_original:
            self.original_preview.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.original_preview.show()
        else:
            self.replacement_preview.fitInView(scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.replacement_preview.show()
    
    def draw_arrow(self):
        self.arrow_scene.clear()
        
        # 绘制箭头
        line = QGraphicsLineItem(20, 50, 80, 50)
        line.setPen(QColor(0, 0, 0))
        
        # 箭头头部
        arrow_head1 = QGraphicsLineItem(80, 50, 70, 40)
        arrow_head1.setPen(QColor(0, 0, 0))
        
        arrow_head2 = QGraphicsLineItem(80, 50, 70, 60)
        arrow_head2.setPen(QColor(0, 0, 0))
        
        self.arrow_scene.addItem(line)
        self.arrow_scene.addItem(arrow_head1)
        self.arrow_scene.addItem(arrow_head2)
    
    def select_replacement_file(self):
        if not self.current_selected_file:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择替换文件", "", 
            "图片文件 (*.png *.dds *.tga);;所有文件 (*)"
        )
        
        if file_path:
            self.replacement_files[self.current_selected_file] = file_path
            self.display_file_info(self.current_selected_file)
            self.update_file_tree_colors()
    
    def update_file_tree_colors(self):
        def traverse_items(item):
            has_modified_child = False
            
            for i in range(item.childCount()):
                child = item.child(i)
                file_path = child.data(0, Qt.UserRole)
                
                if file_path:
                    if os.path.isfile(file_path):
                        # 文件项
                        if file_path in self.replacement_files:
                            child.setForeground(0, QColor(255, 0, 0))
                            has_modified_child = True
                        else:
                            child.setForeground(0, QColor(0, 0, 0))
                    elif os.path.isdir(file_path):
                        # 文件夹项，递归处理
                        child_has_modified = traverse_items(child)
                        if child_has_modified:
                            child.setForeground(0, QColor(255, 0, 0))
                            has_modified_child = True
                        else:
                            child.setForeground(0, QColor(0, 0, 0))
                
            return has_modified_child
        
        # 从根节点开始遍历
        root = self.file_tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            traverse_items(item)

if __name__ == "__main__":
    app = QApplication([])
    
    # 检查Pillow库是否安装
    try:
        from PIL import Image
    except ImportError:
        QMessageBox.critical(None, "缺少依赖", "需要安装Pillow库来处理DDS和TGA文件\n请运行: pip install pillow")
        exit(1)
    
    window = FileViewerApp()
    window.show()
    app.exec_()
