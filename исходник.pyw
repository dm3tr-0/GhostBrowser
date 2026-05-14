import sys, os
import ctypes
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QLineEdit, QPushButton, QHBoxLayout, QSlider, QLabel,
                             QTabWidget)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEngineScript, QWebEngineSettings
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
    script.setRunsOnSubFrames(True)
    
    return script

class FixedCursorWebView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Включаем экспериментальные возможности (может помочь с капчей)
        try:
            from PyQt5.QtWebEngineWidgets import QWebEngineSettings
	    # Пытаемся включить экспериментальные флаги (не все сработают)
            os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-features=NetworkService,NetworkServiceInProcess --disable-features=SameSiteByDefaultCookies,CookiesWithoutSameSiteMustBeSecure"
        except: pass
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        
        profile.scripts().insert(inject_cursor_fixer())
    
    def createWindow(self, type_):
        return self
    
    def setCursor(self, cursor):
        super().setCursor(QCursor(Qt.ArrowCursor))

class GhostBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Ghost Browser")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Верхняя панель
        top_panel = QWidget()
        top_panel.setStyleSheet("background-color: #2d2d2d; padding: 5px;")
        panel_layout = QHBoxLayout(top_panel)
        panel_layout.setContentsMargins(5, 5, 5, 5)
        
        back_button = QPushButton("◀")
        back_button.setFixedWidth(40)
        back_button.setStyleSheet("background-color: #555; color: white; padding: 5px;")
        back_button.clicked.connect(self.go_back)
        panel_layout.addWidget(back_button)
        
        forward_button = QPushButton("▶")
        forward_button.setFixedWidth(40)
        forward_button.setStyleSheet("background-color: #555; color: white; padding: 5px;")
        forward_button.clicked.connect(self.go_forward)
        panel_layout.addWidget(forward_button)
        
        refresh_button = QPushButton("⟳")
        refresh_button.setFixedWidth(40)
        refresh_button.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        refresh_button.clicked.connect(self.refresh_page)
        panel_layout.addWidget(refresh_button)
        
        url_label = QLabel("URL:")
        url_label.setStyleSheet("color: white;")
        panel_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setCursor(QCursor(Qt.ArrowCursor))
        self.url_input.setPlaceholderText("https://google.com")
        self.url_input.setStyleSheet("background-color: white; padding: 5px;")
        self.url_input.returnPressed.connect(self.navigate_to_url)
        panel_layout.addWidget(self.url_input)
        
        go_button = QPushButton("Go")
        go_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        go_button.clicked.connect(self.navigate_to_url)
        panel_layout.addWidget(go_button)
        
        new_tab_button = QPushButton("+")
        new_tab_button.setFixedWidth(40)
        new_tab_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; font-size: 16px;")
        new_tab_button.clicked.connect(self.new_tab)
        panel_layout.addWidget(new_tab_button)
        
        main_layout.addWidget(top_panel)
        
        # Панель прозрачности
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
        
        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs)
        
        self.new_tab("https://google.com")
        
        self.setGeometry(100, 100, 1000, 700)
        self.setCursor(QCursor(Qt.ArrowCursor))
        
        self.show()
        
        hwnd = int(self.winId())
        protect_window_from_capture(hwnd)
    
    def new_tab(self, url=None):
        browser = FixedCursorWebView()
        
        if url:
            browser.setUrl(QUrl(url))
        else:
            browser.setUrl(QUrl("https://google.com"))
        
        browser.urlChanged.connect(lambda qurl, b=browser: self.update_url_bar(b))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b, title))
        
        index = self.tabs.addTab(browser, "Новая вкладка")
        self.tabs.setCurrentIndex(index)
        return browser
    
    def close_tab(self, index):
        if self.tabs.count() > 1:
            widget = self.tabs.widget(index)
            widget.deleteLater()
            self.tabs.removeTab(index)
        else:
            self.new_tab()
            widget = self.tabs.widget(index)
            widget.deleteLater()
            self.tabs.removeTab(index)
    
    def on_tab_changed(self, index):
        if index >= 0:
            browser = self.tabs.widget(index)
            self.url_input.setText(browser.url().toString())
    
    def update_url_bar(self, browser):
        if self.tabs.currentWidget() == browser:
            self.url_input.setText(browser.url().toString())
    
    def update_tab_title(self, browser, title):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i) == browser:
                short_title = title[:30] + "..." if len(title) > 30 else title
                self.tabs.setTabText(i, short_title if short_title else "Новая вкладка")
                break
    
    def navigate_to_url(self):
        url = self.url_input.text()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.setUrl(QUrl(url))
        self.url_input.clear()
    
    def refresh_page(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.reload()
    
    def go_back(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.back()
    
    def go_forward(self):
        current_browser = self.tabs.currentWidget()
        if current_browser:
            current_browser.forward()
    
    def change_transparency(self, value):
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        self.alpha_value_label.setText(f"{value}%")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GhostBrowser()
    sys.exit(app.exec_())