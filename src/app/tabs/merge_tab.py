# tabs/merge_tab.py
import json
import os

from common.i18n.translator import translator

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QFileDialog, QLabel, QProgressBar,
    QMessageBox
)
from PySide6.QtCore import Signal, QThread, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from pypdf import PdfWriter

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
            self.finished.emit(
                translator.tr('merge_success_message', 'merge').format(
                    output_path=self.output_path
                )
            )
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
        self.drop_label = QLabel(translator.tr('merge_drag_drop', 'merge'))
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
        self.add_btn = QPushButton(translator.tr('merge_add_pdfs', 'merge'))
        self.add_btn.clicked.connect(self.add_pdfs)
        self.clear_btn = QPushButton(translator.tr('merge_clear_list', 'merge'))
        self.clear_btn.clicked.connect(self.clear_list)
        self.move_up_btn = QPushButton(translator.tr('merge_move_up', 'merge'))
        self.move_up_btn.clicked.connect(self.move_up)
        self.move_down_btn = QPushButton(translator.tr('merge_move_down', 'merge'))
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
        self.path_label = QLabel(translator.tr('merge_no_path', 'merge'))
        path_layout.addWidget(self.path_label)
        self.path_btn = QPushButton(translator.tr('merge_select_path', 'merge'))
        self.path_btn.clicked.connect(self.select_output)
        path_layout.addWidget(self.path_btn)
        layout.addLayout(path_layout)
        
        # Прогрес та кнопка
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        self.merge_btn = QPushButton(translator.tr('btn_merge', 'ui'))
        self.merge_btn.clicked.connect(self.merge)
        self.merge_btn.setEnabled(False)
        layout.addWidget(self.merge_btn)
    
    def retranslate_ui(self):
        """Оновлює переклади при зміні мови"""
        self.drop_label.setText(translator.tr('merge_drag_drop', 'merge'))
        self.add_btn.setText(translator.tr('merge_add_pdfs', 'merge'))
        self.clear_btn.setText(translator.tr('merge_clear_list', 'merge'))
        self.move_up_btn.setText(translator.tr('merge_move_up', 'merge'))
        self.move_down_btn.setText(translator.tr('merge_move_down', 'merge'))
        self.path_btn.setText(translator.tr('merge_select_path', 'merge'))
        self.merge_btn.setText(translator.tr('btn_merge', 'ui'))
        
        if self.output_path:
            self.path_label.setText(
                translator.tr('merge_path_selected', 'merge').format(
                    path=self.output_path
                )
            )
        else:
            self.path_label.setText(translator.tr('merge_no_path', 'merge'))
    
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
            self.drop_label.setText(translator.tr('merge_drop_here', 'merge'))
    
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
        self.drop_label.setText(translator.tr('merge_drag_drop', 'merge'))
    
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
            self.status_signal.emit(
                translator.tr('merge_pdfs_added', 'merge').format(count=len(files))
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
                border-color: #2196F3;
                background-color: #e3f2fd;
            }
        """)
        self.drop_label.setText(translator.tr('merge_drag_drop', 'merge'))
    
    def add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            translator.tr('merge_select_pdfs_title', 'merge'),
            "",
            translator.tr('merge_pdf_filter', 'merge')
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
            self.path_label.setText(
                translator.tr('merge_path_selected', 'merge').format(
                    path=suggested_path
                )
            )
            self.update_merge_button()
    
    def clear_list(self):
        self.pdf_paths.clear()
        self.pdf_list.clear()
        self.output_path = ""
        self.path_label.setText(translator.tr('merge_no_path', 'merge'))
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
            translator.tr('merge_save_as_title', 'merge'),
            os.path.join(initial_dir, initial_name),
            translator.tr('merge_pdf_filter', 'merge')
        )
        if path:
            self.output_path = path
            self.path_label.setText(
                translator.tr('merge_path_selected', 'merge').format(
                    path=path
                )
            )
            self.update_merge_button()
    
    def update_merge_button(self):
        self.merge_btn.setEnabled(
            len(self.pdf_paths) > 1 and self.output_path != ""
        )
    
    def check_file_exists(self):
        """Перевіряє чи існує файл і пропонує дії"""
        if os.path.exists(self.output_path):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(translator.tr('merge_file_exists_title', 'merge'))
            msg_box.setText(
                translator.tr('merge_file_exists_text', 'merge').format(
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
                    translator.tr('merge_path_selected', 'merge').format(
                        path=new_path
                    )
                )
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
        QMessageBox.information(
            self,
            translator.tr('status_done'),
            message
        )
    
    def on_merge_error(self, error):
        self.progress.setVisible(False)
        self.merge_btn.setEnabled(True)
        self.status_signal.emit(
            translator.tr('merge_error_status', 'merge').format(error=error)
        )
        QMessageBox.critical(
            self,
            translator.tr('status_error'),
            translator.tr('merge_error_detail', 'merge').format(error=error)
        )
