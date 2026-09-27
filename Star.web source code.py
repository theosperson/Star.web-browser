import sys
import os
import re
import json
import psutil
from collections import Counter
from urllib.parse import parse_qs, urlparse

# 1. SET CHROMIUM ANTI-BOT FLAGS BEFORE CREATING QAPPLICATION
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
    "--enable-logging --log-level=3 "
    "--disable-blink-features=AutomationControlled "
    "--disable-features=IsolateOrigins,site-per-process "
    "--no-sandbox"
)

from PyQt6.QtCore import QUrl, Qt, QTimer, QRectF
from PyQt6.QtGui import (
    QAction, QColor, QPainter, QBrush, QPen, QLinearGradient
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QDockWidget, QFrame, QCheckBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineScript
)

SHORTCUTS_FILE = "shortcuts.json"

# REAL CHROME USER AGENT
CHROME_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

# STEALTH JS TO SPOOF AUTOMATION DETECTION
STEALTH_JS = """
// Mask webdriver flag
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Spoof standard Chrome runtime object
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {}
};

// Spoof plugins length
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Spoof languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});
"""

DEFAULT_SHORTCUTS = [
    {"title": "Google", "url": "https://www.google.com", "icon": "🌐"},
    {"title": "YouTube", "url": "https://www.youtube.com", "icon": "▶"},
    {"title": "GitHub", "url": "https://github.com", "icon": "🐙"},
    {"title": "Reddit", "url": "https://www.reddit.com", "icon": "🤖"},
    {"title": "ChatGPT", "url": "https://chatgpt.com", "icon": "🧠"}
]


# -------------------------------------------------------------------
# SHORTCUT PERSISTENCE HELPERS
# -------------------------------------------------------------------
def load_shortcuts():
    if os.path.exists(SHORTCUTS_FILE):
        try:
            with open(SHORTCUTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    save_shortcuts(DEFAULT_SHORTCUTS)
    return DEFAULT_SHORTCUTS


def save_shortcuts(shortcuts):
    try:
        with open(SHORTCUTS_FILE, "w", encoding="utf-8") as f:
            json.dump(shortcuts, f, indent=2)
    except Exception as e:
        print(f"Error saving shortcuts: {e}")


# -------------------------------------------------------------------
# HOME DYNAMIC HTML GENERATOR
# -------------------------------------------------------------------
def generate_home_html(shortcuts):
    shortcuts_json = json.dumps(shortcuts)

    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            background-color: #05010a;
            color: #ff0055;
            font-family: 'Segoe UI', 'Consolas', monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}

        /* RED LAVA ANIMATION KEYFRAMES (LEFT TO RIGHT) */
        @keyframes lavaFlow {{
            0% {{ background-position: -100% 0; }}
            -100% {{ background-position: 0% 0; }}
        }}

        .container {{
            border: 2px solid #ff0055;
            box-shadow: 0 0 25px #9d00ff, 0 0 15px rgba(255, 0, 0, 0.4);
            padding: 40px 35px 35px 35px;
            background: rgba(18, 5, 36, 0.95);
            border-radius: 12px;
            text-align: center;
            width: 85%;
            max-width: 700px;
            position: relative;
            overflow: hidden; /* Clips the rounded top bar */
        }}

        /* FLOWING RED LAVA TOP BAR */
        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 7px;
            background: linear-gradient(
                90deg, 
                #800000 0%, 
                #ff0000 20%, 
                #ff5500 40%, 
                #ff0055 60%, 
                #ff0000 80%, 
                #800000 100%
            );
            background-size: 200% 100%;
            animation: lavaFlow 3s linear infinite;
            box-shadow: 0 0 12px #ff0000, 0 0 20px #ff3300;
        }}

        h1 {{
            font-size: 2.8rem;
            text-shadow: 0 0 10px #ff0055, 0 0 20px #9d00ff;
            margin-bottom: 5px;
            letter-spacing: 3px;
        }}
        .sub {{
            color: #00ffff;
            font-size: 0.95rem;
            margin-bottom: 25px;
            letter-spacing: 1px;
        }}
        .search-box {{
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
        }}
        input[type="text"] {{
            flex: 1;
            background: #0f031d;
            border: 1px solid #9d00ff;
            color: #00ffff;
            padding: 12px 16px;
            font-size: 15px;
            border-radius: 6px;
            outline: none;
            box-shadow: inset 0 0 8px #1c0638;
        }}
        input[type="text"]:focus {{
            border: 1px solid #ff0055;
            box-shadow: 0 0 12px #ff0055;
        }}
        .btn {{
            background: linear-gradient(90deg, #9d00ff, #ff0055);
            color: #fff;
            border: none;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{
            box-shadow: 0 0 15px #ff0055;
        }}
        .shortcuts-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .shortcuts-title {{
            color: #b500fe;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .shortcuts-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }}
        .shortcut-card {{
            background: #100424;
            border: 1px solid #2d0b52;
            padding: 12px;
            border-radius: 8px;
            color: #f0f0f0;
            text-decoration: none;
            font-size: 13px;
            font-weight: bold;
            transition: 0.2s;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
        }}
        .shortcut-card:hover {{
            border-color: #ff0055;
            color: #00ffff;
            box-shadow: 0 0 10px #9d00ff;
            transform: translateY(-2px);
        }}
        .shortcut-content {{
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            flex: 1;
        }}
        .delete-btn {{
            color: #ff0055;
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 4px;
            cursor: pointer;
            visibility: hidden;
            background: rgba(255, 0, 85, 0.15);
        }}
        .shortcut-card:hover .delete-btn {{
            visibility: visible;
        }}
        .delete-btn:hover {{
            background: #ff0055;
            color: #fff;
        }}
        .add-card {{
            border: 1px dashed #9d00ff;
            background: #090214;
            color: #00ffff;
            justify-content: center;
            cursor: pointer;
        }}
        .add-card:hover {{
            border-color: #00ffff;
            background: #120529;
        }}
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(5, 1, 10, 0.85);
            backdrop-filter: blur(4px);
            align-items: center;
            justify-content: center;
            z-index: 100;
        }}
        .modal-box {{
            background: #100424;
            border: 2px solid #ff0055;
            box-shadow: 0 0 20px #9d00ff, 0 0 15px rgba(255, 0, 0, 0.4);
            padding: 30px 25px 25px 25px;
            border-radius: 10px;
            width: 320px;
            text-align: left;
            position: relative;
            overflow: hidden;
        }}
        /* MODAL BOX TOP LAVA BAR */
        .modal-box::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 6px;
            background: linear-gradient(
                90deg, 
                #800000 0%, 
                #ff0000 20%, 
                #ff5500 40%, 
                #ff0055 60%, 
                #ff0000 80%, 
                #800000 100%
            );
            background-size: 200% 100%;
            animation: lavaFlow 3s linear infinite;
            box-shadow: 0 0 10px #ff0000;
        }}
        .modal-box h3 {{
            margin-top: 0;
            color: #ff0055;
            font-size: 16px;
        }}
        .modal-box label {{
            display: block;
            font-size: 11px;
            color: #b500fe;
            margin-top: 10px;
            margin-bottom: 4px;
        }}
        .modal-box input {{
            width: 100%;
            box-sizing: border-box;
            margin-bottom: 10px;
        }}
        .modal-actions {{
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            margin-top: 15px;
        }}
    </style>
    <script>
        const shortcuts = {shortcuts_json};

        function handleSearch(e) {{
            e.preventDefault();
            const query = document.getElementById('searchQuery').value.trim();
            if (!query) return;
            if (query.startsWith('http://') || query.startsWith('https://')) {{
                window.location.href = query;
            }} else if (query.includes('.') && !query.includes(' ')) {{
                window.location.href = 'https://' + query;
            }} else {{
                // PURE GOOGLE SEARCH
                window.location.href = 'https://www.google.com/search?q=' + encodeURIComponent(query);
            }}
        }}

        function openAddModal() {{
            document.getElementById('addModal').style.display = 'flex';
            document.getElementById('nodeTitle').focus();
        }}

        function closeModal() {{
            document.getElementById('addModal').style.display = 'none';
        }}

        function submitShortcut() {{
            const title = document.getElementById('nodeTitle').value.trim();
            let url = document.getElementById('nodeUrl').value.trim();
            const icon = document.getElementById('nodeIcon').value.trim() || '🌐';

            if (!title || !url) return;
            if (!url.startsWith('http://') && !url.startsWith('https://')) {{
                url = 'https://' + url;
            }}

            window.location.href = `titan-action://add?title=${{encodeURIComponent(title)}}&url=${{encodeURIComponent(url)}}&icon=${{encodeURIComponent(icon)}}`;
        }}

        function deleteShortcut(idx, event) {{
            event.stopPropagation();
            if (confirm('Delete this Shortcut?')) {{
                window.location.href = `titan-action://delete?index=${{idx}}`;
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Star.web</h1>
        <div class="sub">Star.web</div>

        <form class="search-box" onsubmit="handleSearch(event)">
            <input type="text" id="searchQuery" placeholder="Search Google or enter URL..." autofocus />
            <button class="btn" type="submit">Search</button>
        </form>

        <div class="shortcuts-header">
            <span class="shortcuts-title">Shortcuts</span>
        </div>

        <div class="shortcuts-grid" id="grid">
""" + "".join([
        f"""
            <div class="shortcut-card">
                <div class="shortcut-content" onclick="window.location.href='{sc['url']}'">
                    <span>{sc.get('icon', '🌐')}</span>
                    <span>{sc['title']}</span>
                </div>
                <span class="delete-btn" onclick="deleteShortcut({i}, event)">✖</span>
            </div>
    """ for i, sc in enumerate(shortcuts)
    ]) + """
            <div class="shortcut-card add-card" onclick="openAddModal()">
                + Add shortcut
            </div>
        </div>
    </div>

    <!-- MODAL POPUP -->
    <div class="modal-overlay" id="addModal">
        <div class="modal-box">
            <h3>Add new shortcut</h3>
            <label>Shortcut title</label>
            <input type="text" id="nodeTitle" placeholder="e.g. GitHub" />
            <label>Shortcut URL</label>
            <input type="text" id="nodeUrl" placeholder="e.g. github.com" />
            <label>Icon</label>
            <input type="text" id="nodeIcon" placeholder="e.g. 🐙" />
            <div class="modal-actions">
                <button class="btn" style="background: #2d0b52;" onclick="closeModal()">Cancel</button>
                <button class="btn" onclick="submitShortcut()">Save shortcut</button>
            </div>
        </div>
    </div>
</body>
</html>
"""


# -------------------------------------------------------------------
# HTTP INTERCEPTOR WITH GOOGLE HEADER SPOOFING
# -------------------------------------------------------------------
class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.enabled = True
        self.blocked_count = 0

        self.ad_domains = [
            "doubleclick.net", "googleadservices.com", "googlesyndication.com",
            "adservice.google.com", "amazon-adsystem.com", "adnxs.com",
            "taboola.com", "outbrain.com", "popads.net", "adroll.com"
        ]

    def interceptRequest(self, info):
        # Inject modern Chrome Client Hints required by Google
        info.setHttpHeader(b"Sec-CH-UA", b'"Chromium";v="128", "Not=A?Brand";v="24", "Google Chrome";v="128"')
        info.setHttpHeader(b"Sec-CH-UA-Mobile", b"?0")
        info.setHttpHeader(b"Sec-CH-UA-Platform", b'"Windows"')
        info.setHttpHeader(b"Sec-Fetch-Dest", b"document")
        info.setHttpHeader(b"Sec-Fetch-Mode", b"navigate")
        info.setHttpHeader(b"Sec-Fetch-Site", b"none")
        info.setHttpHeader(b"Sec-Fetch-User", b"?1")

        url = info.requestUrl().toString()
        if self.enabled:
            for domain in self.ad_domains:
                if domain in url:
                    info.block(True)
                    self.blocked_count += 1
                    return


# -------------------------------------------------------------------
# MAIN WINDOW
# -------------------------------------------------------------------
class Starwebbrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Star.web Browser")
        self.setGeometry(100, 100, 1300, 850)

        self.shortcuts = load_shortcuts()

        # PERSISTENT PROFILE SETUP
        profile_path = os.path.join(os.getcwd(), "google_session")
        self.profile = QWebEngineProfile("GoogleTitanProfile", self)
        self.profile.setPersistentStoragePath(profile_path)
        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.profile.setHttpUserAgent(CHROME_USER_AGENT)

        # INJECT STEALTH JS SCRIPT TO HIDE AUTOMATION
        script = QWebEngineScript()
        script.setSourceCode(STEALTH_JS)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)

        # ATTACH INTERCEPTOR
        self.interceptor = AdBlockInterceptor()
        self.profile.setUrlRequestInterceptor(self.interceptor)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.setup_navbar()
        self.add_new_tab(home=True)

    def setup_navbar(self):
        self.navbar = QToolBar()
        self.addToolBar(self.navbar)

        back_btn = QAction("◄", self)
        back_btn.triggered.connect(lambda: self.current_browser().back() if self.current_browser() else None)
        self.navbar.addAction(back_btn)

        reload_btn = QAction("↻", self)
        reload_btn.triggered.connect(lambda: self.current_browser().reload() if self.current_browser() else None)
        self.navbar.addAction(reload_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        add_btn = QAction("✚ New Tab", self)
        add_btn.triggered.connect(lambda: self.add_new_tab(home=True))
        self.navbar.addAction(add_btn)

    def add_new_tab(self, url=None, home=False):
        # Create WebEngineView with custom Google Profile
        browser = QWebEngineView()
        page = browser.page()

        idx = self.tabs.addTab(browser, "Cyber Hub")
        self.tabs.setCurrentIndex(idx)

        browser.urlChanged.connect(lambda qurl: self.handle_url_change(qurl, browser))
        browser.titleChanged.connect(lambda t: self.tabs.setTabText(self.tabs.indexOf(browser), t[:15]))

        if home or not url:
            browser.setHtml(generate_home_html(self.shortcuts))
        else:
            browser.setUrl(QUrl(url))

    def handle_url_change(self, qurl, browser):
        url_str = qurl.toString()
        if url_str.startswith("titan-action://"):
            parsed = urlparse(url_str)
            action = parsed.netloc
            params = parse_qs(parsed.query)

            if action == "add":
                title = params.get("title", ["New Node"])[0]
                node_url = params.get("url", ["https://google.com"])[0]
                icon = params.get("icon", ["🌐"])[0]
                self.shortcuts.append({"title": title, "url": node_url, "icon": icon})
                save_shortcuts(self.shortcuts)
                browser.setHtml(generate_home_html(self.shortcuts))
            elif action == "delete":
                idx = int(params.get("index", ["-1"])[0])
                if 0 <= idx < len(self.shortcuts):
                    self.shortcuts.pop(idx)
                    save_shortcuts(self.shortcuts)
                    browser.setHtml(generate_home_html(self.shortcuts))
            return

        if browser == self.current_browser():
            self.url_bar.setText(url_str)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            w = self.tabs.widget(index)
            w.deleteLater()
            self.tabs.removeTab(index)

    def current_browser(self):
        return self.tabs.currentWidget()

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return

        if not text.startswith("http://") and not text.startswith("https://"):
            if "." in text and " " not in text:
                text = "https://" + text
            else:
                # PURE GOOGLE SEARCH URL
                text = f"https://www.google.com/search?q={text.replace(' ', '+')}"

        if self.current_browser():
            self.current_browser().setUrl(QUrl(text))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Starwebbrowser()
    window.show()
    sys.exit(app.exec())
