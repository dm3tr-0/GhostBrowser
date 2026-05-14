import sys
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QPushButton, QHBoxLayout, QSlider, QLabel)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineScript
from PyQt5.QtGui import QCursor

WDA_EXCLUDEFROMCAPTURE = 0x00000011

def protect_window_from_capture(hwnd):
    user32 = ctypes.windll.user32
    user32.SetWindowDisplayAffinity.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    user32.SetWindowDisplayAffinity.restype = ctypes.c_bool
    result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
    if not result:
        error = ctypes.get_last_error()
        raise RuntimeError(f"SetWindowDisplayAffinity failed with error {error}")

def inject_cursor_fixer():
    script_code = """
    (function() {
        var style = document.createElement('style');
        style.innerHTML = '* { cursor: default !important; }';
        document.head.appendChild(style);
        
        document.addEventListener('mouseover', function(e) {
            document.body.style.cursor = 'default';
        });
        
        var observer = new MutationObserver(function() {
            document.body.style.cursor = 'default';
            var elements = document.querySelectorAll('[style*="cursor"]');
            elements.forEach(function(el) {
                el.style.cursor = 'default';
            });
        });
        observer.observe(document.body, { attributes: true, subtree: true, childList: true });
    })();
    """
    
    script = QWebEngineScript()
    script.setName("cursorFixer")
    script.setSourceCode(script_code)
    script.setInjectionPoint(QWebEngineScript.DocumentReady)
    script.setWorldId(QWebEngineScript.MainWorld)
    script.setRunsOnSubFrames(True)  # Также работает для iframe
    
    return script

class FixedCursorWebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        profile = QWebEngineProfile.defaultProfile()
        profile.scripts().insert(inject_cursor_fixer())
        
        self._original_set_cursor = None
    
    def setCursor(self, cursor):
        super().setCursor(QCursor(Qt.ArrowCursor))

class GhostBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("test game project")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        top_panel = QWidget()
        top_panel.setStyleSheet("background-color: #2d2d2d; padding: 5px;")
        panel_layout = QHBoxLayout(top_panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)
        
        url_label = QLabel("URL:")
        url_label.setStyleSheet("color: white;")
        panel_layout.addWidget(url_label)
        
        self.url_input = QLineEdit();self.url_input.setCursor(QCursor(Qt.ArrowCursor))
        self.url_input.setPlaceholderText("https://google.com")
        self.url_input.setStyleSheet("background-color: white; padding: 5px;")
        self.url_input.returnPressed.connect(self.navigate_to_url)
        panel_layout.addWidget(self.url_input)
        
        go_button = QPushButton("Go")
        go_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        go_button.clicked.connect(self.navigate_to_url)
        panel_layout.addWidget(go_button)
        
        refresh_button = QPushButton("⟳")
        refresh_button.setFixedWidth(40)
        refresh_button.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        refresh_button.clicked.connect(self.refresh_page)
        panel_layout.addWidget(refresh_button)
        
        main_layout.addWidget(top_panel)
        
        alpha_panel = QWidget()
        alpha_panel.setStyleSheet("background-color: #2d2d2d; padding: 5px;")
        alpha_layout = QHBoxLayout(alpha_panel)
        alpha_layout.setContentsMargins(5, 5, 5, 5)
        
        alpha_label = QLabel("Прозрачность:")
        alpha_label.setStyleSheet("color: white;")
        alpha_layout.addWidget(alpha_label)
        
        self.alpha_slider = QSlider(Qt.Horizontal)
        self.alpha_slider.setMinimum(30)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(100)
        self.alpha_slider.valueChanged.connect(self.change_transparency)
        alpha_layout.addWidget(self.alpha_slider)
        
        self.alpha_value_label = QLabel("100%")
        self.alpha_value_label.setStyleSheet("color: white; min-width: 40px;")
        alpha_layout.addWidget(self.alpha_value_label)
        
        main_layout.addWidget(alpha_panel)
        
        self.browser = FixedCursorWebView()
        self.browser.setUrl(QUrl("https://google.com"))
        main_layout.addWidget(self.browser)
        
        self.setGeometry(100, 100, 900, 700)
        
        self.setCursor(QCursor(Qt.ArrowCursor))
        
        self.show()
        
        hwnd = int(self.winId())
        protect_window_from_capture(hwnd)
        
    
    def navigate_to_url(self):
        url = self.url_input.text()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        self.browser.setUrl(QUrl(url))
        self.url_input.clear()
    
    def refresh_page(self):
        self.browser.reload()
    
    def change_transparency(self, value):
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        self.alpha_value_label.setText(f"{value}%")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GhostBrowser()
    sys.exit(app.exec_())