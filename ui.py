from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QLabel, QFileDialog, QProgressBar, QHBoxLayout, QGridLayout, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon
import sys
import asyncio
from pathlib import Path
from fatura_isleyici import FaturaIsleyici

class IslemThread(QThread):
    progress = pyqtSignal(str, dict, dict)  # message, stats, file_details
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, fatura_dizini, cikti_dizini):
        super().__init__()
        self.fatura_dizini = fatura_dizini
        self.cikti_dizini = cikti_dizini
        self.is_running = True
        
    def run(self):
        try:
            async def run_isleyici():
                try:
                    isleyici = FaturaIsleyici(self.fatura_dizini, self.cikti_dizini)
                    isleyici.progress_callback = lambda msg, stats, file_details: self.progress.emit(msg, stats, file_details)
                    await isleyici.tum_yillari_isle()
                except Exception as e:
                    self.error.emit(str(e))
                finally:
                    self.finished.emit()
            
            asyncio.run(run_isleyici())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.is_running = False
            
    def stop(self):
        self.is_running = False
        self.wait()

class MacButton(QPushButton):
    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setFont(QFont(".AppleSystemUIFont", 13))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(36)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {('#0A84FF' if primary else '#2C2C2E')};
                color: {('#FFFFFF' if primary else '#FFFFFF')};
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                min-width: 160px;
            }}
            QPushButton:hover {{
                background-color: {('#0071E3' if primary else '#3A3A3C')};
            }}
            QPushButton:pressed {{
                background-color: {('#0058B6' if primary else '#48484A')};
            }}
            QPushButton:disabled {{
                background-color: #3A3A3C;
                color: #98989D;
            }}
        """)

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget#dashboard {
                background-color: #242424;
                border: 1px solid #383838;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #383838;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #4A4A4A;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        self.setObjectName("dashboard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Başlık ve özet kısmı
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("İşlem Durumu")
        title.setFont(QFont(".AppleSystemUIFont", 18, QFont.Weight.Medium))
        title.setStyleSheet("color: #FFFFFF;")
        
        self.summary_label = QLabel("Henüz işlem başlatılmadı")
        self.summary_label.setStyleSheet("""
            color: #98989D;
            background: transparent;
            padding: 4px 8px;
        """)
        self.summary_label.setFont(QFont(".AppleSystemUIFont", 13))
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.summary_label)
        
        layout.addWidget(header)
        
        # İşlem listesi
        self.process_list = QWidget()
        self.process_list.setStyleSheet("""
            QWidget {
                background-color: #2C2C2E;
                border-radius: 8px;
            }
        """)
        
        process_layout = QVBoxLayout(self.process_list)
        process_layout.setSpacing(8)
        process_layout.setContentsMargins(16, 16, 16, 16)
        
        scroll = QScrollArea()
        scroll.setWidget(self.process_list)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(scroll, 1)  # 1 stretch factor ile tüm alanı kapla

    def add_process_item(self, filename, fatura_count, year_distribution):
        item = QWidget()
        item.setStyleSheet("""
            QWidget {
                background-color: #333333;
                border-radius: 8px;
                padding: 16px;
                margin: 4px 0px;
            }
            QLabel#filename {
                color: #FFFFFF;
                font-weight: 500;
            }
            QLabel#details {
                color: #A0A0A0;
            }
        """)
        
        layout = QVBoxLayout(item)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 16, 16, 16)
        
        filename_label = QLabel(filename)
        filename_label.setObjectName("filename")
        filename_label.setFont(QFont(".AppleSystemUIFont", 14))
        
        details = QLabel(f"{fatura_count} fatura • {year_distribution}")
        details.setObjectName("details")
        details.setFont(QFont(".AppleSystemUIFont", 12))
        details.setWordWrap(True)
        
        layout.addWidget(filename_label)
        layout.addWidget(details)
        
        self.process_list.layout().addWidget(item)


class FormSection(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget#form {
                background-color: #242424;
                border: 1px solid #383838;
                border-radius: 12px;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        self.setObjectName("form")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Başlık
        title = QLabel("Dizin Seçimi")
        title.setFont(QFont(".AppleSystemUIFont", 18, QFont.Weight.Medium))
        layout.addWidget(title)
        
        # Form içeriği
        form_content = QWidget()
        form_layout = QVBoxLayout(form_content)
        form_layout.setSpacing(16)
        
        # Fatura dizini seçme
        self.select_button = MacButton("Fatura Dizini Seç")
        self.path_label = QLabel("Henüz dizin seçilmedi")
        self.path_label.setFont(QFont(".AppleSystemUIFont", 13))
        self.path_label.setStyleSheet("color: #86868B;")
        
        fatura_layout = QHBoxLayout()
        fatura_layout.addWidget(self.select_button)
        fatura_layout.addWidget(self.path_label, 1)
        form_layout.addLayout(fatura_layout)
        
        # Çıktı dizini seçme
        self.output_button = MacButton("Rapor Dizini Seç")
        self.output_label = QLabel("Henüz dizin seçilmedi")
        self.output_label.setFont(QFont(".AppleSystemUIFont", 13))
        self.output_label.setStyleSheet("color: #86868B;")
        
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_button)
        output_layout.addWidget(self.output_label, 1)
        form_layout.addLayout(output_layout)
        
        layout.addWidget(form_content)


class FaturaUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fatura İşleyici")
        self.setMinimumSize(1200, 800)
        
        # Uygulama ikonunu ayarla
        icon_path = Path(__file__).parent / "icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)
            # macOS için dock ikonu ayarla
            if sys.platform == "darwin":
                from PyQt6.QtWidgets import QApplication
                QApplication.setWindowIcon(icon)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1A1A1A;
            }
            QLabel {
                color: #FFFFFF;
            }
            QProgressBar {
                border: none;
                background-color: #2C2C2E;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #0A84FF;
                border-radius: 4px;
            }
        """)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)
        
        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)
        
        self.title_label = QLabel("Fatura İşleyici")
        self.title_label.setFont(QFont(".AppleSystemUIFont", 34, QFont.Weight.Light))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle_label = QLabel("Faturalarınızı kolayca analiz edin")
        self.subtitle_label.setFont(QFont(".AppleSystemUIFont", 15))
        self.subtitle_label.setStyleSheet("color: #86868B;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        layout.addWidget(header)
        
        # Orta kısım (Form ve Dashboard)
        middle_section = QHBoxLayout()
        middle_section.setSpacing(24)
        
        self.form_section = FormSection()
        middle_section.addWidget(self.form_section)
        
        self.dashboard = DashboardWidget()
        middle_section.addWidget(self.dashboard)
        
        layout.addLayout(middle_section)
        
        # Alt kısım
        bottom_section = QWidget()
        bottom_layout = QVBoxLayout(bottom_section)
        bottom_layout.setSpacing(16)
        
        self.process_button = MacButton("İşlemi Başlat", primary=True)
        self.process_button.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        
        self.status_label = QLabel("")
        self.status_label.setFont(QFont(".AppleSystemUIFont", 13))
        self.status_label.setStyleSheet("color: #1D1D1F;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        bottom_layout.addWidget(self.process_button, alignment=Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(self.progress_bar)
        bottom_layout.addWidget(self.status_label)
        
        layout.addWidget(bottom_section)
        
        # Footer
        self.footer_label = QLabel("© 2025 Hüseyin ASLIM - Codev")
        self.footer_label.setFont(QFont(".AppleSystemUIFont", 12))
        self.footer_label.setStyleSheet("color: #86868B;")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.footer_label)
        
        # Bağlantıları kur
        self.setup_connections()
        
        # State
        self.selected_dir = None
        self.output_dir = None
        self.thread = None
        
        # Uygulama kapatılırken thread'i temizle
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
    
    def setup_connections(self):
        self.form_section.select_button.clicked.connect(self.select_directory)
        self.form_section.output_button.clicked.connect(self.select_output_directory)
        self.process_button.clicked.connect(self.start_processing)
    
    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Fatura Dizinini Seç")
        if dir_path:
            self.selected_dir = dir_path
            self.form_section.path_label.setText(f"Seçilen dizin: {Path(dir_path).name}")
            self.check_ready()
    
    def select_output_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Rapor Dizinini Seç")
        if dir_path:
            self.output_dir = dir_path
            self.form_section.output_label.setText(f"Seçilen dizin: {Path(dir_path).name}")
            self.check_ready()
    
    def check_ready(self):
        # Her iki dizin de seçili ise işlem başlatma butonunu aktif et
        self.process_button.setEnabled(bool(self.selected_dir and self.output_dir))
    
    def start_processing(self):
        if not self.selected_dir or not self.output_dir:
            return
            
        self.process_button.setEnabled(False)
        self.form_section.select_button.setEnabled(False)
        self.form_section.output_button.setEnabled(False)  # Çıktı dizini butonunu da devre dışı bırak
        self.progress_bar.setMaximum(0)
        
        # Önceki thread varsa temizle
        if self.thread:
            self.thread.stop()
            self.thread.wait()
            
        self.thread = IslemThread(self.selected_dir, self.output_dir)
        self.thread.progress.connect(self.update_progress)
        self.thread.error.connect(self.handle_error)
        self.thread.finished.connect(self.processing_finished)
        self.thread.start()
    
    def update_progress(self, message, stats, file_details):
        # Özet bilgiyi güncelle
        if all(key in stats for key in ['islenen_dosya', 'toplam_dosya', 'bulunan_fatura']):
            self.dashboard.summary_label.setText(
                f"{stats['islenen_dosya']}/{stats['toplam_dosya']} dosya işlendi, {stats['bulunan_fatura']} fatura bulundu"
            )
        
        # Dosya detayını ekle
        if file_details:
            self.dashboard.add_process_item(
                file_details['filename'],
                file_details['fatura_count'],
                file_details['year_distribution']
            )
        
        # Durum mesajını güncelle
        self.status_label.setText(message)
    
    def handle_error(self, error_message):
        self.status_label.setText(f"Hata: {error_message}")
        self.status_label.setStyleSheet("color: #FF3B30;")  # Hata mesajını kırmızı yap
        self.processing_finished()
    
    def processing_finished(self):
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100)
        self.process_button.setEnabled(True)
        self.form_section.select_button.setEnabled(True)
        self.form_section.output_button.setEnabled(True)  # Çıktı dizini butonunu tekrar aktif et
        
        if "Hata" not in self.status_label.text():
            self.status_label.setStyleSheet("color: #1D1D1F;")
            self.status_label.setText("İşlem tamamlandı!")
    
    def closeEvent(self, event):
        if self.thread and self.thread.is_running:
            self.thread.stop()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = FaturaUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 