# tabs/all_in_one_tab.py
import os
import tempfile
from PIL import Image

from common.i18n.translator import translator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QFileDialog, QLabel, QProgressBar,
    QMessageBox, QGroupBox, QCheckBox, QComboBox,
    QSpinBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import subprocess
import shutil

from tabs.compress_tab import get_gs_path, get_ghostscript_env, check_ghostscript


class AllInOneThread(QThread):
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    status_update = Signal(str)
    
    def __init__(self, image_paths, output_path, settings):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
        self.settings = settings
    
    def run(self):
        try:
            temp_dir = tempfile.mkdtemp()
            temp_pdf_path = os.path.join(temp_dir, "temp_merged.pdf")
            
            self.status_update.emit(translator.tr('status_processing', 'common'))
            self._convert_images_to_pdf(temp_pdf_path)
            self.progress.emit(30)
            
            self.status_update.emit(translator.tr('status_processing', 'common'))
            self.progress.emit(60)
            
            if self.settings.get('compress', False):
                self.status_update.emit(translator.tr('status_processing', 'common'))
                self._compress_pdf(temp_pdf_path, self.output_path)
                self.progress.emit(90)
            else:
                shutil.copy2(temp_pdf_path, self.output_path)
            
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            self.progress.emit(100)
            self.finished.emit(
                translator.tr('success_convert', 'messages')
            )
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _convert_images_to_pdf(self, output_path):
        images = []
        for path in self.image_paths:
            img = Image.open(path)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        
        if len(images) == 1:
            images[0].save(output_path, "PDF", resolution=100.0)
        else:
            images[0].save(
                output_path,
                "PDF",
                save_all=True,
                append_images=images[1:],
                resolution=100.0
            )
    
    def _compress_pdf(self, input_path, output_path):
        gs_path = get_gs_path()
        if not gs_path:
            raise Exception(translator.tr('compress_gs_not_found', 'compress'))
        
        env = get_ghostscript_env()
        if not env:
            raise Exception(translator.tr('compress_gs_resources_not_found', 'compress'))
        
        profile = self.settings.get('profile', 'ebook')
        quality = self.settings.get('quality', 80)
        
        cmd = [
            gs_path,
            '-sDEVICE=pdfwrite',
            '-dNOPAUSE',
            '-dBATCH',
            '-dSAFER',
            '-dPDFSETTINGS=/' + profile,
            '-dCompatibilityLevel=1.4',
            '-dAutoRotatePages=/None',
            '-dColorImageDownsampleType=/Bicubic',
            '-dGrayImageDownsampleType=/Bicubic',
            '-dMonoImageDownsampleType=/Bicubic',
            '-dDownsampleColorImages=true',
            '-dDownsampleGrayImages=true',
            '-dDownsampleMonoImages=true',
        ]
        
        if profile == 'screen':
            cmd.extend(['-dColorImageResolution=72', '-dGrayImageResolution=72', '-dMonoImageResolution=72'])
        elif profile == 'ebook':
            cmd.extend(['-dColorImageResolution=150', '-dGrayImageResolution=150', '-dMonoImageResolution=150'])
        elif profile == 'printer':
            cmd.extend(['-dColorImageResolution=300', '-dGrayImageResolution=300', '-dMonoImageResolution=300'])
        
        if quality:
            cmd.append(f'-dJPEGQuality={quality}')
        
        cmd.extend([
            '-dOptimize=true',
            '-dPreserveOverprintSettings=false',
            '-dPreserveHalftoneInfo=false',
            '-dPreserveSpotObjects=false',
            f'-sOutputFile={output_path}',
            input_path
        ])
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            raise Exception(translator.tr('compress_gs_error', 'compress').format(error=stderr))


class AllInOneTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.output_path = ""
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # ========================
        # ПОЯСНЮЮЧИЙ ЗАГОЛОВОК
        # ========================
        info_label = QLabel(translator.tr('description', 'all_in_one'))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #555;
                padding: 8px;
                background-color: #f5f5f5;
                border-radius: 5px;
                margin-bottom: 5px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Drag & drop область
        self.drop_label = QLabel(translator.tr('convert_drag_drop', 'convert'))
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #9C27B0;
                background-color: #f3e5f5;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Кнопки додавання/видалення
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton(translator.tr('btn_add_images', 'convert'))
        self.add_btn.clicked.connect(self.add_images)
        self.clear_btn = QPushButton(translator.tr('btn_clear_list', 'convert'))
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Список зображень
        self.image_list = QListWidget()
        layout.addWidget(self.image_list)
        
        # Налаштування
        settings_group = QGroupBox(translator.tr('menu_settings', 'ui'))
        settings_layout = QVBoxLayout()
        
        self.compress_check = QCheckBox(translator.tr('btn_compress', 'ui'))
        self.compress_check.setChecked(True)
        self.compress_check.toggled.connect(self.toggle_compress_settings)
        settings_layout.addWidget(self.compress_check)
        
        compress_settings = QHBoxLayout()
        compress_settings.addWidget(QLabel(translator.tr('compress_profile_label', 'compress')))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem(translator.tr('compress_profile_screen', 'compress'), "screen")
        self.profile_combo.addItem(translator.tr('compress_profile_ebook', 'compress'), "ebook")
        self.profile_combo.addItem(translator.tr('compress_profile_printer', 'compress'), "printer")
        self.profile_combo.setCurrentIndex(1)
        compress_settings.addWidget(self.profile_combo)
        compress_settings.addStretch()
        settings_layout.addLayout(compress_settings)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel(translator.tr('compress_quality_label', 'compress')))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        self.quality_spin.setSingleStep(5)
        quality_layout.addWidget(self.quality_spin)
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Вибір шляху збереження
        path_layout = QHBoxLayout()
        self.path_label = QLabel(translator.tr('convert_no_path', 'convert'))
        path_layout.addWidget(self.path_label)
        self.path_btn = QPushButton(translator.tr('btn_select_path', 'convert'))
        self.path_btn.clicked.connect(self.select_output)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        self.start_btn = QPushButton(translator.tr('btn_start', 'ui'))
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)
    
    def retranslate_ui(self):
        """Оновлює переклади при зміні мови"""
        # Оновлюємо пояснювальний заголовок
        for label in self.findChildren(QLabel):
            if label.styleSheet() and "background-color: #f5f5f5;" in label.styleSheet():
                label.setText(translator.tr('all_in_one_description', 'all_in_one'))
        
        self.drop_label.setText(translator.tr('convert_drag_drop', 'convert'))
        self.add_btn.setText(translator.tr('btn_add_images', 'convert'))
        self.clear_btn.setText(translator.tr('btn_clear_list', 'convert'))
        self.compress_check.setText(translator.tr('btn_compress', 'ui'))
        self.path_btn.setText(translator.tr('btn_select_path', 'convert'))
        self.start_btn.setText(translator.tr('btn_start', 'ui'))
        
        for group in self.findChildren(QGroupBox):
            if group.title() in ["Налаштування", "Settings"]:
                group.setTitle(translator.tr('menu_settings', 'ui'))
        
        for i in range(self.profile_combo.count()):
            data = self.profile_combo.itemData(i)
            if data == "screen":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_screen', 'compress'))
            elif data == "ebook":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_ebook', 'compress'))
            elif data == "printer":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_printer', 'compress'))
        
        for label in self.findChildren(QLabel):
            if label.text() in ["Рівень стиснення:", "Compression level:"]:
                label.setText(translator.tr('compress_profile_label', 'compress'))
            elif label.text() in ["Якість JPEG (1-100):", "JPEG quality (1-100):"]:
                label.setText(translator.tr('compress_quality_label', 'compress'))
        
        if self.output_path:
            self.path_label.setText(
                translator.tr('convert_path_selected', 'convert').format(
                    path=self.output_path
                )
            )
        else:
            self.path_label.setText(translator.tr('convert_no_path', 'convert'))
    
    def toggle_compress_settings(self, checked):
        self.profile_combo.setEnabled(checked)
        self.quality_spin.setEnabled(checked)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    event.acceptProposedAction()
                    self.drop_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #9C27B0;
                            border-radius: 10px;
                            padding: 20px;
                            background-color: #e1bee7;
                            color: #4a148c;
                            font-size: 14px;
                        }
                    """)
                    self.drop_label.setText(translator.tr('convert_drop_here', 'convert'))
                    break
    
    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #9C27B0;
                background-color: #f3e5f5;
            }
        """)
        self.drop_label.setText(translator.tr('convert_drag_drop', 'convert'))
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                if file_path not in self.image_paths:
                    files.append(file_path)
        
        if files:
            self.image_paths.extend(files)
            for file in files:
                self.image_list.addItem(os.path.basename(file))
            
            if not self.output_path:
                self.suggest_output_name()
            
            self.update_start_button()
            self.status_signal.emit(
                translator.tr('convert_images_added', 'convert').format(count=len(files))
            )
        
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                background-color: #f0f0f0;
                color: #666;
                font-size: 14px;
            }
            QLabel:hover {
                border-color: #9C27B0;
                background-color: #f3e5f5;
            }
        """)
        self.drop_label.setText(translator.tr('convert_drag_drop', 'convert'))
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            translator.tr('convert_select_images_title', 'convert'),
            "",
            translator.tr('convert_images_filter', 'convert')
        )
        for file in files:
            if file not in self.image_paths:
                self.image_paths.append(file)
                self.image_list.addItem(os.path.basename(file))
        
        if len(self.image_paths) > 0 and not self.output_path:
            self.suggest_output_name()
        
        self.update_start_button()
    
    def suggest_output_name(self):
        if self.image_paths:
            first_image_dir = os.path.dirname(self.image_paths[0])
            base_name = os.path.splitext(os.path.basename(self.image_paths[0]))[0]
            suggested_name = f"{base_name}_processed.pdf"
            self.output_path = os.path.join(first_image_dir, suggested_name)
            self.path_label.setText(
                translator.tr('convert_path_selected', 'convert').format(
                    path=self.output_path
                )
            )
            self.update_start_button()
    
    def clear_list(self):
        self.image_paths.clear()
        self.image_list.clear()
        self.output_path = ""
        self.path_label.setText(translator.tr('convert_no_path', 'convert'))
        self.update_start_button()
    
    def select_output(self):
        initial_dir = os.getcwd()
        initial_name = "processed.pdf"
        
        if self.image_paths:
            initial_dir = os.path.dirname(self.image_paths[0])
            base_name = os.path.splitext(os.path.basename(self.image_paths[0]))[0]
            initial_name = f"{base_name}_processed.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            translator.tr('convert_save_pdf_title', 'convert'),
            os.path.join(initial_dir, initial_name),
            translator.tr('convert_pdf_filter', 'convert')
        )
        if path:
            self.output_path = path
            self.path_label.setText(
                translator.tr('convert_path_selected', 'convert').format(
                    path=path
                )
            )
            self.update_start_button()
    
    def update_start_button(self):
        self.start_btn.setEnabled(
            len(self.image_paths) > 0 and self.output_path != ""
        )
    
    def check_file_exists(self):
        if os.path.exists(self.output_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(translator.tr('convert_file_exists_title', 'convert'))
            msg_box.setText(
                translator.tr('convert_file_exists_text', 'convert').format(
                    filename=os.path.basename(self.output_path)
                )
            )
            
            overwrite_btn = msg_box.addButton(
                translator.tr('btn_overwrite', 'convert'),
                QMessageBox.ButtonRole.AcceptRole
            )
            rename_btn = msg_box.addButton(
                translator.tr('btn_rename', 'convert'),
                QMessageBox.ButtonRole.AcceptRole
            )
            cancel_btn = msg_box.addButton(
                translator.tr('btn_cancel', 'ui'),
                QMessageBox.ButtonRole.RejectRole
            )
            
            msg_box.setDefaultButton(overwrite_btn)
            msg_box.exec()
            
            if msg_box.clickedButton() == overwrite_btn:
                return True
            elif msg_box.clickedButton() == rename_btn:
                base, ext = os.path.splitext(self.output_path)
                counter = 1
                new_path = f"{base}_{counter}{ext}"
                while os.path.exists(new_path):
                    counter += 1
                    new_path = f"{base}_{counter}{ext}"
                self.output_path = new_path
                self.path_label.setText(
                    translator.tr('convert_path_selected', 'convert').format(
                        path=new_path
                    )
                )
                return self.check_file_exists()
            else:
                return False
        return True
    
    def start_processing(self):
        if not self.image_paths or not self.output_path:
            return
        
        if not self.check_file_exists():
            return
        
        if self.compress_check.isChecked():
            gs_ok, gs_message = check_ghostscript()
            if not gs_ok:
                QMessageBox.critical(
                    self,
                    translator.tr('status_error'),
                    translator.tr('compress_gs_not_ready', 'compress').format(error=gs_message)
                )
                return
        
        settings = {
            'compress': self.compress_check.isChecked(),
            'profile': self.profile_combo.currentData(),
            'quality': self.quality_spin.value()
        }
        
        self.start_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText(translator.tr('status_processing', 'common'))
        
        self.thread = AllInOneThread(self.image_paths, self.output_path, settings)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.status_update.connect(self.status_label.setText)
        self.thread.start()
    
    def on_finished(self, message):
        self.progress.setVisible(False)
        self.status_label.setVisible(False)
        self.start_btn.setEnabled(True)
        self.status_signal.emit(translator.tr('status_done', 'common'))
        QMessageBox.information(
            self,
            translator.tr('status_done', 'common'),
            message
        )
    
    def on_error(self, error):
        self.progress.setVisible(False)
        self.status_label.setVisible(False)
        self.start_btn.setEnabled(True)
        self.status_signal.emit(
            translator.tr('status_error', 'common').format(error=error)
        )
        QMessageBox.critical(
            self,
            translator.tr('status_error', 'common'),
            translator.tr('error_convert_failed', 'messages').format(error=error)
        )
