from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QFileDialog, QLabel, QProgressBar,
    QMessageBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from pypdf import PdfWriter
import os

class MergeThread(QThread):
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self, pdf_paths, output_path):
        super().__init__()
        self.pdf_paths = pdf_paths
        self.output_path = output_path
    
    def run(self):
        try:
            writer = PdfWriter()
            for i, path in enumerate(self.pdf_paths):
                writer.append(path)
                self.progress.emit(int((i + 1) / len(self.pdf_paths) * 100))
            
            writer.write(self.output_path)
            writer.close()
            self.finished.emit(f"Об'єднання завершено: {self.output_path}")
        except Exception as e:
            self.error.emit(str(e))

class MergeTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.pdf_paths = []
        self.output_path = ""
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Інформаційне повідомлення про drag & drop
        self.drop_label = QLabel("📥 Перетягніть PDF файли сюди або скористайтеся кнопками нижче")
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
                border-color: #2196F3;
                background-color: #e3f2fd;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Кнопки додавання/видалення
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Додати PDF")
        self.add_btn.clicked.connect(self.add_pdfs)
        self.clear_btn = QPushButton("🗑️ Очистити список")
        self.clear_btn.clicked.connect(self.clear_list)
        self.move_up_btn = QPushButton("⬆️ Вгору")
        self.move_up_btn.clicked.connect(self.move_up)
        self.move_down_btn = QPushButton("⬇️ Вниз")
        self.move_down_btn.clicked.connect(self.move_down)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Список PDF
        self.pdf_list = QListWidget()
        layout.addWidget(self.pdf_list)
        
        # Вибір шляху збереження
        path_layout = QHBoxLayout()
        self.path_label = QLabel("Шлях збереження: не вибрано")
        path_layout.addWidget(self.path_label)
        self.path_btn = QPushButton("📁 Вибрати шлях")
        self.path_btn.clicked.connect(self.select_output)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.merge_btn = QPushButton("📄 Об'єднати PDF")
        self.merge_btn.clicked.connect(self.merge)
        self.merge_btn.setEnabled(False)
        layout.addWidget(self.merge_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #2196F3;
                    border-radius: 10px;
                    padding: 20px;
                    background-color: #bbdefb;
                    color: #0d47a1;
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
                border-color: #2196F3;
                background-color: #e3f2fd;
            }
        """)
        self.drop_label.setText("📥 Перетягніть PDF файли сюди або скористайтеся кнопками нижче")
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                if file_path not in self.pdf_paths:
                    files.append(file_path)
        
        if files:
            self.pdf_paths.extend(files)
            for file in files:
                self.pdf_list.addItem(os.path.basename(file))
            
            if not self.output_path:
                self.suggest_output_name()
            
            self.update_merge_button()
            self.status_signal.emit(f"Додано {len(files)} PDF файлів")
        
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
                border-color: #2196F3;
                background-color: #e3f2fd;
            }
        """)
        self.drop_label.setText("📥 Перетягніть PDF файли сюди або скористайтеся кнопками нижче")
    
    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Виберіть PDF файли",
            "",
            "PDF файли (*.pdf)"
        )
        for file in files:
            if file not in self.pdf_paths:
                self.pdf_paths.append(file)
                self.pdf_list.addItem(os.path.basename(file))
        
        if len(self.pdf_paths) > 0 and not self.output_path:
            self.suggest_output_name()
        
        self.update_merge_button()
    
    def suggest_output_name(self):
        if self.pdf_paths:
            first_pdf_dir = os.path.dirname(self.pdf_paths[0])
            base_name = os.path.splitext(os.path.basename(self.pdf_paths[0]))[0]
            
            if len(self.pdf_paths) > 1:
                suggested_name = f"{base_name}_merged.pdf"
            else:
                suggested_name = f"{base_name}.pdf"
            
            suggested_path = os.path.join(first_pdf_dir, suggested_name)
            self.output_path = suggested_path
            self.path_label.setText(f"Шлях збереження: {suggested_path}")
            self.update_merge_button()
    
    def clear_list(self):
        self.pdf_paths.clear()
        self.pdf_list.clear()
        self.output_path = ""
        self.path_label.setText("Шлях збереження: не вибрано")
        self.update_merge_button()
    
    def move_up(self):
        current = self.pdf_list.currentRow()
        if current > 0:
            self.pdf_paths[current], self.pdf_paths[current-1] = self.pdf_paths[current-1], self.pdf_paths[current]
            self.pdf_list.insertItem(current-1, self.pdf_list.takeItem(current))
            self.pdf_list.setCurrentRow(current-1)
    
    def move_down(self):
        current = self.pdf_list.currentRow()
        if current < self.pdf_list.count() - 1:
            self.pdf_paths[current], self.pdf_paths[current+1] = self.pdf_paths[current+1], self.pdf_paths[current]
            self.pdf_list.insertItem(current+1, self.pdf_list.takeItem(current))
            self.pdf_list.setCurrentRow(current+1)
    
    def select_output(self):
        initial_dir = os.getcwd()
        initial_name = "merged.pdf"
        
        if self.pdf_paths:
            initial_dir = os.path.dirname(self.pdf_paths[0])
            base_name = os.path.splitext(os.path.basename(self.pdf_paths[0]))[0]
            if len(self.pdf_paths) > 1:
                initial_name = f"{base_name}_merged.pdf"
            else:
                initial_name = f"{base_name}.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти об'єднаний PDF як",
            os.path.join(initial_dir, initial_name),
            "PDF файли (*.pdf)"
        )
        if path:
            self.output_path = path
            self.path_label.setText(f"Шлях збереження: {path}")
            self.update_merge_button()
    
    def update_merge_button(self):
        self.merge_btn.setEnabled(
            len(self.pdf_paths) > 1 and self.output_path != ""
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
                self.path_label.setText(f"Шлях збереження: {new_path}")
                return self.check_file_exists()
            else:
                return False
        return True
    
    def merge(self):
        if len(self.pdf_paths) < 2 or not self.output_path:
            return
        
        if not self.check_file_exists():
            return
        
        self.merge_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.thread = MergeThread(self.pdf_paths, self.output_path)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_merge_finished)
        self.thread.error.connect(self.on_merge_error)
        self.thread.start()
    
    def on_merge_finished(self, message):
        self.progress.setVisible(False)
        self.merge_btn.setEnabled(True)
        self.status_signal.emit(message)
        QMessageBox.information(self, "Успішно", message)
    
    def on_merge_error(self, error):
        self.progress.setVisible(False)
        self.merge_btn.setEnabled(True)
        self.status_signal.emit(f"Помилка: {error}")
        QMessageBox.critical(self, "Помилка", f"Не вдалося об'єднати:\n{error}")
