import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QMessageBox, QTabBar, QStackedWidget, QSizePolicy, QFrame, QListWidget,
    QLineEdit, QFileDialog, QFormLayout, QCheckBox
)
from PySide6.QtGui import QPixmap, QPainter, QFont, QIcon, QColor
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Property, QRect, QThread, Signal
from func.ApplySkybox import install_skybox, install_assets
from func.ApplyDark import install_dark_textures
from func.Restore import restore_skybox, full_restore, restore_dark_textures
from func.APIFunc import download_file, unzip_file, delete_all_downloads
import json
import urllib.request
import tempfile
import shutil
import requests

# URLs for downloading resources
DarkTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DarkTextures.zip"
LightTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/LightTextures.zip"
DefaultTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DefaultTextures.zip"
DefaultSky = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DefaultSky.zip"
SkyboxPatch = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxPatch.zip"

# SkyBox data and download URLs
SkyName = ""
SkyboxZIPs = f"https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxZIPs/{SkyName}.zip"
SkyboxPNGsZIP = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxPNGs/SkyboxPNGs.zip"
SkysList = "https://raw.githubusercontent.com/eman225511/CustomDebloatedBloxLauncher/refs/heads/main/src/SkyboxZIPs/sky-list.txt"

print("[DEBUG] Starting CDBL...")
print("[DEBUG] Downloading required files...")

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_all_versions_paths():
    localappdata = os.environ.get('LOCALAPPDATA')
    paths = [
        os.path.join(localappdata, 'Roblox', 'Versions'),
        os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        os.path.join(localappdata, 'Fishstrap', 'Versions'),
    ]
    return [p for p in paths if os.path.exists(p)]

def get_all_roblox_paths():
    localappdata = os.environ.get('LOCALAPPDATA')
    paths = [
        os.path.join(localappdata, 'Roblox'),
        os.path.join(localappdata, 'Bloxstrap'),
        os.path.join(localappdata, 'Fishstrap'),
    ]
    return [p for p in paths if os.path.exists(p)]

def emoji_icon(emoji, size=20):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    font = QFont("Segoe UI Emoji", int(size * 0.8))
    painter.setFont(font)
    painter.setPen(Qt.white)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, emoji)
    painter.end()
    return QIcon(pixmap)

class AnimatedToggle(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 2 if not self.isChecked() else 22
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(38)
        self.setMaximumWidth(48)
        self.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
                min-height: 38px;
                height: 38px;
            }
        """)
        self.stateChanged.connect(self.animate_toggle)

    def animate_toggle(self, state):
        self._anim.stop()
        if state == Qt.Checked or state == 2:
            self._anim.setStartValue(self._offset)
            self._anim.setEndValue(22)
        else:
            self._anim.setStartValue(self._offset)
            self._anim.setEndValue(2)
        self._anim.start()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Draw the track
        track_rect = QRect(2, self.height() // 2 - 12, 40, 24)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#232428") if not self.isChecked() else QColor("#8edcff"))
        painter.drawRoundedRect(track_rect, 12, 12)
        # Draw the thumb
        thumb_rect = QRect(int(self._offset), self.height() // 2 - 10, 20, 20)
        painter.setBrush(QColor("#888") if not self.isChecked() else QColor("#22303a"))
        painter.drawEllipse(thumb_rect)

    def get_offset(self):
        return self._offset

    def set_offset(self, value):
        self._offset = value
        self.update()

    offset = Property(int, get_offset, set_offset)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CDBL")
        self.setMinimumSize(720, 520)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            #MainBg {
                background-color: #18191c;
                border-radius: 18px;
            }
        """)
        # Always use an absolute path for the skybox directory
        self.config_path = os.path.join(BASE_DIR, "user_config.json")
        self.skybox_dir = os.path.abspath(os.path.join(BASE_DIR, "src", "skybox"))
        self.roblox_shortcut = ""
        local_app_data = os.getenv("LOCALAPPDATA")
        self.skybox_preview_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Previews")
        os.makedirs(self.skybox_preview_dir, exist_ok=True)
        self.available_skyboxes = self.fetch_skybox_list()
        self.ensure_previews_zip()
        self.load_config()

        # --- Main rounded background frame ---
        main_bg = QFrame(self)
        main_bg.setObjectName("MainBg")
        main_bg_layout = QVBoxLayout(main_bg)
        main_bg_layout.setContentsMargins(0, 0, 0, 0)

        # --- Outer layout for all content ---
        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(40, 40, 40, 40)
        self.outer_layout.setSpacing(0)
        main_bg_layout.addLayout(self.outer_layout)

        # --- Set only one layout on MainWindow ---
        super_layout = QVBoxLayout(self)
        super_layout.setContentsMargins(0, 0, 0, 0)
        super_layout.addWidget(main_bg)

        self.init_ui()

    # --- Make window draggable ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def fetch_skybox_list(self):
        try:
            resp = requests.get(SkysList)
            resp.raise_for_status()
            return [line.strip() for line in resp.text.splitlines() if line.strip()]
        except Exception as e:
            print(f"Failed to fetch skybox list: {e}")
            return []

    def ensure_previews_zip(self):
        # Only download/extract if not already extracted
        marker = os.path.join(self.skybox_preview_dir, ".unzipped")
        if not os.path.exists(marker):
            import tempfile
            import requests
            zip_path = os.path.join(tempfile.gettempdir(), "SkyboxPNGs.zip")
            try:
                # Download the zip
                resp = requests.get(SkyboxPNGsZIP)
                resp.raise_for_status()
                with open(zip_path, "wb") as f:
                    f.write(resp.content)
                # Extract to preview dir
                unzip_file(zip_path, self.skybox_preview_dir)
                # Mark as unzipped
                with open(marker, "w") as f:
                    f.write("done")
            except Exception as e:
                print(f"Failed to download/extract SkyboxPNGs.zip: {e}")

    def download_all_previews(self):
        # No longer needed, previews are extracted from the zip
        pass

    def get_skybox_names(self):
        return self.available_skyboxes

    def init_ui(self):
        outer_layout = self.outer_layout

        # Top bar with title and close, no border
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        title = QLabel("CDBL")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        version = QLabel("Version 1")
        version.setFont(QFont("Segoe UI", 9))
        version.setStyleSheet("color: #aaa; margin-right: 12px; border: 1px solid #222; border-radius: 12px; padding: 2px 12px;")
        top_bar.addWidget(version)

        min_btn = QPushButton("–")
        min_btn.setFixedSize(24, 24)
        min_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaa;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                color: #b8f582;
            }
        """)
        min_btn.clicked.connect(self.showMinimized)
        top_bar.addWidget(min_btn)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaa;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #f55;
            }
        """)
        close_btn.clicked.connect(self.close)
        top_bar.addWidget(close_btn)
        outer_layout.addLayout(top_bar)

        # --- Status label for updates ---
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.status_label.setStyleSheet("color: #b8f582; margin-bottom: 6px;")
        outer_layout.addWidget(self.status_label)

        # Add vertical space between top bar and tabs
        outer_layout.addSpacing(18)

        # Tab bar with no border
        tab_bar = QTabBar()
        tab_bar.addTab("Roblox")
        tab_bar.addTab("Skyboxes")
        tab_bar.addTab("Textures")
        tab_bar.addTab("Settings")
        tab_bar.setStyleSheet("""
            QTabBar {
                background: transparent;
            }
            QTabBar::tab {
                background: #232428;
                color: #b8f582;
                border-radius: 8px 8px 0 0;
                padding: 8px 24px;
                font: bold 12pt "Segoe UI";
                margin-right: 2px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #18191c;
                color: #fff;
            }
            QTabBar::tab:!selected {
                background: #232428;
                color: #b8f582;
            }
        """)
        outer_layout.addWidget(tab_bar)

        # Add vertical space below tabs
        outer_layout.addSpacing(12)

        # Stacked widget for tab content
        self.stacked = QStackedWidget()
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Roblox Tab
        roblox_page = QWidget()
        roblox_layout = QVBoxLayout(roblox_page)
        roblox_layout.setAlignment(Qt.AlignTop)
        roblox_label = QLabel("Roblox Launcher")
        roblox_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        roblox_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        roblox_layout.addWidget(roblox_label)

        # --- Roblox Buttons ---
        launch_btn = QPushButton("[✔️]  Launch Roblox")
        launch_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        launch_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d3a22;
                color: #c6ff8e;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #3e4d2c;
                color: #fff;
            }
        """)
        launch_btn.clicked.connect(self.launch_roblox)
        roblox_layout.addWidget(launch_btn)

        kill_btn = QPushButton("[❌]  Kill Roblox")
        kill_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        kill_btn.setStyleSheet("""
            QPushButton {
                background-color: #3a2323;
                color: #ff8e8e;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #5a2a2a;
                color: #fff;
            }
        """)
        kill_btn.clicked.connect(self.kill_roblox)
        roblox_layout.addWidget(kill_btn)
        # --- End Kill Roblox Button ---

        # Roblox Shortcut Path
        shortcut_layout = QHBoxLayout()
        shortcut_layout.setContentsMargins(0, 0, 0, 0)
        shortcut_layout.setAlignment(Qt.AlignVCenter)

        self.shortcut_edit = QLineEdit(self.roblox_shortcut)
        self.shortcut_edit.setPlaceholderText("Path to Roblox shortcut (.lnk or .exe)")
        self.shortcut_edit.setFixedHeight(32)
        self.shortcut_edit.setStyleSheet("""
            QLineEdit {
                background: #232428;
                color: #fff;
                border-radius: 8px;
                padding: 6px 12px;
                font: 10pt "Segoe UI";
                border: 1px solid #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #b8f582;
            }
        """)

        browse_btn = QPushButton("Browse")
        browse_btn.setFixedHeight(32)
        browse_btn.setFixedWidth(90)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #232428;
                color: #b8f582;
                border-radius: 8px;
                padding: 6px 18px;
                font: bold 10pt "Segoe UI";
                border: 1px solid #333;
                margin-left: 8px;
            }
            QPushButton:hover {
                background-color: #2d325a;
                color: #fff;
                border: 1.5px solid #b8f582;
            }
        """)
        browse_btn.clicked.connect(self.browse_shortcut)

        shortcut_layout.addWidget(self.shortcut_edit)
        shortcut_layout.addWidget(browse_btn)
        roblox_layout.addLayout(shortcut_layout)

        # Add stretch to push the install button to the bottom
        roblox_layout.addStretch()

        # --- Install Roblox Button ---
        install_btn = QPushButton("[⬇️]  Install Roblox")
        install_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        install_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        install_btn.clicked.connect(self.install_roblox)
        roblox_layout.addWidget(install_btn)

        self.stacked.addWidget(roblox_page)

        # Skyboxes UI
        skybox_page = QWidget()
        skybox_layout = QHBoxLayout(skybox_page)
        skybox_layout.setContentsMargins(0, 0, 0, 0)
        skybox_layout.setSpacing(18)

        # Left: List of skyboxes
        left_side = QVBoxLayout()
        left_side.setAlignment(Qt.AlignTop)
        skybox_label = QLabel("Skybox Management")
        skybox_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        skybox_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        left_side.addWidget(skybox_label)

        # --- Add Skybox Search Bar ---
        self.skybox_search = QLineEdit()
        self.skybox_search.setPlaceholderText("Search Skyboxes...")
        self.skybox_search.setStyleSheet("""
            QLineEdit {
                background: #232428;
                color: #fff;
                border-radius: 8px;
                padding: 6px 12px;
                font: 11pt "Segoe UI";
                margin-bottom: 8px;
                border: 1px solid #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #b8f582;
            }
        """)
        left_side.addWidget(self.skybox_search)

        # --- Skybox List ---
        self.skybox_list = QListWidget()
        self.skybox_list.addItems(self.get_skybox_names())
        self.skybox_list.setStyleSheet("""
            QListWidget {
                background: #232428;
                color: #fff;
                border-radius: 8px;
                font: 11pt "Segoe UI";
                padding: 8px;
            }
            QListWidget::item:selected {
                background: #b8f582;
                color: #18191c;
                border-radius: 6px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 16px;
                margin: 4px 2px 4px 0;
                border-radius: 8px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #a8ffce, stop:1 #fbed96
                );
                min-height: 36px;
                border-radius: 8px;
                border: 2px solid #232428;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #b8f582, stop:1 #8edcff
                );
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.skybox_list.currentTextChanged.connect(self.update_skybox_preview)
        left_side.addWidget(self.skybox_list)

        # --- Skybox Search Filtering ---
        def filter_skyboxes():
            filter_text = self.skybox_search.text().lower()
            self.skybox_list.clear()
            for name in self.get_skybox_names():
                if filter_text in name.lower():
                    self.skybox_list.addItem(name)
            if self.skybox_list.count() > 0:
                self.skybox_list.setCurrentRow(0)
                self.update_skybox_preview(self.skybox_list.currentItem().text())
            else:
                self.skybox_preview.setText("No Preview")
        self.skybox_search.textChanged.connect(filter_skyboxes)

        # --- Add Apply and Restore Skybox Buttons ---
        button_width = 320  # Set to 320 for a more compact look, or keep 420 if you prefer wider

        # --- Left Side Buttons ---
        apply_skybox_btn = QPushButton("[✔️]  Apply Skybox")
        apply_skybox_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        apply_skybox_btn.setFixedHeight(54)
        apply_skybox_btn.setFixedWidth(button_width)
        apply_skybox_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        apply_skybox_btn.clicked.connect(self.apply_skybox)
        left_side.addSpacing(12)
        left_side.addWidget(apply_skybox_btn)

        restore_skybox_btn = QPushButton("[❌]  Restore Skybox")
        restore_skybox_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        restore_skybox_btn.setFixedHeight(54)
        restore_skybox_btn.setFixedWidth(button_width)
        restore_skybox_btn.setStyleSheet("""
            QPushButton {
                background-color: #223a2d;
                color: #8effc6;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c5a42;
                color: #fff;
            }
        """)
        restore_skybox_btn.clicked.connect(self.restore_skybox)
        left_side.addSpacing(12)
        left_side.addWidget(restore_skybox_btn)

        # Right: Preview and custom sky buttons
        right_side = QVBoxLayout()
        right_side.setAlignment(Qt.AlignTop)

        # Add preview label and preview widget to right_side first
        preview_label = QLabel("Preview")
        preview_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        preview_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        right_side.addWidget(preview_label)

        self.skybox_preview = QLabel()
        self.skybox_preview.setFixedSize(420, 260)
        self.skybox_preview.setStyleSheet("""
            QLabel {
                background: #232428;
                border-radius: 8px;
                border: 1px solid #333;
            }
        """)
        self.skybox_preview.setAlignment(Qt.AlignCenter)
        self.skybox_preview.setText("No Preview")
        right_side.addWidget(self.skybox_preview)

        # --- Right Side Buttons (now under the preview) ---
        right_side.addSpacing(18)

        custom_sky_btn = QPushButton("[📂]  Use Custom Sky Folder")
        custom_sky_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        custom_sky_btn.setFixedHeight(54)
        custom_sky_btn.setFixedWidth(button_width)
        custom_sky_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        custom_sky_btn.clicked.connect(self.use_custom_sky_folder)
        right_side.addWidget(custom_sky_btn)

        self.apply_custom_sky_btn = QPushButton("[✔️]  Apply Custom Skybox")
        self.apply_custom_sky_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.apply_custom_sky_btn.setFixedHeight(54)
        self.apply_custom_sky_btn.setFixedWidth(button_width)
        self.apply_custom_sky_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #888;
            }
            QPushButton:hover:!disabled {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        self.apply_custom_sky_btn.setEnabled(False)
        self.apply_custom_sky_btn.clicked.connect(self.apply_custom_skybox)
        right_side.addSpacing(12)
        right_side.addWidget(self.apply_custom_sky_btn)

        # Add both sides to the horizontal layout
        skybox_layout.addLayout(left_side, 2)
        skybox_layout.addLayout(right_side, 3)
        self.stacked.addWidget(skybox_page)

        # Textures UI
        textures_page = QWidget()
        textures_layout = QVBoxLayout(textures_page)
        textures_layout.setAlignment(Qt.AlignTop)
        textures_label = QLabel("Texture Management")
        textures_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        textures_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        textures_layout.addWidget(textures_label)

        # --- Dark Textures Buttons ---
        dark_btn_row = QHBoxLayout()
        dark_btn_row.setContentsMargins(0, 0, 0, 0)
        dark_btn_row.setAlignment(Qt.AlignVCenter)

        apply_dark_btn = QPushButton("[✔️]  Apply Dark Textures")
        apply_dark_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        apply_dark_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        apply_dark_btn.clicked.connect(self.apply_dark_textures)

        restore_dark_btn = QPushButton("[❌]  Restore Default Textures")
        restore_dark_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        restore_dark_btn.setStyleSheet("""
            QPushButton {
                background-color: #223a2d;
                color: #8effc6;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c5a42;
                color: #fff;
            }
        """)
        restore_dark_btn.clicked.connect(self.restore_dark_textures)

        dark_btn_row.addWidget(apply_dark_btn)
        dark_btn_row.addWidget(restore_dark_btn)
        textures_layout.addLayout(dark_btn_row)
        # --- End Dark Textures Buttons ---

        restore_btn = QPushButton("[❌]  Full Restore")
        restore_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #223a2d;
                color: #8effc6;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2c5a42;
                color: #fff;
            }
        """)
        restore_btn.clicked.connect(self.full_restore)
        textures_layout.addWidget(restore_btn)
        textures_layout.addStretch()
        self.stacked.addWidget(textures_page)

        # --- Settings UI ---
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setAlignment(Qt.AlignTop)
        settings_label = QLabel("Settings")
        settings_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        settings_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        settings_layout.addWidget(settings_label)

        # Warning label for settings
        warning_label = QLabel("⚠️ Settings only work on regular Roblox (not Bloxstrap/Fishstrap)!")
        warning_label.setStyleSheet("color: #ffb347; font-weight: bold; margin-bottom: 12px;")
        settings_layout.addWidget(warning_label)

        # Use a form layout for better alignment
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        form_layout.setHorizontalSpacing(18)
        form_layout.setVerticalSpacing(12)

        edit_style = """
            QLineEdit {
                background: #232428;
                color: #fff;
                border-radius: 8px;
                padding: 6px 12px;
                font: 10pt "Segoe UI";
                border: 1px solid #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #b8f582;
            }
        """

        self.sensitivity_edit = QLineEdit()
        self.sensitivity_edit.setPlaceholderText("e.g. 0.5")
        self.sensitivity_edit.setFixedHeight(32)
        self.sensitivity_edit.setMinimumWidth(120)
        self.sensitivity_edit.setStyleSheet(edit_style)
        form_layout.addRow("Sensitivity:", self.sensitivity_edit)

        self.fpscap_edit = QLineEdit()
        self.fpscap_edit.setPlaceholderText("e.g. 144 or inf")
        self.fpscap_edit.setFixedHeight(32)
        self.fpscap_edit.setMinimumWidth(120)
        self.fpscap_edit.setStyleSheet(edit_style)
        form_layout.addRow("FPS Cap:", self.fpscap_edit)

        self.graphics_edit = QLineEdit()
        self.graphics_edit.setPlaceholderText("1-20")
        self.graphics_edit.setFixedHeight(32)
        self.graphics_edit.setMinimumWidth(120)
        self.graphics_edit.setStyleSheet(edit_style)
        form_layout.addRow("Graphics:", self.graphics_edit)

        self.volume_edit = QLineEdit()
        self.volume_edit.setPlaceholderText("1-10")
        self.volume_edit.setFixedHeight(32)
        self.volume_edit.setMinimumWidth(120)
        self.volume_edit.setStyleSheet(edit_style)
        form_layout.addRow("Volume:", self.volume_edit)

        settings_layout.addLayout(form_layout)

        # Apply Button
        apply_btn = QPushButton("[✔️]  Apply Settings")
        apply_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #23283a;
                color: #b8c6ff;
                border-radius: 16px;
                padding: 8px 28px 8px 28px;
                min-height: 38px;
                font-size: 15px;
                text-align: left;
                font-weight: bold;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background-color: #2d325a;
                color: #fff;
            }
        """)
        apply_btn.clicked.connect(self.apply_settings)
        settings_layout.addWidget(apply_btn)
        settings_layout.addStretch()
        self.stacked.addWidget(settings_page)

        outer_layout.addWidget(self.stacked)

        # Connect tab changes to stacked widget
        tab_bar.currentChanged.connect(self.stacked.setCurrentIndex)

        # Set initial preview if any skybox is selected
        if self.skybox_list.count() > 0:
            self.skybox_list.setCurrentRow(0)
            self.update_skybox_preview(self.skybox_list.currentItem().text())

    def launch_roblox(self):
        shortcut = self.shortcut_edit.text().strip()
        if not shortcut or not os.path.exists(shortcut):
            QMessageBox.warning(self, "Launch", "Please set a valid Roblox shortcut path.")
            return
        self.save_config()
        try:
            subprocess.Popen(['cmd', '/c', 'start', '', shortcut], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Launch", f"Failed to launch Roblox:\n{e}")

    def configure_settings(self):
        QMessageBox.information(self, "Settings", "This would open the settings dialog.")

    def apply_dark_textures(self):
        self.status_label.setText("Downloading dark textures...")
        self._worker_dark = DownloadWorker(DarkTextures)
        def on_finished(zip_path, error):
            if error:
                self.status_label.setText("Failed to apply dark textures.")
                QMessageBox.critical(self, "Dark Textures", f"Failed to apply dark textures:\n{error}")
                self._worker_dark = None
                return
            try:
                install_dark_textures()
                delete_all_downloads()
                self.status_label.setText("Dark textures applied! Restart Roblox to see the changes.")
                QMessageBox.information(self, "Dark Textures", "Dark textures applied successfully.\nRestart Roblox to see the changes.")
            except Exception as e:
                self.status_label.setText("Failed to apply dark textures.")
                QMessageBox.critical(self, "Dark Textures", f"Failed to apply dark textures:\n{e}")
            self._worker_dark = None
        self._worker_dark.finished.connect(on_finished)
        self._worker_dark.start()

    def restore_skybox(self):
        self.status_label.setText("Restoring default skybox...")
        self._worker_restore_skybox = DownloadWorker(DefaultSky)
        def on_finished(zip_path, error):
            if error:
                self.status_label.setText("Failed to restore skybox.")
                QMessageBox.critical(self, "Restore Skybox", f"Failed to restore skybox:\n{error}")
                self._worker_restore_skybox = None
                return
            try:
                restore_skybox()
                delete_all_downloads()
                self.status_label.setText("Default skybox restored! Restart Roblox to see the changes.")
                QMessageBox.information(self, "Restore Skybox", "Default skybox restored.\nRestart Roblox to see the changes.")
            except Exception as e:
                self.status_label.setText("Failed to restore skybox.")
                QMessageBox.critical(self, "Restore Skybox", f"Failed to restore skybox:\n{e}")
            self._worker_restore_skybox = None
        self._worker_restore_skybox.finished.connect(on_finished)
        self._worker_restore_skybox.start()

    def restore_dark_textures(self):
        self.status_label.setText("Restoring default textures...")
        self._worker_restore_dark = DownloadWorker(LightTextures)
        def on_finished(zip_path, error):
            if error:
                self.status_label.setText("Failed to restore dark textures.")
                QMessageBox.critical(self, "Restore Dark Textures", f"Failed to restore dark textures:\n{error}")
                self._worker_restore_dark = None
                return
            try:
                restore_dark_textures()
                delete_all_downloads()
                self.status_label.setText("Default textures restored! Restart Roblox to see the changes.")
                QMessageBox.information(self, "Restore Dark Textures", "Dark textures restored to default.\nRestart Roblox to see the changes.")
            except Exception as e:
                self.status_label.setText("Failed to restore dark textures.")
                QMessageBox.critical(self, "Restore Dark Textures", f"Failed to restore dark textures:\n{e}")
            self._worker_restore_dark = None
        self._worker_restore_dark.finished.connect(on_finished)
        self._worker_restore_dark.start()

    def full_restore(self):
        self.status_label.setText("Restoring all textures...")
        self._worker_full_restore = DownloadWorker(DefaultTextures)
        def on_finished(zip_path, error):
            if error:
                self.status_label.setText("Failed to restore all textures.")
                QMessageBox.critical(self, "Full Restore", f"Failed to restore textures:\n{error}")
                self._worker_full_restore = None
                return
            try:
                full_restore()
                delete_all_downloads()
                self.status_label.setText("All textures restored! Restart Roblox to see the changes.")
                QMessageBox.information(self, "Full Restore", "All textures restored to default.\nRestart Roblox to see the changes.")
            except Exception as e:
                self.status_label.setText("Failed to restore all textures.")
                QMessageBox.critical(self, "Full Restore", f"Failed to restore textures:\n{e}")
            self._worker_full_restore = None
        self._worker_full_restore.finished.connect(on_finished)
        self._worker_full_restore.start()

    def kill_roblox(self):
        try:
            subprocess.run(
                ["taskkill", "/f", "/im", "RobloxPlayerBeta.exe"],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, "Kill Roblox", "No Roblox processes found or could not terminate.")

    def install_roblox(self):
        import shutil
        url = "https://www.roblox.com/download/client?os=win"
        temp_dir = tempfile.gettempdir()
        save_path = os.path.join(temp_dir, "RobloxPlayerInstaller.exe")
        try:
            if os.path.exists(save_path):
                os.remove(save_path)
            urllib.request.urlretrieve(url, save_path)
            QMessageBox.information(self, "Download", f"Roblox installer downloaded to:\n{save_path}\n\nThe installer will now run.")
            subprocess.Popen([save_path], shell=True)
        except Exception as e:
            QMessageBox.critical(self, "Download", f"Failed to download or run Roblox installer:\n{e}")

    def apply_skybox(self):
        import shutil
        selected = self.skybox_list.currentItem()
        if not selected:
            self.status_label.setText("No skybox selected.")
            QMessageBox.warning(self, "Apply Skybox", "No skybox selected.")
            return
        skybox_name = selected.text()
        zip_url = f"https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxZIPs/{skybox_name}.zip"
        local_zip = os.path.join(tempfile.gettempdir(), f"{skybox_name}.zip")
        local_app_data = os.getenv("LOCALAPPDATA")
        extract_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Skyboxes", skybox_name)
        os.makedirs(extract_dir, exist_ok=True)
        # Download ZIP if not already extracted
        if not os.listdir(extract_dir):
            try:
                self.status_label.setText(f"Downloading skybox '{skybox_name}'...")
                QApplication.processEvents()
                resp = requests.get(zip_url)
                resp.raise_for_status()
                with open(local_zip, "wb") as f:
                    f.write(resp.content)
                self.status_label.setText(f"Extracting skybox '{skybox_name}'...")
                QApplication.processEvents()
                unzip_file(local_zip, extract_dir)
                # --- Flatten any nested folders ---
                for root, dirs, files in os.walk(extract_dir):
                    if root == extract_dir:
                        continue
                    for f in files:
                        src = os.path.join(root, f)
                        dst = os.path.join(extract_dir, f)
                        if not os.path.exists(dst):
                            shutil.move(src, dst)
                # Remove empty subfolders
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    if os.path.isdir(dir_path) and not os.listdir(dir_path):
                        os.rmdir(dir_path)
            except Exception as e:
                self.status_label.setText("Failed to download/extract skybox.")
                QMessageBox.critical(self, "Apply Skybox", f"Failed to download/extract skybox:\n{e}")
                return
        # Now apply as before
        try:
            self.status_label.setText(f"Applying skybox '{skybox_name}'...")
            QApplication.processEvents()
            install_skybox(extract_dir)
            self.status_label.setText(f"Skybox '{skybox_name}' installed! Restart Roblox to see the changes.")
            QMessageBox.information(self, "Apply Skybox", f"Skybox '{skybox_name}' installed successfully.\nRestart Roblox to see the changes.")
        except Exception as e:
            self.status_label.setText("Failed to apply skybox.")
            QMessageBox.critical(self, "Apply Skybox", f"Failed to install skybox:\n{e}")

    def apply_custom_skybox(self):
        if not self.last_custom_sky_folder or not os.path.isdir(self.last_custom_sky_folder):
            self.status_label.setText("No custom sky folder selected.")
            QMessageBox.warning(self, "Apply Custom Skybox", "No custom sky folder selected.")
            return
        self.status_label.setText("Applying custom skybox...")
        try:
            install_skybox(self.last_custom_sky_folder)
            delete_all_downloads()
            self.status_label.setText("Custom skybox applied! Restart Roblox to see the changes.")
            QMessageBox.information(self, "Apply Custom Skybox", "Custom skybox applied successfully.\nRestart Roblox to see the changes.")
        except Exception as e:
            self.status_label.setText("Failed to apply custom skybox.")
            QMessageBox.critical(self, "Apply Custom Skybox", f"Failed to apply custom skybox:\n{e}")
        self.update_skybox_preview(self.last_custom_sky_folder)

    def update_skybox_preview(self, skybox_name):
        preview_path = os.path.join(self.skybox_preview_dir, f"{skybox_name}.png")
        if os.path.exists(preview_path):
            pixmap = QPixmap(preview_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(self.skybox_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.skybox_preview.setPixmap(pixmap)
                return
        self.skybox_preview.setText("No Preview")

    def browse_shortcut(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Roblox Shortcut", "", "Shortcuts (*.lnk);;Executables (*.exe);;All Files (*)")
        if path:
            self.shortcut_edit.setText(path)
            self.roblox_shortcut = path
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, "w") as f:
                json.dump({"roblox_shortcut": self.shortcut_edit.text()}, f)
        except Exception as e:
            print(f"[ERROR] Could not save config: {e}")

    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    self.roblox_shortcut = data.get("roblox_shortcut", "")
            else:
                self.roblox_shortcut = ""
        except Exception as e:
            print(f"[ERROR] Could not load config: {e}")
            self.roblox_shortcut = ""

    def apply_settings(self):
        import shutil

        sens = self.sensitivity_edit.text().strip()
        fps = self.fpscap_edit.text().strip()
        gfx = self.graphics_edit.text().strip()
        vol = self.volume_edit.text().strip()

        roblox_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox")
        src = os.path.join(roblox_dir, "GlobalBasicSettings_13.xml")
        default_settings = os.path.join(BASE_DIR, "func", "GlobalBasicSettings_13.xml")
        temp_settings = os.path.join(BASE_DIR, "func", "GlobalBasicSettings_13_edit.xml")

        # If Roblox settings file doesn't exist, clone from default
        if not os.path.exists(src):
            if os.path.exists(default_settings):
                shutil.copy2(default_settings, src)
            else:
                QMessageBox.critical(self, "Settings", f"Could not find:\n{src}\n\nAnd no default settings found at:\n{default_settings}")
                return

        # Always work on a temp copy
        try:
            shutil.copy2(src, temp_settings)
        except Exception as e:
            QMessageBox.critical(self, "Settings", f"Failed to copy settings file:\n{e}")
            return

        script_path = os.path.join(BASE_DIR, "func", "ChangeSettings.ps1")
        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Settings", f"Script not found:\n{script_path}")
            return

        args = []
        if sens: args += ["-Sensitivity", sens]
        if fps:  args += ["-FPSCap", fps]
        if gfx:  args += ["-Graphics", gfx]
        if vol:  args += ["-Volume", vol]

        if not args:
            QMessageBox.warning(self, "Settings", "Please enter at least one value.")
            self.sensitivity_edit.setFocus()
            return

        try:
            completed = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, temp_settings] + args,
                capture_output=True, text=True, shell=True
            )
            # --- Replace the original XML if script succeeded ---
            if completed.returncode == 0:
                try:
                    backup_path = src + ".bak"
                    if os.path.exists(src):
                        shutil.copy2(src, backup_path)
                        os.remove(src)
                    shutil.move(temp_settings, src)
                except Exception as e:
                    QMessageBox.warning(self, "Settings", f"Settings applied, but failed to move back to Roblox folder:\n{e}")
                QMessageBox.information(self, "Settings", "Settings applied!\n\n" + completed.stdout)
                # Clear fields for user clarity
                self.sensitivity_edit.clear()
                self.fpscap_edit.clear()
                self.graphics_edit.clear()
                self.volume_edit.clear()
                self.sensitivity_edit.setFocus()
            else:
                QMessageBox.critical(self, "Settings", "Failed to apply settings:\n\n" + completed.stderr)
        except Exception as e:
            QMessageBox.critical(self, "Settings", f"Error running script:\n{e}")

    def get_and_extract_resource(self, url):
        try:
            zip_path = download_file(url, None)
            if zip_path and zip_path.endswith(".zip"):
                unzip_file(zip_path)
                QMessageBox.information(self, "Resource", f"Downloaded and extracted:\n{zip_path}")
            else:
                QMessageBox.warning(self, "Resource", "Failed to download or not a zip file.")
        except Exception as e:
            QMessageBox.critical(self, "Resource", f"Error: {e}")

    def use_custom_sky_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Custom Sky Folder", "")
        if folder:
            self.last_custom_sky_folder = folder
            self.update_skybox_preview(folder)  # Only update preview
            self.apply_custom_sky_btn.setEnabled(True)
        else:
            self.apply_custom_sky_btn.setEnabled(False)

    def toggle_dark_textures(self, state):
        if state == Qt.Checked or state == 2:
            try:
                install_dark_textures()
                QMessageBox.information(self, "Dark Textures", "Dark textures applied!\nRestart Roblox to see the changes.")
            except Exception as e:
                QMessageBox.critical(self, "Dark Textures", f"Failed to apply dark textures:\n{e}")
                self.dark_toggle.setChecked(False)
        else:
            try:
                restore_dark_textures()
                QMessageBox.information(self, "Restore Dark Textures", "Default textures restored!\nRestart Roblox to see the changes.")
            except Exception as e:
                QMessageBox.critical(self, "Restore Dark Textures", f"Failed to restore textures:\n{e}")
                self.dark_toggle.setChecked(True)
                
                
class DownloadWorker(QThread):
    finished = Signal(str, str)  # zip_path, error

    def __init__(self, url, extract_subfolder=None):
        super().__init__()
        self.url = url
        self.extract_subfolder = extract_subfolder

    def run(self):
        import shutil
        try:
            zip_path = download_file(self.url, None)
            if zip_path and zip_path.endswith(".zip"):
                extract_to = None
                if self.extract_subfolder:
                    local_app_data = os.getenv("LOCALAPPDATA")
                    extract_to = os.path.join(local_app_data, "CustomBloxLauncher", "Downloads", self.extract_subfolder)
                unzip_file(zip_path, extract_to)
                # --- Move all files from any subfolders up to extract_to ---
                if extract_to:
                    for root, dirs, files in os.walk(extract_to):
                        if root == extract_to:
                            continue  # skip the root itself
                        for f in files:
                            src = os.path.join(root, f)
                            dst = os.path.join(extract_to, f)
                            try:
                                shutil.move(src, dst)
                            except Exception:
                                pass
                    # Remove empty subfolders
                    for root, dirs, files in os.walk(extract_to, topdown=False):
                        if root != extract_to and not os.listdir(root):
                            os.rmdir(root)
                self.finished.emit(zip_path, "")
            else:
                self.finished.emit("", "Failed to download or extract zip.")
        except Exception as e:
            self.finished.emit("", str(e))
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())