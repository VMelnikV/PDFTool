from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QFileDialog, QLabel, QProgressBar,
    QMessageBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PIL import Image
import os

class ConvertThread(QThread):
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self, image_paths, output_path):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
    
    def run(self):
        try:
            images = []
            for i, path in enumerate(self.image_paths):
                img = Image.open(path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)
                self.progress.emit(int((i + 1) / len(self.image_paths) * 100))
            
            if len(images) == 1:
                images[0].save(self.output_path)
            else:
                images[0].save(
                    self.output_path,
                    save_all=True,
                    append_images=images[1:]
                )
            
            self.finished.emit(f"Конвертацію завершено: {self.output_path}")
        except Exception as e:
            self.error.emit(str(e))

class ConvertTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.output_path = ""
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Інформаційне повідомлення про drag & drop
        self.drop_label = QLabel("📥 Перетягніть зображення сюди або скористайтеся кнопками нижче")
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
                border-color: #4CAF50;
                background-color: #e8f5e9;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Кнопки додавання/видалення зображень
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Додати зображення")
        self.add_btn.clicked.connect(self.add_images)
        self.clear_btn = QPushButton("🗑️ Очистити список")
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Список зображень
        self.image_list = QListWidget()
        self.image_list.setAcceptDrops(True)
        layout.addWidget(self.image_list)
        
        # Кнопка вибору шляху збереження
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Шлях збереження: не вибрано")
        path_layout.addWidget(self.path_label)
        self.path_btn = QPushButton("📁 Вибрати шлях")
        self.path_btn.clicked.connect(self.select_output)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)
        
        # Прогрес-бар та кнопка конвертації
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.convert_btn = QPushButton("🚀 Конвертувати в PDF")
        self.convert_btn.clicked.connect(self.convert)
        self.convert_btn.setEnabled(False)
        layout.addWidget(self.convert_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    padding: 20px;
                    background-color: #c8e6c9;
                    color: #2e7d32;
                    font-size: 14px;
                }
            """)
            self.drop_label.setText("📥 Відпустіть файли для додавання")
    
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
                border-color: #4CAF50;
                background-color: #e8f5e9;
            }
        """)
        self.drop_label.setText("📥 Перетягніть зображення сюди або скористайтеся кнопками нижче")
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')):
                if file_path not in self.image_paths:
                    files.append(file_path)
        
        if files:
            self.image_paths.extend(files)
            for file in files:
                self.image_list.addItem(os.path.basename(file))
            
            if not self.output_path:
                self.suggest_output_name()
            
            self.update_convert_button()
            self.status_signal.emit(f"Додано {len(files)} зображень")
        
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
                border-color: #4CAF50;
                background-color: #e8f5e9;
            }
        """)
        self.drop_label.setText("📥 Перетягніть зображення сюди або скористайтеся кнопками нижче")
    
    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Виберіть зображення",
            "",
            "Зображення (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        for file in files:
            if file not in self.image_paths:
                self.image_paths.append(file)
                self.image_list.addItem(os.path.basename(file))
        
        if len(self.image_paths) > 0 and not self.output_path:
            self.suggest_output_name()
        
        self.update_convert_button()
    
    def suggest_output_name(self):
        """Пропонує ім'я для вихідного PDF на основі першого зображення"""
        if self.image_paths:
            # Беремо папку першого зображення
            first_image_dir = os.path.dirname(self.image_paths[0])
            base_name = os.path.splitext(os.path.basename(self.image_paths[0]))[0]
            
            if len(self.image_paths) > 1:
                suggested_name = f"{base_name}_merged.pdf"
            else:
                suggested_name = f"{base_name}.pdf"
            
            # Зберігаємо в тій же папці, де знаходиться перше зображення
            suggested_path = os.path.join(first_image_dir, suggested_name)
            self.output_path = suggested_path
            self.path_label.setText(f"Шлях збереження: {suggested_path}")
            self.update_convert_button()
    
    def clear_list(self):
        self.image_paths.clear()
        self.image_list.clear()
        self.output_path = ""
        self.path_label.setText("Шлях збереження: не вибрано")
        self.update_convert_button()
    
    def select_output(self):
        initial_dir = os.getcwd()
        initial_name = "output.pdf"
        
        if self.image_paths:
            # Беремо папку першого зображення
            initial_dir = os.path.dirname(self.image_paths[0])
            base_name = os.path.splitext(os.path.basename(self.image_paths[0]))[0]
            if len(self.image_paths) > 1:
                initial_name = f"{base_name}_merged.pdf"
            else:
                initial_name = f"{base_name}.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти PDF як",
            os.path.join(initial_dir, initial_name),
            "PDF файли (*.pdf)"
        )
        if path:
            self.output_path = path
            self.path_label.setText(f"Шлях збереження: {path}")
            self.update_convert_button()
    
    def update_convert_button(self):
        self.convert_btn.setEnabled(
            len(self.image_paths) > 0 and self.output_path != ""
        )
    
    def convert(self):
        if not self.image_paths or not self.output_path:
            return
        
        self.convert_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.thread = ConvertThread(self.image_paths, self.output_path)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_conversion_finished)
        self.thread.error.connect(self.on_conversion_error)
        self.thread.start()
    
    def on_conversion_finished(self, message):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.status_signal.emit(message)
        QMessageBox.information(self, "Успішно", message)
    
    def on_conversion_error(self, error):
        self.progress.setVisible(False)
        self.convert_btn.setEnabled(True)
        self.status_signal.emit(f"Помилка: {error}", 5000)
        QMessageBox.critical(self, "Помилка", f"Не вдалося конвертувати:\n{error}")
