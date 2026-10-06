# tabs/forms_tab.py
import json
import os

from common.i18n.translator import translator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QFormLayout, QLineEdit,
    QCheckBox, QComboBox, QScrollArea, QGroupBox,
    QProgressBar, QMessageBox, QSpinBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PyPDFForm import PdfWrapper


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
            self.finished.emit(
                translator.tr('forms_success_message', 'forms').format(
                    output_path=self.output_path
                )
            )
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
        self.drop_label = QLabel(translator.tr('forms_drag_drop', 'forms'))
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
        self.file_label = QLabel(translator.tr('forms_no_file', 'forms'))
        file_layout.addWidget(self.file_label)
        
        self.load_btn = QPushButton(translator.tr('forms_open_pdf', 'forms'))
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
        self.save_label = QLabel(translator.tr('forms_no_output', 'forms'))
        save_layout.addWidget(self.save_label)
        
        self.save_btn = QPushButton(translator.tr('forms_select_path', 'forms'))
        self.save_btn.clicked.connect(self.select_output)
        save_layout.addWidget(self.save_btn)
        
        layout.addLayout(save_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.fill_btn = QPushButton(translator.tr('btn_fill_form', 'ui'))
        self.fill_btn.clicked.connect(self.fill_form)
        self.fill_btn.setEnabled(False)
        layout.addWidget(self.fill_btn)
    
    def retranslate_ui(self):
        """Оновлює переклади при зміні мови"""
        self.drop_label.setText(translator.tr('forms_drag_drop', 'forms'))
        
        if self.input_path:
            self.file_label.setText(
                translator.tr('forms_file_selected', 'forms').format(
                    filename=os.path.basename(self.input_path)
                )
            )
        else:
            self.file_label.setText(translator.tr('forms_no_file', 'forms'))
        
        if self.output_path:
            self.save_label.setText(
                translator.tr('forms_output_selected', 'forms').format(
                    filename=os.path.basename(self.output_path)
                )
            )
        else:
            self.save_label.setText(translator.tr('forms_no_output', 'forms'))
        
        self.load_btn.setText(translator.tr('forms_open_pdf', 'forms'))
        self.save_btn.setText(translator.tr('forms_select_path', 'forms'))
        self.fill_btn.setText(translator.tr('btn_fill_form', 'ui'))
        
        # Оновлюємо заголовки груп полів (якщо вони вже створені)
        for i in range(self.fields_layout.count()):
            widget = self.fields_layout.itemAt(i).widget()
            if isinstance(widget, QGroupBox):
                # Зберігаємо назву поля, вона не перекладається
                pass
    
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
                    self.drop_label.setText(translator.tr('forms_drop_here', 'forms'))
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
        self.drop_label.setText(translator.tr('forms_drag_drop', 'forms'))
    
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
        self.drop_label.setText(translator.tr('forms_drag_drop', 'forms'))
    
    def load_pdf_from_path(self, path):
        self.input_path = path
        self.file_label.setText(
            translator.tr('forms_file_selected', 'forms').format(
                filename=os.path.basename(path)
            )
        )
        
        self.suggest_output_name()
        
        try:
            wrapper = PdfWrapper(path)
            fields = wrapper.get_form_fields()
            
            self.clear_fields()
            
            if not fields:
                QMessageBox.warning(
                    self,
                    translator.tr('forms_warning_title', 'forms'),
                    translator.tr('forms_no_fields', 'forms')
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
                    widget.addItems([
                        translator.tr('forms_list_option_1', 'forms'),
                        translator.tr('forms_list_option_2', 'forms'),
                        translator.tr('forms_list_option_3', 'forms')
                    ])
                else:
                    widget = QLineEdit()
                    default_val = field_info.get('value', '')
                    if default_val and hasattr(widget, 'setText'):
                        widget.setText(str(default_val))
                
                field_layout.addRow(translator.tr('forms_value_label', 'forms'), widget)
                field_group.setLayout(field_layout)
                
                self.fields_layout.addWidget(field_group)
                self.field_widgets[field_name] = widget
            
            self.fill_btn.setEnabled(True)
            self.status_signal.emit(
                translator.tr('forms_fields_found', 'forms').format(count=len(fields))
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                translator.tr('status_error'),
                translator.tr('forms_read_error', 'forms').format(error=str(e))
            )
    
    def load_pdf(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            translator.tr('forms_select_pdf_title', 'forms'),
            "",
            translator.tr('forms_pdf_filter', 'forms')
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
            self.save_label.setText(
                translator.tr('forms_output_selected', 'forms').format(
                    filename=suggested_name
                )
            )
    
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
            translator.tr('forms_save_as_title', 'forms'),
            os.path.join(initial_dir, initial_name),
            translator.tr('forms_pdf_filter', 'forms')
        )
        if path:
            self.output_path = path
            self.save_label.setText(
                translator.tr('forms_output_selected', 'forms').format(
                    filename=os.path.basename(path)
                )
            )
    
    def check_file_exists(self):
        """Перевіряє чи існує файл і пропонує дії"""
        if os.path.exists(self.output_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(translator.tr('forms_file_exists_title', 'forms'))
            msg_box.setText(
                translator.tr('forms_file_exists_text', 'forms').format(
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
                    translator.tr('forms_output_selected', 'forms').format(
                        filename=os.path.basename(new_path)
                    )
                )
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
        QMessageBox.information(
            self,
            translator.tr('status_done'),
            message
        )
    
    def on_fill_error(self, error):
        self.progress.setVisible(False)
        self.fill_btn.setEnabled(True)
        self.status_signal.emit(
            translator.tr('forms_error_status', 'forms').format(error=error)
        )
        QMessageBox.critical(
            self,
            translator.tr('status_error'),
            translator.tr('forms_error_detail', 'forms').format(error=error)
        )
