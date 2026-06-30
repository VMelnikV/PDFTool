from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFormLayout, QLineEdit,
    QCheckBox, QComboBox, QScrollArea, QGroupBox,
    QProgressBar, QMessageBox, QSpinBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyPDFForm import PdfWrapper
import json
import os

class FormsThread(QThread):
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, input_path, output_path, fields_data):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.fields_data = fields_data
    
    def run(self):
        try:
            wrapper = PdfWrapper(self.input_path)
            wrapper.fill(self.fields_data)
            wrapper.write(self.output_path)
            self.finished.emit(f"Форму заповнено: {self.output_path}")
        except Exception as e:
            self.error.emit(str(e))

class FormsTab(QWidget):
    status_signal = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.input_path = ""
        self.output_path = ""
        self.fields_data = {}
        self.field_widgets = {}
        self.setup_ui()
        self.setAcceptDrops(True)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Інформаційне повідомлення про drag & drop
        self.drop_label = QLabel("📥 Перетягніть PDF з формою сюди або скористайтеся кнопками нижче")
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
        
        # Вибір файлу
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл: не вибрано")
        file_layout.addWidget(self.file_label)
        
        self.load_btn = QPushButton("📂 Відкрити PDF")
        self.load_btn.clicked.connect(self.load_pdf)
        file_layout.addWidget(self.load_btn)
        
        layout.addLayout(file_layout)
        
        # Скрол-область для полів форми
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        scroll.setWidget(self.fields_widget)
        
        layout.addWidget(scroll)
        
        # Шлях збереження
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
        
        self.fill_btn = QPushButton("✍️ Заповнити форму")
        self.fill_btn.clicked.connect(self.fill_form)
        self.fill_btn.setEnabled(False)
        layout.addWidget(self.fill_btn)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
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
                    self.drop_label.setText("📥 Відпустіть файл для відкриття форми")
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
        self.drop_label.setText("📥 Перетягніть PDF з формою сюди або скористайтеся кнопками нижче")
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.load_pdf_from_path(file_path)
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
                border-color: #9C27B0;
                background-color: #f3e5f5;
            }
        """)
        self.drop_label.setText("📥 Перетягніть PDF з формою сюди або скористайтеся кнопками нижче")
    
    def load_pdf_from_path(self, path):
        self.input_path = path
        self.file_label.setText(f"Файл: {os.path.basename(path)}")
        
        self.suggest_output_name()
        
        try:
            wrapper = PdfWrapper(path)
            fields = wrapper.get_form_fields()
            
            self.clear_fields()
            
            if not fields:
                QMessageBox.warning(
                    self,
                    "Попередження",
                    "У цьому PDF немає полів для заповнення."
                )
                return
            
            for field_name, field_info in fields.items():
                field_group = QGroupBox(field_name)
                field_layout = QFormLayout()
                
                field_type = field_info.get('type', 'text')
                
                if field_type == 'checkbox':
                    widget = QCheckBox()
                elif field_type == 'list':
                    widget = QComboBox()
                    widget.addItems(['Варіант 1', 'Варіант 2', 'Варіант 3'])
                else:
                    widget = QLineEdit()
                    default_val = field_info.get('value', '')
                    if default_val and hasattr(widget, 'setText'):
                        widget.setText(str(default_val))
                
                field_layout.addRow("Значення:", widget)
                field_group.setLayout(field_layout)
                
                self.fields_layout.addWidget(field_group)
                self.field_widgets[field_name] = widget
            
            self.fill_btn.setEnabled(True)
            self.status_signal.emit(f"Знайдено {len(fields)} полів форми")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Помилка",
                f"Не вдалося прочитати форму:\n{str(e)}"
            )
    
    def load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть PDF з формою",
            "",
            "PDF файли (*.pdf)"
        )
        if not path:
            return
        
        self.load_pdf_from_path(path)
    
    def suggest_output_name(self):
        if self.input_path:
            input_dir = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            suggested_name = f"{base_name}_filled.pdf"
            suggested_path = os.path.join(input_dir, suggested_name)
            self.output_path = suggested_path
            self.save_label.setText(f"Зберегти як: {suggested_name}")
    
    def clear_fields(self):
        for i in reversed(range(self.fields_layout.count())):
            widget = self.fields_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.field_widgets.clear()
    
    def select_output(self):
        initial_dir = os.getcwd()
        initial_name = "filled_form.pdf"
        
        if self.input_path:
            initial_dir = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            initial_name = f"{base_name}_filled.pdf"
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти заповнену форму як",
            os.path.join(initial_dir, initial_name),
            "PDF файли (*.pdf)"
        )
        if path:
            self.output_path = path
            self.save_label.setText(f"Зберегти як: {os.path.basename(path)}")
    
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
    
    def fill_form(self):
        if not self.input_path or not self.output_path:
            return
        
        if not self.check_file_exists():
            return
        
        self.fields_data = {}
        for field_name, widget in self.field_widgets.items():
            if isinstance(widget, QLineEdit):
                self.fields_data[field_name] = widget.text()
            elif isinstance(widget, QCheckBox):
                self.fields_data[field_name] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                self.fields_data[field_name] = widget.currentText()
        
        self.fill_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        
        self.thread = FormsThread(
            self.input_path,
            self.output_path,
            self.fields_data
        )
        self.thread.finished.connect(self.on_fill_finished)
        self.thread.error.connect(self.on_fill_error)
        self.thread.start()
    
    def on_fill_finished(self, message):
        self.progress.setVisible(False)
        self.fill_btn.setEnabled(True)
        self.status_signal.emit(message)
        QMessageBox.information(self, "Успішно", message)
    
    def on_fill_error(self, error):
        self.progress.setVisible(False)
        self.fill_btn.setEnabled(True)
        self.status_signal.emit(f"Помилка: {error}")
        QMessageBox.critical(self, "Помилка", f"Не вдалося заповнити форму:\n{error}")
