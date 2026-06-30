from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QComboBox, QProgressBar,
    QMessageBox, QSpinBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
import subprocess
import os

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
            try:
                subprocess.run(['gs', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.error.emit("Ghostscript не встановлено. Встановіть: sudo apt install ghostscript")
                return
            
            cmd = [
                'gs',
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
                cmd.extend([
                    '-dColorImageResolution=72',
                    '-dGrayImageResolution=72',
                    '-dMonoImageResolution=72',
                    '-dColorImageDownsampleThreshold=1.0',
                    '-dGrayImageDownsampleThreshold=1.0',
                    '-dMonoImageDownsampleThreshold=1.0',
                ])
            elif self.profile == 'ebook':
                cmd.extend([
                    '-dColorImageResolution=150',
                    '-dGrayImageResolution=150',
                    '-dMonoImageResolution=150',
                    '-dColorImageDownsampleThreshold=1.0',
                    '-dGrayImageDownsampleThreshold=1.0',
                    '-dMonoImageDownsampleThreshold=1.0',
                ])
            elif self.profile == 'printer':
                cmd.extend([
                    '-dColorImageResolution=300',
                    '-dGrayImageResolution=300',
                    '-dMonoImageResolution=300',
                    '-dColorImageDownsampleThreshold=1.0',
                    '-dGrayImageDownsampleThreshold=1.0',
                    '-dMonoImageDownsampleThreshold=1.0',
                ])
            
            if self.quality:
                cmd.append(f'-dJPEGQuality={self.quality}')
            
            cmd.extend([
                '-dOptimize=true',
                '-dPreserveOverprintSettings=false',
                '-dPreserveHalftoneInfo=false',
                '-dPreserveSpotObjects=false',
            ])
            
            cmd.extend([
                f'-sOutputFile={self.output_path}',
                self.input_path
            ])
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                self.error.emit(f"Помилка Ghostscript:\n{stderr}")
                return
            
            input_size = os.path.getsize(self.input_path) / (1024 * 1024)
            output_size = os.path.getsize(self.output_path) / (1024 * 1024)
            reduction = ((input_size - output_size) / input_size * 100) if input_size > 0 else 0
            
            self.progress.emit(100)
            
            if reduction > 0:
                self.finished.emit(
                    f"Стиснення завершено!\n"
                    f"Початковий розмір: {input_size:.2f} MB\n"
                    f"Кінцевий розмір: {output_size:.2f} MB\n"
                    f"Зменшено на: {reduction:.1f}%"
                )
            else:
                self.finished.emit(
                    f"Стиснення завершено!\n"
                    f"Початковий розмір: {input_size:.2f} MB\n"
                    f"Кінцевий розмір: {output_size:.2f} MB\n"
                    f"Розмір не зменшився. Спробуйте більш агресивні налаштування."
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
        
        # Інформаційне повідомлення про drag & drop
        self.drop_label = QLabel("📥 Перетягніть PDF файл сюди або скористайтеся кнопками нижче")
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
        
        # Вибір файлу
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл: не вибрано")
        file_layout.addWidget(self.file_label)
        self.file_btn = QPushButton("📂 Вибрати PDF")
        self.file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_btn)
        layout.addLayout(file_layout)
        
        # Налаштування стиснення
        settings_layout = QVBoxLayout()
        
        # Профіль стиснення
        profile_layout = QHBoxLayout()
        profile_layout.addWidget(QLabel("Рівень стиснення:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Екран (найменший розмір, 72 DPI)", "screen")
        self.profile_combo.addItem("Електронна книга (баланс, 150 DPI)", "ebook")
        self.profile_combo.addItem("Друк (висока якість, 300 DPI)", "printer")
        self.profile_combo.setCurrentIndex(1)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addStretch()
        settings_layout.addLayout(profile_layout)
        
        # Якість JPEG
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Якість JPEG (1-100):"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(80)
        self.quality_spin.setSingleStep(5)
        quality_layout.addWidget(self.quality_spin)
        quality_layout.addWidget(QLabel("(нижче = менший розмір, гірша якість)"))
        quality_layout.addStretch()
        settings_layout.addLayout(quality_layout)
        
        layout.addLayout(settings_layout)
        
        # Інформація про файл
        self.info_label = QLabel("Розмір файлу: не визначено")
        layout.addWidget(self.info_label)
        
        # Вибір шляху збереження
        save_layout = QHBoxLayout()
        self.save_label = QLabel("Зберегти як: не вибрано")
        save_layout.addWidget(self.save_label)
        self.save_btn = QPushButton("📁 Вибрати шлях")
        self.save_btn.clicked.connect(self.select_output)
        save_layout.addWidget(self.save_btn)
        layout.addLayout(save_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.compress_btn = QPushButton("📦 Стиснути PDF")
        self.compress_btn.clicked.connect(self.compress)
        self.compress_btn.setEnabled(False)
        layout.addWidget(self.compress_btn)
    
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
                    self.drop_label.setText("📥 Відпустіть файл для стиснення")
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
        self.drop_label.setText("📥 Перетягніть PDF файл сюди або скористайтеся кнопками нижче")
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.input_path = file_path
                self.file_label.setText(f"Файл: {os.path.basename(file_path)}")
                
                size = os.path.getsize(file_path) / (1024 * 1024)
                self.info_label.setText(f"Розмір файлу: {size:.2f} MB")
                
                self.suggest_output_name()
                self.update_compress_button()
                self.status_signal.emit(f"Вибрано файл: {os.path.basename(file_path)}")
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
        self.drop_label.setText("📥 Перетягніть PDF файл сюди або скористайтеся кнопками нижче")
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть PDF для стиснення",
            "",
            "PDF файли (*.pdf)"
        )
        if path:
            self.input_path = path
            self.file_label.setText(f"Файл: {os.path.basename(path)}")
            
            size = os.path.getsize(path) / (1024 * 1024)
            self.info_label.setText(f"Розмір файлу: {size:.2f} MB")
            
            self.suggest_output_name()
            self.update_compress_button()
    
    def suggest_output_name(self):
        if self.input_path:
            input_dir = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            suggested_name = f"{base_name}_compressed.pdf"
            suggested_path = os.path.join(input_dir, suggested_name)
            self.output_path = suggested_path
            self.save_label.setText(f"Зберегти як: {suggested_name}")
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
            "Зберегти стиснутий PDF як",
            os.path.join(initial_dir, initial_name),
            "PDF файли (*.pdf)"
        )
        if path:
            self.output_path = path
            self.save_label.setText(f"Зберегти як: {os.path.basename(path)}")
            self.update_compress_button()
    
    def update_compress_button(self):
        self.compress_btn.setEnabled(
            self.input_path != "" and self.output_path != ""
        )
    
    def check_file_exists(self):
        """Перевіряє чи існує файл і пропонує дії"""
        if os.path.exists(self.output_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Файл існує")
            msg_box.setText(f"Файл '{os.path.basename(self.output_path)}' вже існує.\nЩо бажаєте зробити?")
            
            overwrite_btn = msg_box.addButton("✅ Перезаписати", QMessageBox.ButtonRole.AcceptRole)
            rename_btn = msg_box.addButton("✏️ Змінити назву", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("❌ Скасувати", QMessageBox.ButtonRole.RejectRole)
            
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
                self.save_label.setText(f"Зберегти як: {os.path.basename(new_path)}")
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
                "Попередження",
                "Вихідний файл співпадає з вхідним. Це перезапише оригінал.\n"
                "Продовжити?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        if not self.check_file_exists():
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
        self.status_signal.emit("Стиснення завершено")
        
        if os.path.exists(self.output_path):
            size = os.path.getsize(self.output_path) / (1024 * 1024)
            self.info_label.setText(f"Новий розмір: {size:.2f} MB")
        
        QMessageBox.information(self, "Успішно", message)
    
    def on_compress_error(self, error):
        self.progress.setVisible(False)
        self.compress_btn.setEnabled(True)
        self.status_signal.emit(f"Помилка: {error}")
        QMessageBox.critical(self, "Помилка", f"Не вдалося стиснути PDF:\n{error}")
