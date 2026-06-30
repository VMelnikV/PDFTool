from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QSpinBox, QProgressBar,
    QMessageBox, QRadioButton, QGroupBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from pypdf import PdfReader, PdfWriter
import os

class SplitThread(QThread):
    finished = Signal(str)
    progress = Signal(int)
    error = Signal(str)
    
    def __init__(self, input_path, output_dir, mode, pages_range=None):
        super().__init__()
        self.input_path = input_path
        self.output_dir = output_dir
        self.mode = mode
        self.pages_range = pages_range
    
    def run(self):
        try:
            reader = PdfReader(self.input_path)
            total_pages = len(reader.pages)
            
            if self.mode == 'all':
                for i in range(total_pages):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[i])
                    output_path = os.path.join(
                        self.output_dir,
                        f"page_{i+1}.pdf"
                    )
                    writer.write(output_path)
                    writer.close()
                    self.progress.emit(int((i + 1) / total_pages * 100))
                
                self.finished.emit(f"Розділено на {total_pages} сторінок")
            
            elif self.mode == 'range':
                start, end = self.pages_range
                writer = PdfWriter()
                for i in range(start - 1, end):
                    writer.add_page(reader.pages[i])
                    self.progress.emit(int((i - (start - 1) + 1) / (end - start + 1) * 100))
                
                output_path = os.path.join(
                    self.output_dir,
                    f"pages_{start}_{end}.pdf"
                )
                writer.write(output_path)
                writer.close()
                self.finished.emit(f"Сторінки {start}-{end} збережено")
            
            elif self.mode == 'single':
                page_num = self.pages_range[0]
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num - 1])
                output_path = os.path.join(
                    self.output_dir,
                    f"page_{page_num}.pdf"
                )
                writer.write(output_path)
                writer.close()
                self.progress.emit(100)
                self.finished.emit(f"Сторінку {page_num} збережено")
                
        except Exception as e:
            self.error.emit(str(e))

class SplitTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.input_path = ""
        self.output_dir = ""
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
                border-color: #F44336;
                background-color: #ffebee;
            }
        """)
        layout.addWidget(self.drop_label)
        
        # Вибір вхідного файлу
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл: не вибрано")
        file_layout.addWidget(self.file_label)
        self.file_btn = QPushButton("📂 Вибрати PDF")
        self.file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_btn)
        layout.addLayout(file_layout)
        
        # Режими розділення
        mode_group = QGroupBox("Режим розділення")
        mode_layout = QVBoxLayout()
        
        self.all_pages_radio = QRadioButton("Розділити на окремі сторінки")
        self.all_pages_radio.setChecked(True)
        self.all_pages_radio.toggled.connect(self.toggle_mode)
        
        self.range_radio = QRadioButton("Виділити діапазон сторінок")
        self.range_radio.toggled.connect(self.toggle_mode)
        
        self.single_radio = QRadioButton("Виділити одну сторінку")
        self.single_radio.toggled.connect(self.toggle_mode)
        
        mode_layout.addWidget(self.all_pages_radio)
        mode_layout.addWidget(self.range_radio)
        mode_layout.addWidget(self.single_radio)
        
        # Налаштування для діапазону
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("З:"))
        self.start_spin = QSpinBox()
        self.start_spin.setMinimum(1)
        self.start_spin.setMaximum(9999)
        self.start_spin.setEnabled(False)
        range_layout.addWidget(self.start_spin)
        
        range_layout.addWidget(QLabel("По:"))
        self.end_spin = QSpinBox()
        self.end_spin.setMinimum(1)
        self.end_spin.setMaximum(9999)
        self.end_spin.setEnabled(False)
        range_layout.addWidget(self.end_spin)
        
        # Налаштування для однієї сторінки
        single_layout = QHBoxLayout()
        single_layout.addWidget(QLabel("Номер сторінки:"))
        self.single_spin = QSpinBox()
        self.single_spin.setMinimum(1)
        self.single_spin.setMaximum(9999)
        self.single_spin.setEnabled(False)
        single_layout.addWidget(self.single_spin)
        
        mode_layout.addLayout(range_layout)
        mode_layout.addLayout(single_layout)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Вибір папки для збереження
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Папка: не вибрано")
        dir_layout.addWidget(self.dir_label)
        self.dir_btn = QPushButton("📁 Вибрати папку")
        self.dir_btn.clicked.connect(self.select_dir)
        dir_layout.addWidget(self.dir_btn)
        layout.addLayout(dir_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.split_btn = QPushButton("✂️ Розділити PDF")
        self.split_btn.clicked.connect(self.split)
        self.split_btn.setEnabled(False)
        layout.addWidget(self.split_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    self.drop_label.setStyleSheet("""
                        QLabel {
                            border: 2px solid #F44336;
                            border-radius: 10px;
                            padding: 20px;
                            background-color: #ffcdd2;
                            color: #c62828;
                            font-size: 14px;
                        }
                    """)
                    self.drop_label.setText("📥 Відпустіть файл для розділення")
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
                border-color: #F44336;
                background-color: #ffebee;
            }
        """)
        self.drop_label.setText("📥 Перетягніть PDF файл сюди або скористайтеся кнопками нижче")
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.select_file_from_path(file_path)
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
                border-color: #F44336;
                background-color: #ffebee;
            }
        """)
        self.drop_label.setText("📥 Перетягніть PDF файл сюди або скористайтеся кнопками нижче")
    
    def select_file_from_path(self, path):
        self.input_path = path
        self.file_label.setText(f"Файл: {os.path.basename(path)}")
        
        reader = PdfReader(path)
        max_page = len(reader.pages)
        self.start_spin.setMaximum(max_page)
        self.end_spin.setMaximum(max_page)
        self.single_spin.setMaximum(max_page)
        
        if not self.output_dir:
            self.output_dir = os.path.dirname(path)
            self.dir_label.setText(f"Папка: {os.path.basename(self.output_dir)}")
        
        self.update_split_button()
        self.status_signal.emit(f"Вибрано файл: {os.path.basename(path)}")
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть PDF файл",
            "",
            "PDF файли (*.pdf)"
        )
        if path:
            self.select_file_from_path(path)
    
    def select_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Виберіть папку для збереження"
        )
        if dir_path:
            self.output_dir = dir_path
            self.dir_label.setText(f"Папка: {os.path.basename(dir_path)}")
            self.update_split_button()
    
    def toggle_mode(self):
        self.start_spin.setEnabled(self.range_radio.isChecked())
        self.end_spin.setEnabled(self.range_radio.isChecked())
        self.single_spin.setEnabled(self.single_radio.isChecked())
    
    def update_split_button(self):
        self.split_btn.setEnabled(self.input_path != "" and self.output_dir != "")
    
    def check_file_exists(self, file_path):
        """Перевіряє чи існує файл і пропонує дії"""
        if os.path.exists(file_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Файл існує")
            msg_box.setText(f"Файл '{os.path.basename(file_path)}' вже існує.\nЩо бажаєте зробити?")
            
            overwrite_btn = msg_box.addButton("✅ Перезаписати", QMessageBox.ButtonRole.AcceptRole)
            rename_btn = msg_box.addButton("✏️ Змінити назву", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg_box.addButton("❌ Скасувати", QMessageBox.ButtonRole.RejectRole)
            
            msg_box.setDefaultButton(overwrite_btn)
            msg_box.exec()
            
            if msg_box.clickedButton() == overwrite_btn:
                return file_path
            elif msg_box.clickedButton() == rename_btn:
                base, ext = os.path.splitext(file_path)
                counter = 1
                new_path = f"{base}_{counter}{ext}"
                while os.path.exists(new_path):
                    counter += 1
                    new_path = f"{base}_{counter}{ext}"
                return new_path
            else:
                return None
        return file_path
    
    def split(self):
        if not self.input_path or not self.output_dir:
            return
        
        mode = 'all'
        pages_range = None
        
        if self.range_radio.isChecked():
            mode = 'range'
            pages_range = (self.start_spin.value(), self.end_spin.value())
        elif self.single_radio.isChecked():
            mode = 'single'
            pages_range = (self.single_spin.value(),)
        
        # Перевіряємо наявність файлів
        if mode == 'all':
            reader = PdfReader(self.input_path)
            for i in range(1, len(reader.pages) + 1):
                test_path = os.path.join(self.output_dir, f"page_{i}.pdf")
                if os.path.exists(test_path):
                    new_path = self.check_file_exists(test_path)
                    if new_path is None:
                        return
                    elif new_path != test_path:
                        # Якщо користувач змінив назву, пропонуємо створити нову папку
                        reply = QMessageBox.question(
                            self,
                            "Увага",
                            "Для зміни назв краще вибрати іншу папку.\n"
                            "Створити нову папку з іменем файлу?",
                            QMessageBox.Yes | QMessageBox.No
                        )
                        if reply == QMessageBox.Yes:
                            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
                            new_dir = os.path.join(self.output_dir, f"{base_name}_split")
                            counter = 1
                            while os.path.exists(new_dir):
                                new_dir = os.path.join(self.output_dir, f"{base_name}_split_{counter}")
                                counter += 1
                            os.makedirs(new_dir)
                            self.output_dir = new_dir
                            self.dir_label.setText(f"Папка: {os.path.basename(new_dir)}")
                            self.split()
                            return
                    break
        
        elif mode in ['range', 'single']:
            if mode == 'single':
                page_num = pages_range[0]
                test_path = os.path.join(self.output_dir, f"page_{page_num}.pdf")
            else:
                start, end = pages_range
                test_path = os.path.join(self.output_dir, f"pages_{start}_{end}.pdf")
            
            new_path = self.check_file_exists(test_path)
            if new_path is None:
                return
            elif new_path != test_path:
                QMessageBox.information(
                    self,
                    "Інформація",
                    f"Файл буде збережено як: {os.path.basename(new_path)}"
                )
                self.output_dir = os.path.dirname(new_path)
                self.dir_label.setText(f"Папка: {os.path.basename(self.output_dir)}")
        
        self.split_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.thread = SplitThread(self.input_path, self.output_dir, mode, pages_range)
        self.thread.progress.connect(self.progress.setValue)
        self.thread.finished.connect(self.on_split_finished)
        self.thread.error.connect(self.on_split_error)
        self.thread.start()
    
    def on_split_finished(self, message):
        self.progress.setVisible(False)
        self.split_btn.setEnabled(True)
        self.status_signal.emit(message)
        QMessageBox.information(self, "Успішно", message)
    
    def on_split_error(self, error):
        self.progress.setVisible(False)
        self.split_btn.setEnabled(True)
        self.status_signal.emit(f"Помилка: {error}")
        QMessageBox.critical(self, "Помилка", f"Не вдалося розділити:\n{error}")

