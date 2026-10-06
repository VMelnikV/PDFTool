# tabs/compress_tab.py
import os
import sys
import subprocess
import shutil

from common.i18n.translator import translator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QComboBox, QProgressBar,
    QMessageBox, QSpinBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent

# ==================================================
# ФУНКЦІЇ ДЛЯ РОБОТИ З СИСТЕМНИМ GHOSTSCRIPT
# ==================================================

def get_gs_path():
    """Повертає шлях до системного Ghostscript"""
    gs_path = shutil.which('gs')
    if gs_path:
        return gs_path
    
    possible_paths = ['/usr/bin/gs', '/usr/local/bin/gs']
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    
    return None

def get_ghostscript_env():
    """Повертає середовище для системного Ghostscript"""
    env = os.environ.copy()
    
    try:
        result = subprocess.run(['gs', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
    except:
        version = "10.02.1"
    
    env['GS_LIB'] = f'/usr/share/ghostscript/{version}/Resource/Init'
    env['GS_FONTPATH'] = '/usr/share/fonts/type1/gsfonts'
    env['GS_OPTIONS'] = '-dNOPAUSE -dBATCH -dSAFER'
    
    return env

def check_ghostscript():
    """Перевіряє наявність системного Ghostscript"""
    try:
        gs_path = get_gs_path()
        if not gs_path:
            return False, translator.tr('compress_gs_not_found', 'compress')
        
        env = get_ghostscript_env()
        
        gs_init_path = os.path.join(env.get('GS_LIB', ''), 'gs_init.ps')
        if not os.path.exists(gs_init_path):
            return False, translator.tr('compress_gs_init_not_found', 'compress').format(path=gs_init_path)
        
        result = subprocess.run(
            [gs_path, '--version'],
            env=env,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, translator.tr('compress_gs_init_error', 'compress').format(error=result.stderr)
        
        return True, translator.tr('compress_gs_ready', 'compress')
    except Exception as e:
        return False, translator.tr('compress_gs_check_error', 'compress').format(error=str(e))


class CompressThread(QThread):
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self, input_path, output_path, profile, dpi=None, quality=None):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.profile = profile
        self.dpi = dpi
        self.quality = quality
    
    def run(self):
        try:
            gs_path = get_gs_path()
            
            if not gs_path:
                self.error.emit(translator.tr('compress_gs_not_found', 'compress'))
                return
            
            env = get_ghostscript_env()
            
            cmd = [
                gs_path,
                '-sDEVICE=pdfwrite',
                '-dNOPAUSE',
                '-dBATCH',
                '-dSAFER',
                '-dPDFSETTINGS=/' + self.profile,
                '-dCompatibilityLevel=1.4',
                '-dAutoRotatePages=/None',
                '-dColorImageDownsampleType=/Bicubic',
                '-dGrayImageDownsampleType=/Bicubic',
                '-dMonoImageDownsampleType=/Bicubic',
                '-dDownsampleColorImages=true',
                '-dDownsampleGrayImages=true',
                '-dDownsampleMonoImages=true',
            ]
            
            if self.profile == 'screen':
                cmd.extend(['-dColorImageResolution=72', '-dGrayImageResolution=72', '-dMonoImageResolution=72'])
            elif self.profile == 'ebook':
                cmd.extend(['-dColorImageResolution=150', '-dGrayImageResolution=150', '-dMonoImageResolution=150'])
            elif self.profile == 'printer':
                cmd.extend(['-dColorImageResolution=300', '-dGrayImageResolution=300', '-dMonoImageResolution=300'])
            
            if self.quality:
                cmd.append(f'-dJPEGQuality={self.quality}')
            
            cmd.extend([
                '-dOptimize=true',
                '-dPreserveOverprintSettings=false',
                '-dPreserveHalftoneInfo=false',
                '-dPreserveSpotObjects=false',
                f'-sOutputFile={self.output_path}',
                self.input_path
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
                self.error.emit(translator.tr('compress_gs_error', 'compress').format(error=stderr))
                return
            
            input_size = os.path.getsize(self.input_path) / (1024 * 1024)
            output_size = os.path.getsize(self.output_path) / (1024 * 1024)
            reduction = ((input_size - output_size) / input_size * 100) if input_size > 0 else 0
            
            self.progress.emit(100)
            
            if reduction > 0:
                self.finished.emit(
                    translator.tr('compress_success_with_reduction', 'compress').format(
                        input_size=input_size,
                        output_size=output_size,
                        reduction=reduction
                    )
                )
            else:
                self.finished.emit(
                    translator.tr('compress_success_no_reduction', 'compress').format(
                        input_size=input_size,
                        output_size=output_size
                    )
                )
            
        except Exception as e:
            self.error.emit(str(e))


class CompressTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.input_path = ""
        self.output_path = ""
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.drop_label = QLabel(translator.tr('compress_drag_drop', 'compress'))
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
                border-color: #FF9800;
                background-color: #fff3e0;
            }
        """)
        layout.addWidget(self.drop_label)
        
        file_layout = QHBoxLayout()
        self.file_label = QLabel(translator.tr('compress_no_file', 'compress'))
        file_layout.addWidget(self.file_label)
        self.file_btn = QPushButton(translator.tr('compress_select_pdf', 'compress'))
        self.file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_btn)
        layout.addLayout(file_layout)
        
        settings_layout = QVBoxLayout()
        
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel(translator.tr('compress_profile_label', 'compress')))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem(translator.tr('compress_profile_screen', 'compress'), "screen")
        self.profile_combo.addItem(translator.tr('compress_profile_ebook', 'compress'), "ebook")
        self.profile_combo.addItem(translator.tr('compress_profile_printer', 'compress'), "printer")
        self.profile_combo.setCurrentIndex(1)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addStretch()
        settings_layout.addLayout(profile_layout)
        
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel(translator.tr('compress_quality_label', 'compress')))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        self.quality_spin.setSingleStep(5)
        quality_layout.addWidget(self.quality_spin)
        quality_layout.addWidget(QLabel(translator.tr('compress_quality_hint', 'compress')))
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        layout.addLayout(settings_layout)
        
        self.info_label = QLabel(translator.tr('compress_no_size', 'compress'))
        layout.addWidget(self.info_label)
        
        save_layout = QHBoxLayout()
        self.save_label = QLabel(translator.tr('compress_no_output', 'compress'))
        save_layout.addWidget(self.save_label)
        self.save_btn = QPushButton(translator.tr('compress_select_output', 'compress'))
        self.save_btn.clicked.connect(self.select_output)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.compress_btn = QPushButton(translator.tr('btn_compress', 'ui'))
        self.compress_btn.clicked.connect(self.compress)
        self.compress_btn.setEnabled(False)
        layout.addWidget(self.compress_btn)
    
    def retranslate_ui(self):
        self.drop_label.setText(translator.tr('compress_drag_drop', 'compress'))
        
        if self.input_path:
            self.file_label.setText(
                translator.tr('compress_file_selected', 'compress').format(
                    filename=os.path.basename(self.input_path)
                )
            )
        else:
            self.file_label.setText(translator.tr('compress_no_file', 'compress'))
        
        if self.output_path:
            self.save_label.setText(
                translator.tr('compress_output_selected', 'compress').format(
                    filename=os.path.basename(self.output_path)
                )
            )
        else:
            self.save_label.setText(translator.tr('compress_no_output', 'compress'))
        
        self.file_btn.setText(translator.tr('compress_select_pdf', 'compress'))
        self.save_btn.setText(translator.tr('compress_select_output', 'compress'))
        self.compress_btn.setText(translator.tr('btn_compress', 'ui'))
        
        for i in range(self.profile_combo.count()):
            data = self.profile_combo.itemData(i)
            if data == "screen":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_screen', 'compress'))
            elif data == "ebook":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_ebook', 'compress'))
            elif data == "printer":
                self.profile_combo.setItemText(i, translator.tr('compress_profile_printer', 'compress'))
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    self.drop_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #FF9800;
                            border-radius: 10px;
                            padding: 20px;
                            background-color: #ffe0b2;
                            color: #e65100;
                            font-size: 14px;
                        }
                    """)
                    self.drop_label.setText(translator.tr('compress_drop_here', 'compress'))
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
                border-color: #FF9800;
                background-color: #fff3e0;
            }
        """)
        self.drop_label.setText(translator.tr('compress_drag_drop', 'compress'))
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.input_path = file_path
                self.file_label.setText(
                    translator.tr('compress_file_selected', 'compress').format(
                        filename=os.path.basename(file_path)
                    )
                )
                
                size = os.path.getsize(file_path) / (1024 * 1024)
                self.info_label.setText(
                    translator.tr('compress_file_size', 'compress').format(size=size)
                )
                
                self.suggest_output_name()
                self.update_compress_button()
                self.status_signal.emit(
                    translator.tr('compress_file_selected_status', 'compress').format(
                        filename=os.path.basename(file_path)
                    )
                )
                break
        
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
                border-color: #FF9800;
                background-color: #fff3e0;
            }
        """)
        self.drop_label.setText(translator.tr('compress_drag_drop', 'compress'))
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            translator.tr('compress_select_pdf_title', 'compress'),
            "",
            translator.tr('compress_pdf_filter', 'compress')
        )
        if path:
            self.input_path = path
            self.file_label.setText(
                translator.tr('compress_file_selected', 'compress').format(
                    filename=os.path.basename(path)
                )
            )
            
            size = os.path.getsize(path) / (1024 * 1024)
            self.info_label.setText(
                translator.tr('compress_file_size', 'compress').format(size=size)
            )
            
            self.suggest_output_name()
            self.update_compress_button()
    
    def suggest_output_name(self):
        if self.input_path:
            input_dir = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            suggested_name = f"{base_name}_compressed.pdf"
            suggested_path = os.path.join(input_dir, suggested_name)
            self.output_path = suggested_path
            self.save_label.setText(
                translator.tr('compress_output_selected', 'compress').format(
                    filename=suggested_name
                )
            )
            self.update_compress_button()
    
    def select_output(self):
        initial_dir = os.getcwd()
        initial_name = "compressed.pdf"
        
        if self.input_path:
            initial_dir = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            initial_name = f"{base_name}_compressed.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            translator.tr('compress_save_as_title', 'compress'),
            os.path.join(initial_dir, initial_name),
            translator.tr('compress_pdf_filter', 'compress')
        )
        if path:
            self.output_path = path
            self.save_label.setText(
                translator.tr('compress_output_selected', 'compress').format(
                    filename=os.path.basename(path)
                )
            )
            self.update_compress_button()
    
    def update_compress_button(self):
        self.compress_btn.setEnabled(
            self.input_path != "" and self.output_path != ""
        )
    
    def check_file_exists(self):
        if os.path.exists(self.output_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(translator.tr('compress_file_exists_title', 'compress'))
            msg_box.setText(
                translator.tr('compress_file_exists_text', 'compress').format(
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
                self.save_label.setText(
                    translator.tr('compress_output_selected', 'compress').format(
                        filename=os.path.basename(new_path)
                    )
                )
                return self.check_file_exists()
            else:
                return False
        return True
    
    def compress(self):
        if not self.input_path or not self.output_path:
            return
        
        if self.input_path == self.output_path:
            reply = QMessageBox.question(
                self,
                translator.tr('compress_warning_title', 'compress'),
                translator.tr('compress_warning_same_file', 'compress'),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        if not self.check_file_exists():
            return
        
        gs_ok, gs_message = check_ghostscript()
        if not gs_ok:
            QMessageBox.critical(
                self,
                translator.tr('status_error'),
                translator.tr('compress_gs_not_ready', 'compress').format(error=gs_message)
            )
            return
        
        profile = self.profile_combo.currentData()
        quality = self.quality_spin.value()
        
        self.compress_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.thread = CompressThread(
            self.input_path,
            self.output_path,
            profile,
            None,
            quality
        )
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_compress_finished)
        self.thread.error.connect(self.on_compress_error)
        self.thread.start()
    
    def on_compress_finished(self, message):
        self.progress.setVisible(False)
        self.compress_btn.setEnabled(True)
        self.status_signal.emit(translator.tr('compress_done_status', 'compress'))
        
        if os.path.exists(self.output_path):
            size = os.path.getsize(self.output_path) / (1024 * 1024)
            self.info_label.setText(
                translator.tr('compress_new_size', 'compress').format(size=size)
            )
        
        QMessageBox.information(
            self,
            translator.tr('status_done'),
            message
        )
    
    def on_compress_error(self, error):
        self.progress.setVisible(False)
        self.compress_btn.setEnabled(True)
        self.status_signal.emit(
            translator.tr('compress_error_status', 'compress').format(error=error)
        )
        QMessageBox.critical(
            self,
            translator.tr('status_error'),
            translator.tr('compress_error_detail', 'compress').format(error=error)
        )
