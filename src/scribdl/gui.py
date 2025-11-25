import logging
import sys
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QFileDialog, QHBoxLayout
from qfluentwidgets import (
    FluentWindow,
    NavigationItemPosition,
    SubtitleLabel,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    TextEdit,
    InfoBar,
    InfoBarPosition,
    setTheme,
    Theme,
    BodyLabel,
    IndeterminateProgressRing,
    HyperlinkButton
)
from qfluentwidgets import FluentIcon as FIF

# Configure logging to capture in GUI
class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class DownloadThread(QThread):
    finished_signal = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str)

    def __init__(self, url: str, mode: str, output_dir: Optional[str] = None, use_selenium: bool = False):
        super().__init__()
        self.url = url
        self.mode = mode
        self.output_dir = output_dir
        self.use_selenium = use_selenium
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            if self.use_selenium:
                # Use Selenium downloader
                from scribdl.selenium_downloader import download_with_selenium
                
                download_with_selenium(
                    self.url,
                    self.mode,
                    self.output_dir,
                    check_stop=lambda: not self._is_running
                )
            else:
                # Use traditional BeautifulSoup downloader
                from scribdl.scribdl import get_scribd_document
                
                get_scribd_document(
                    self.url, 
                    self.mode, 
                    self.output_dir, 
                    check_stop=lambda: not self._is_running
                )
            
            if self._is_running:
                self.finished_signal.emit(True, "Download completed successfully!")
            else:
                self.finished_signal.emit(False, "Download stopped by user.")
                
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class ScribdDownloaderWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scribd PDF Downloader")
        self.resize(800, 600)
        
        # Main Widget
        self.main_widget = QWidget()
        self.main_widget.setObjectName("downloaderInterface")
        self.layout = QVBoxLayout(self.main_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # Title
        self.title_label = SubtitleLabel("Scribd PDF Downloader", self)
        self.layout.addWidget(self.title_label)

        # URL Input
        self.url_input = LineEdit(self)
        self.url_input.setPlaceholderText("Enter Scribd Document URL")
        self.layout.addWidget(self.url_input)

        # Output Directory Selection
        self.output_layout = QHBoxLayout()
        self.output_path_input = LineEdit(self)
        self.output_path_input.setPlaceholderText("Select Output Directory (Optional)")
        self.output_path_input.setReadOnly(True)
        self.output_layout.addWidget(self.output_path_input)
        
        self.browse_btn = PushButton("Browse", self)
        self.browse_btn.clicked.connect(self.browse_folder)
        self.output_layout.addWidget(self.browse_btn)
        
        self.layout.addLayout(self.output_layout)

        # Action Buttons & Status
        self.action_layout = QHBoxLayout()
        
        self.download_btn = PrimaryPushButton("Download", self)
        self.download_btn.clicked.connect(self.start_download)
        self.action_layout.addWidget(self.download_btn)
        
        self.stop_btn = PushButton("Stop", self)
        self.stop_btn.setIcon(FIF.CANCEL)
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        self.action_layout.addWidget(self.stop_btn)
        
        self.status_ring = IndeterminateProgressRing(self)
        self.status_ring.setFixedSize(24, 24)
        self.status_ring.setVisible(False)
        self.action_layout.addWidget(self.status_ring)
        
        self.status_label = BodyLabel("", self)
        self.action_layout.addWidget(self.status_label)
        
        self.action_layout.addStretch(1)
        self.layout.addLayout(self.action_layout)

        # Log Output
        self.log_output = TextEdit(self)
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)
        
        # Ko-fi Donation Button
        self.donation_layout = QHBoxLayout()
        self.donation_layout.addStretch(1)
        self.kofi_button = HyperlinkButton(
            url="https://ko-fi.com/solveproblem",
            text="☕ Support this project on Ko-fi",
            parent=self
        )
        self.kofi_button.setIcon(FIF.HEART)
        self.donation_layout.addWidget(self.kofi_button)
        self.donation_layout.addStretch(1)
        self.layout.addLayout(self.donation_layout)

        self.addSubInterface(self.main_widget, FIF.DOWNLOAD, "Downloader")
        
        # Setup Logging
        self.log_handler = QTextEditLogger(self.log_output)
        self.log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.INFO)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if folder:
            self.output_path_input.setText(folder)
    
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            InfoBar.error(
                title="Error",
                content="Please enter a valid URL.",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
            return

        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_ring.setVisible(True)
        self.status_ring.start()
        self.status_label.setText("Downloading...")
        
        self.log_output.clear()
        self.log_output.append(f"Starting download for: {url}")
        
        output_dir = self.output_path_input.text().strip() or None
        if output_dir:
            self.log_output.append(f"Saving to: {output_dir}")
            
        mode = "pdf"  # Always use PDF mode
        use_selenium = True  # Always use Selenium for PDF
        
        self.log_output.append(f"Mode: PDF")
        self.log_output.append(f"Method: Selenium (with auto-scroll)")
        self.log_output.append("⚠️ This will take longer but ensures all content is loaded")

        self.thread = DownloadThread(url, mode, output_dir, use_selenium)
        self.thread.finished_signal.connect(self.on_download_finished)
        self.thread.start()

    def stop_download(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Stopping...")

    def on_download_finished(self, success, message):
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_ring.stop()
        self.status_ring.setVisible(False)
        self.status_label.setText("Ready")
        
        if success:
            InfoBar.success(
                title="Success",
                content=message,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self
            )
        else:
            # If stopped by user, show warning instead of error
            if "stopped by user" in message:
                InfoBar.warning(
                    title="Stopped",
                    content=message,
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=self
                )
            else:
                InfoBar.error(
                    title="Error",
                    content=f"Download failed: {message}",
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    parent=self
                )

def main():
    app = QApplication(sys.argv)
    setTheme(Theme.DARK)
    w = ScribdDownloaderWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
