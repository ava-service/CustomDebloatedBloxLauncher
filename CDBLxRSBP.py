import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QMessageBox, QTabBar, QStackedWidget, QSizePolicy, QFrame, QListWidget,
    QLineEdit, QFileDialog, QFormLayout, QCheckBox, QRadioButton, QButtonGroup
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
import webbrowser
import winreg
import glob
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import math
from io import BytesIO

# Version information
# Update this for each release
APP_VERSION = "V1-2 x 8.9.25 Bday beta"  # Update this for each release

# URLs for downloading resources
DarkTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DarkTextures.zip"
LightTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/LightTextures.zip"
DefaultTextures = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DefaultTextures.zip"
DefaultSky = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DefaultSky.zip"
SkyboxPatch = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxPatch.zip"

OgOof = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/og-oof.ogg"
DefaultOOF = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/DefaultOOF.ogg"

# SkyBox data and download URLs
SkyName = ""
SkyboxZIPs = f"https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxZIPs/{SkyName}.zip"
SkyboxPNGsZIP = "https://github.com/eman225511/CustomDebloatedBloxLauncher/raw/refs/heads/main/src/SkyboxPNGs/SkyboxPNGs.zip"
SkysList = "https://raw.githubusercontent.com/eman225511/CustomDebloatedBloxLauncher/refs/heads/main/src/SkyboxZIPs/sky-list.txt"

GITHUB_RELEASES_API = "https://api.github.com/repos/eman225511/CustomDebloatedBloxLauncher/releases/latest"

def check_for_update():
    try:
        resp = requests.get(GITHUB_RELEASES_API, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        latest = data.get("tag_name", "").lstrip("v")
        html_url = data.get("html_url", "https://github.com/eman225511/CustomDebloatedBloxLauncher/releases/latest")
        if latest and latest != APP_VERSION:
            QMessageBox.information(
                None,
                "Update Available",
                f"A new version ({latest}) is available!\n"
                "The latest release page will now open in your browser."
            )
            webbrowser.open(html_url)
    except Exception as e:
        print(f"[WARN] Could not check for updates: {e}")

print("[DEBUG] Starting CDBL...")
print("[DEBUG] Downloading required files...")

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_all_versions_paths():
    """Enhanced Roblox detection that checks multiple sources"""
    paths = []
    localappdata = os.environ.get('LOCALAPPDATA')
    
    # Standard paths
    standard_paths = [
        os.path.join(localappdata, 'Roblox', 'Versions'),
        os.path.join(localappdata, 'Bloxstrap', 'Versions'),
        os.path.join(localappdata, 'Fishstrap', 'Versions'),
    ]
    
    # Add existing standard paths
    for path in standard_paths:
        if os.path.exists(path):
            try:
                # Test if we can actually read the directory
                os.listdir(path)
                paths.append(path)
                print(f"[DEBUG] Added standard path: {path}")
            except (PermissionError, OSError) as e:
                print(f"[DEBUG] Cannot access {path}: {e}")
    
    # Check Windows Registry for Roblox installation
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox Corporation\Environments\roblox-player") as key:
            install_path = winreg.QueryValueEx(key, "")[0]
            versions_path = os.path.join(os.path.dirname(install_path), 'Versions')
            if os.path.exists(versions_path) and versions_path not in paths:
                try:
                    os.listdir(versions_path)
                    paths.append(versions_path)
                    print(f"[DEBUG] Found Roblox via registry: {versions_path}")
                except (PermissionError, OSError) as e:
                    print(f"[DEBUG] Cannot access registry path {versions_path}: {e}")
    except (WindowsError, FileNotFoundError):
        print("[DEBUG] Roblox not found in registry")
    
    # Check common alternative installation locations with timeout protection
    alternative_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Roblox', 'Versions'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Roblox', 'Versions'),
        os.path.join(os.environ.get('APPDATA', ''), 'Roblox', 'Versions'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Roblox', 'Versions'),
    ]
    
    for alt_path in alternative_paths:
        if not alt_path:
            continue
        print(f"[DEBUG] Checking alternative path: {alt_path}")
        try:
            if os.path.exists(alt_path) and alt_path not in paths:
                # Test directory access
                test_list = os.listdir(alt_path)
                paths.append(alt_path)
                print(f"[DEBUG] Found alternative Roblox installation: {alt_path} ({len(test_list)} items)")
        except (PermissionError, OSError) as e:
            print(f"[DEBUG] Cannot access alternative path {alt_path}: {e}")
        except Exception as e:
            print(f"[DEBUG] Unexpected error with {alt_path}: {e}")
    
    # Search for RobloxPlayerBeta.exe in common locations with limits
    search_locations = [
        (os.environ.get('LOCALAPPDATA', ''), 3),
        (os.environ.get('PROGRAMFILES', ''), 2),
        (os.environ.get('PROGRAMFILES(X86)', ''), 2),
        (os.environ.get('APPDATA', ''), 3),
    ]
    
    for location, max_depth in search_locations:
        if not location:
            continue
        print(f"[DEBUG] Searching for RobloxPlayerBeta.exe in: {location}")
        try:
            found_exes = []
            for root, dirs, files in os.walk(location):
                depth = root[len(location):].count(os.sep)
                if depth >= max_depth:
                    dirs[:] = []
                    continue
                
                if 'RobloxPlayerBeta.exe' in files:
                    exe_path = os.path.join(root, 'RobloxPlayerBeta.exe')
                    found_exes.append(exe_path)
                    
                    exe_dir = os.path.dirname(exe_path)
                    versions_dir = os.path.dirname(exe_dir)
                    if os.path.basename(versions_dir) == 'Versions' and versions_dir not in paths:
                        try:
                            os.listdir(versions_dir)
                            paths.append(versions_dir)
                            print(f"[DEBUG] Found Roblox via exe search: {versions_dir}")
                        except (PermissionError, OSError):
                            print(f"[DEBUG] Cannot access found versions dir: {versions_dir}")
                
                if len(found_exes) >= 5:
                    break
                    
        except Exception as e:
            print(f"[DEBUG] Error searching in {location}: {e}")
    
    print(f"[DEBUG] Total Roblox installations found: {len(paths)}")
    for i, path in enumerate(paths, 1):
        try:
            version_count = len([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
            print(f"[DEBUG] {i}. {path} ({version_count} versions)")
        except Exception as e:
            print(f"[DEBUG] {i}. {path} (cannot count versions: {e})")
    
    return paths

def get_all_roblox_paths():
    """Enhanced function to get all Roblox installation root directories"""
    paths = []
    localappdata = os.environ.get('LOCALAPPDATA')
    
    standard_paths = [
        os.path.join(localappdata, 'Roblox'),
        os.path.join(localappdata, 'Bloxstrap'),
        os.path.join(localappdata, 'Fishstrap'),
    ]
    
    paths.extend([p for p in standard_paths if os.path.exists(p)])
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox Corporation\Environments\roblox-player") as key:
            install_path = winreg.QueryValueEx(key, "")[0]
            roblox_root = os.path.dirname(os.path.dirname(install_path))
            if os.path.exists(roblox_root) and roblox_root not in paths:
                paths.append(roblox_root)
    except (WindowsError, FileNotFoundError):
        pass
    
    return paths

def find_roblox_executable():
    """Find the main Roblox executable for launching"""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox Corporation\Environments\roblox-player") as key:
            exe_path = winreg.QueryValueEx(key, "")[0]
            if os.path.exists(exe_path):
                return exe_path
    except (WindowsError, FileNotFoundError):
        pass
    
    for versions_path in get_all_versions_paths():
        for version_dir in os.listdir(versions_path):
            exe_path = os.path.join(versions_path, version_dir, 'RobloxPlayerBeta.exe')
            if os.path.exists(exe_path):
                return exe_path
    
    return None

def diagnose_roblox_installation():
    """Diagnostic function to help troubleshoot Roblox detection"""
    print("\n=== ROBLOX INSTALLATION DIAGNOSIS ===")
    
    print(f"LOCALAPPDATA: {os.environ.get('LOCALAPPDATA')}")
    print(f"PROGRAMFILES: {os.environ.get('PROGRAMFILES')}")
    print(f"PROGRAMFILES(X86): {os.environ.get('PROGRAMFILES(X86)')}")
    
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox Corporation\Environments\roblox-player") as key:
            install_path = winreg.QueryValueEx(key, "")[0]
            print(f"Registry install path: {install_path}")
            print(f"Registry path exists: {os.path.exists(install_path)}")
    except Exception as e:
        print(f"Registry check failed: {e}")
    
    problematic_path = r"C:\Program Files (x86)\Roblox\Versions"
    print(f"\nChecking problematic path: {problematic_path}")
    try:
        if os.path.exists(problematic_path):
            contents = os.listdir(problematic_path)
            print(f"  Path exists with {len(contents)} items")
            for item in contents[:5]:
                item_path = os.path.join(problematic_path, item)
                is_dir = os.path.isdir(item_path)
                print(f"    - {item} ({'DIR' if is_dir else 'FILE'})")
            if len(contents) > 5:
                print(f"    ... and {len(contents) - 5} more items")
        else:
            print("  Path does not exist")
    except Exception as e:
        print(f"  Error accessing path: {e}")
    
    print(f"\nDetecting Roblox installations...")
    try:
        found_paths = get_all_versions_paths()
        print(f"Detection completed successfully!")
    except Exception as e:
        print(f"Detection failed: {e}")
    
    print("=== END DIAGNOSIS ===\n")

# ================================================
# New Skybox Creator classes and functions from RSBP-2Beta.py
# Using PySide6 now
# ================================================

vrs = 'r8.9.25-bday'
FACE_NAMES = ['ft', 'bk', 'lf', 'rt', 'up', 'dn']
Trotation = 270

class SkyboxPreview(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textures = {}
        self.rot_x = 20
        self.rot_y = -30
        self.last_pos = None
        self.use_spherical_uv = False
        self.subdivide = 20

    def initializeGL(self):
        glEnable(GL_TEXTURE_2D)
        glClearColor(0, 0, 0, 1)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)
        glEnable(GL_CULL_FACE)

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60, w / h, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)
        self.drawSkybox()
        glEnable(GL_CULL_FACE)
        glDepthMask(GL_TRUE)

    def drawSkybox(self):
        size = 1.0
        vertices = [
            [-size, -size, size],
            [size, -size, size],
            [size, size, size],
            [-size, size, size],
            [-size, -size, -size],
            [size, -size, -size],
            [size, size, -size],
            [-size, size, -size],
        ]

        faces = {
            'ft': ([0, 1, 2, 3], [(0, 0), (1, 0), (1, 1), (0, 1)]),
            'bk': ([5, 4, 7, 6], [(0, 0), (1, 0), (1, 1), (0, 1)]),
            'rt': ([4, 0, 3, 7], [(0, 0), (1, 0), (1, 1), (0, 1)]),
            'lf': ([1, 5, 6, 2], [(0, 0), (1, 0), (1, 1), (0, 1)]),
            'up': ([3, 2, 6, 7], [(0, 0), (1, 0), (1, 1), (0, 1)]),
            'dn': ([4, 5, 1, 0], [(0, 0), (1, 0), (1, 1), (0, 1)]),
        }

        glEnable(GL_TEXTURE_2D)
        glFrontFace(GL_CW)

        for face_name, (verts_idx, _) in faces.items():
            tex_id = self.textures.get(face_name)
            if tex_id:
                glBindTexture(GL_TEXTURE_2D, tex_id)
            else:
                glBindTexture(GL_TEXTURE_2D, 0)

            if self.use_spherical_uv:
                self.drawFaceSpherical(vertices, verts_idx)
            else:
                self.drawFaceFlat(vertices, verts_idx)

        glFrontFace(GL_CCW)

    def drawFaceFlat(self, vertices, verts_idx):
        texcoords = [(0, 0), (1, 0), (1, 1), (0, 1)]
        glBegin(GL_QUADS)
        for vi, (u, v) in zip(verts_idx, texcoords):
            glTexCoord2f(u, v)
            glVertex3f(*vertices[vi])
        glEnd()

    def drawFaceSpherical(self, vertices, verts_idx):
        sub = self.subdivide
        v0 = vertices[verts_idx[0]]
        v1 = vertices[verts_idx[1]]
        v2 = vertices[verts_idx[2]]
        v3 = vertices[verts_idx[3]]

        for i in range(sub):
            t0 = i / sub
            t1 = (i + 1) / sub
            glBegin(GL_TRIANGLE_STRIP)
            for j in range(sub + 1):
                s = j / sub

                pA = self.lerp3D(self.lerp3D(v0, v1, s), self.lerp3D(v3, v2, s), t0)
                pB = self.lerp3D(self.lerp3D(v0, v1, s), self.lerp3D(v3, v2, s), t1)

                uA, vA = self.cubeToSphereUV(pA)
                uB, vB = self.cubeToSphereUV(pB)

                glTexCoord2f(uA, vA)
                glVertex3f(*pA)
                glTexCoord2f(uB, vB)
                glVertex3f(*pB)
            glEnd()

    def lerp3D(self, a, b, t):
        return [a[i] + (b[i] - a[i]) * t for i in range(3)]

    def cubeToSphereUV(self, pos):
        x, y, z = pos
        length = math.sqrt(x*x + y*y + z*z)
        nx, ny, nz = x/length, y/length, z/length

        u = 0.5 + math.atan2(nz, nx) / (2 * math.pi)
        v = 0.5 - math.asin(ny) / math.pi
        return u, v

    def loadTexture(self, face_name, pil_image):
        img = pil_image.convert('RGBA')
        img_data = img.tobytes("raw", "RGBA", 0, -1)
        w, h = img.size

        if face_name in self.textures:
            glDeleteTextures([self.textures[face_name]])
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        self.textures[face_name] = tex_id
        self.update()

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.last_pos = event.pos()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self.last_pos:
            dx = event.x() - self.last_pos.x()
            dy = event.y() - self.last_pos.y()
            self.rot_x += dy
            self.rot_y += dx
            self.rot_x = max(min(self.rot_x, 90), -90)
            self.last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self.last_pos = None


class SkyboxGenerator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Roblox SkyBox Project - ava.service " + vrs)
        self.setMinimumSize(1000, 600)

        self.face_images = {face: None for face in FACE_NAMES}
        self.face_rotations = {face: 0 for face in FACE_NAMES}
        self.stretch_image = None
        self.stretch_rotation = 0

        self.temp_folder = os.path.join(os.getcwd(), "temp_skybox_images")
        os.makedirs(self.temp_folder, exist_ok=True)

        self.initUI()

    def initUI(self):
        main_layout = QtWidgets.QHBoxLayout(self)

        panel = QtWidgets.QFrame()
        panel.setFixedWidth(460)
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(10, 10, 10, 10)

        panel_layout.addWidget(QtWidgets.QLabel("Skybox Title (folder name):"))
        self.title_input = QtWidgets.QLineEdit()
        panel_layout.addWidget(self.title_input)

        panel_layout.addSpacing(15)

        self.mode_group = QtWidgets.QButtonGroup()
        self.radio_six = QtWidgets.QRadioButton("Six Separate Images (recommended)")
        self.radio_stretch = QtWidgets.QRadioButton("Single Stretch Image")
        self.radio_six.setChecked(True)
        self.mode_group.addButton(self.radio_six)
        self.mode_group.addButton(self.radio_stretch)
        panel_layout.addWidget(self.radio_six)
        
        stretch_image_layout = QtWidgets.QHBoxLayout()
        stretch_image_layout.addWidget(self.radio_stretch)
        self.stretch_path_edit = QtWidgets.QLineEdit()
        self.stretch_path_edit.setReadOnly(True)
        stretch_image_layout.addWidget(self.stretch_path_edit, 1)

        self.stretch_rotate_btn = QtWidgets.QPushButton("R")
        self.stretch_rotate_btn.setFixedWidth(20)
        self.stretch_rotate_btn.clicked.connect(self.rotateStretchImage)
        stretch_image_layout.addWidget(self.stretch_rotate_btn)
        
        self.stretch_flip_btn = QtWidgets.QPushButton("F")
        self.stretch_flip_btn.setFixedWidth(20)
        self.stretch_flip_btn.clicked.connect(self.flipStretchImage)
        stretch_image_layout.addWidget(self.stretch_flip_btn)

        self.btn_browse_stretch = QtWidgets.QPushButton("Browse")
        self.btn_browse_stretch.setFixedWidth(55)
        self.btn_browse_stretch.clicked.connect(self.browseStretchImage)
        stretch_image_layout.addWidget(self.btn_browse_stretch)
        
        panel_layout.addLayout(stretch_image_layout)
        panel_layout.addSpacing(10)

        self.face_inputs = {}
        for face in FACE_NAMES:
            face_label = QtWidgets.QLabel(face.upper())
            face_label.setFixedWidth(25)

            face_path_edit = QtWidgets.QLineEdit()
            face_path_edit.setReadOnly(True)

            browse_btn = QtWidgets.QPushButton("Browse")
            browse_btn.setFixedWidth(55)
            browse_btn.clicked.connect(lambda _, f=face: self.browseFaceImage(f))

            load_tex_btn = QtWidgets.QPushButton("Load .tex")
            load_tex_btn.setFixedWidth(60)
            load_tex_btn.clicked.connect(lambda _, f=face: self.loadTexFile(f))

            rotate_btn = QtWidgets.QPushButton("R")
            rotate_btn.setFixedWidth(20)
            rotate_btn.clicked.connect(lambda _, f=face: self.rotateImage(f))

            flip_btn = QtWidgets.QPushButton("F")
            flip_btn.setFixedWidth(20)
            flip_btn.clicked.connect(lambda _, f=face: self.flipImage(f))

            rotation_label = QtWidgets.QLabel("0")
            rotation_label.setFixedWidth(20)
            rotation_label.setAlignment(QtCore.Qt.AlignCenter)

            row_layout = QtWidgets.QHBoxLayout()
            row_layout.addWidget(face_label)
            row_layout.addWidget(rotate_btn)
            row_layout.addWidget(flip_btn)
            row_layout.addWidget(rotation_label)
            row_layout.addWidget(browse_btn)
            row_layout.addWidget(load_tex_btn)
            row_layout.addWidget(face_path_edit)

            panel_layout.addLayout(row_layout)

            self.face_inputs[face] = {
                'path_edit': face_path_edit,
                'browse_btn': browse_btn,
                'load_tex_btn': load_tex_btn,
                'rotate_btn': rotate_btn,
                'flip_btn': flip_btn,
                'rotation_label': rotation_label,
            }
            
            if face == 'up':
                self.face_rotations[face] = Trotation
                rotation_label.setText(str(Trotation))

        panel_layout.addSpacing(20)

        self.btn_bulk_import = QtWidgets.QPushButton("Bulk Import Images")
        self.btn_bulk_import.clicked.connect(self.bulkImportImages)
        panel_layout.addWidget(self.btn_bulk_import)

        panel_layout.addSpacing(10)

        self.btn_generate = QtWidgets.QPushButton("Generate Skybox")
        self.btn_generate.clicked.connect(self.generateSkybox)
        panel_layout.addWidget(self.btn_generate)

        panel_layout.addStretch()

        main_layout.addWidget(panel)

        self.preview = SkyboxPreview()
        main_layout.addWidget(self.preview, 1)

        self.mode_group.buttonClicked.connect(self.updateMode)
        self.updateMode()

    def updateMode(self):
        six_mode = self.radio_six.isChecked()
        for face in FACE_NAMES:
            self.face_inputs[face]['path_edit'].setEnabled(six_mode)
            self.face_inputs[face]['browse_btn'].setEnabled(six_mode)
            self.face_inputs[face]['load_tex_btn'].setEnabled(six_mode)
            self.face_inputs[face]['rotate_btn'].setEnabled(six_mode)
            self.face_inputs[face]['flip_btn'].setEnabled(six_mode)
            self.face_inputs[face]['rotation_label'].setEnabled(six_mode)

        self.stretch_path_edit.setEnabled(not six_mode)
        self.btn_browse_stretch.setEnabled(not six_mode)
        self.stretch_rotate_btn.setEnabled(not six_mode)
        self.stretch_flip_btn.setEnabled(not six_mode)

        self.preview.textures.clear()
        self.preview.use_spherical_uv = not six_mode
        self.preview.update()

    def copyToTemp(self, face, source_path):
        dest_path = os.path.join(self.temp_folder, f"{face}.png")
        try:
            img = Image.open(source_path)
            img = img.resize((512, 512), Image.Resampling.LANCZOS)
            
            if face == 'up':
                img = img.rotate(Trotation, expand=False)
                self.face_rotations[face] = Trotation
                self.face_inputs[face]['rotation_label'].setText(str(Trotation))


            img.save(dest_path, format='PNG')
            return dest_path
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Copy Error", f"Failed copying image to temp:\n{str(e)}")
            return None

    def overwriteTempImage(self, face):
        if self.face_images[face]:
            dest_path = os.path.join(self.temp_folder, f"{face}.png")
            try:
                self.face_images[face].save(dest_path, format='PNG')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Save Error", f"Failed saving updated image to temp:\n{str(e)}")

    def overwriteTempStretch(self):
        if self.stretch_image:
            dest_path = os.path.join(self.temp_folder, "stretch.png")
            try:
                self.stretch_image.save(dest_path, format='PNG')
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Save Error", f"Failed saving updated stretch image to temp:\n{str(e)}")

    def browseFaceImage(self, face):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, f"Select image for {face.upper()}", "",
                                                     "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)")
        if path:
            temp_path = self.copyToTemp(face, path)
            if temp_path:
                img = Image.open(temp_path)
                self.face_images[face] = img
                self.face_inputs[face]['path_edit'].setText(temp_path)
                self.preview.loadTexture(face, img)

    def loadTexFile(self, face):
        pass

    def rotateImage(self, face):
        if self.face_images[face]:
            current_rot = self.face_rotations[face]
            new_rot = (current_rot - 90) % 360  
            self.face_rotations[face] = new_rot
            self.face_images[face] = self.face_images[face].rotate(-90, expand=True)
            self.overwriteTempImage(face)
            self.preview.loadTexture(face, self.face_images[face])
            self.face_inputs[face]['rotation_label'].setText(str(new_rot))


    def flipImage(self, face):
        if self.face_images[face]:
            self.face_images[face] = self.face_images[face].transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            self.overwriteTempImage(face)
            self.preview.loadTexture(face, self.face_images[face])

    def browseStretchImage(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select stretch image", "",
                                                     "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)")
        if path:
            img = Image.open(path).resize((512, 512), Image.Resampling.LANCZOS)
            self.stretch_image = img
            temp_path = os.path.join(self.temp_folder, "stretch.png")
            img.save(temp_path, format='PNG')
            self.stretch_path_edit.setText(temp_path)
            self.preview.loadTexture('stretch', img)

    def rotateStretchImage(self):
        if self.stretch_image:
            self.stretch_image = self.stretch_image.rotate(-90, expand=True)
            self.overwriteTempStretch()
            self.preview.loadTexture('stretch', self.stretch_image)

    def flipStretchImage(self):
        if self.stretch_image:
            self.stretch_image = self.stretch_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            self.overwriteTempStretch()
            self.preview.loadTexture('stretch', self.stretch_image)

    def bulkImportImages(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder with images")
        if not folder:
            return

        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            for face in FACE_NAMES:
                if fname.lower().endswith(face + ".png"):
                    img = Image.open(fpath).resize((512, 512), Image.Resampling.LANCZOS)
                    if face == 'up':
                        img = img.rotate(Trotation, expand=False)
                        self.face_rotations[face] = Trotation
                        self.face_inputs[face]['rotation_label'].setText(str(Trotation))
                    
                    self.face_images[face] = img
                    temp_path = os.path.join(self.temp_folder, f"{face}.png")
                    img.save(temp_path, format='PNG')
                    self.face_inputs[face]['path_edit'].setText(temp_path)
                    self.preview.loadTexture(face, img)
                    break
    
    def generateSkybox(self):
        title = self.title_input.text().strip()
        if not title:
            QtWidgets.QMessageBox.warning(self, "Missing Title", "You need to enter a folder name!")
            return

        output_folder = os.path.join(os.getcwd(), title)
        if os.path.exists(output_folder):
            reply = QtWidgets.QMessageBox.question(self, "Overwrite?", 
                                 f"Folder '{title}' exists. Overwrite?", 
                                 QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                return
            shutil.rmtree(output_folder)

        os.makedirs(output_folder)

        if self.radio_six.isChecked():
            for face in FACE_NAMES:
                img = self.face_images.get(face)
                if not img:
                    QtWidgets.QMessageBox.warning(self, "Missing Image", f"Face '{face}' is missing!")
                    return

                img_to_save = img
                if face == 'up':
                    img_to_save = img.rotate(Trotation, expand=False)
                
                png_path = os.path.join(output_folder, f"sky512_{face}.png")
                img_to_save.save(png_path, format='PNG')

                tex_path = os.path.join(output_folder, f"sky512_{face}.tex")
                tex_img = img_to_save.convert('RGBA')
                tex_img.save(tex_path, format='PNG')

        else:
            if not self.stretch_image:
                QtWidgets.QMessageBox.warning(self, "No Stretch Image", "Load a stretch image first!")
                return

            for face in FACE_NAMES:
                img_to_save = self.stretch_image
                if face == 'up':
                    img_to_save = img_to_save.rotate(Trotation, expand=False)
                
                png_path = os.path.join(output_folder, f"sky512_{face}.png")
                img_to_save.save(png_path, format='PNG')
                tex_path = os.path.join(output_folder, f"sky512_{face}.tex")
                tex_img = img_to_save.convert('RGBA')
                tex_img.save(tex_path, format='PNG')

        QtWidgets.QMessageBox.information(self, "Done", f"Skybox generated in '{output_folder}'")
        shutil.rmtree(self.temp_folder, ignore_errors=True)
        os.makedirs(self.temp_folder, exist_ok=True)
# ================================================

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Initializing MainWindow...")
        print("[DEBUG] Checking for updates...")
        check_for_update()
        print("[DEBUG] Detecting Roblox installations...")
        
        if not hasattr(self, 'roblox_shortcut') or not self.roblox_shortcut:
            auto_detected = find_roblox_executable()
            if auto_detected:
                self.roblox_shortcut = auto_detected
                print(f"[DEBUG] Auto-detected Roblox: {auto_detected}")
        
        print("[DEBUG] Setting up UI...")
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
        self.config_path = os.path.join(BASE_DIR, "user_config.json")
        self.skybox_dir = os.path.abspath(os.path.join(BASE_DIR, "src", "skybox"))
        self.roblox_shortcut = ""
        local_app_data = os.getenv("LOCALAPPDATA")
        self.skybox_preview_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Previews")
        os.makedirs(self.skybox_preview_dir, exist_ok=True)
        self.available_skyboxes = self.fetch_skybox_list()
        print("[DEBUG] Downloading skybox previews...")
        self.ensure_previews_zip()
        print("[DEBUG] Previews zip ensured and extracted.")
        self.load_config()
        self.last_custom_sky_folder = None

        main_bg = QFrame(self)
        main_bg.setObjectName("MainBg")
        main_bg_layout = QVBoxLayout(main_bg)
        main_bg_layout.setContentsMargins(0, 0, 0, 0)

        self.outer_layout = QVBoxLayout()
        self.outer_layout.setContentsMargins(40, 40, 40, 40)
        self.outer_layout.setSpacing(0)
        main_bg_layout.addLayout(self.outer_layout)

        super_layout = QVBoxLayout(self)
        super_layout.setContentsMargins(0, 0, 0, 0)
        super_layout.addWidget(main_bg)

        self.init_ui()

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
        marker = os.path.join(self.skybox_preview_dir, ".unzipped")
        if not os.path.exists(marker):
            import tempfile
            import requests
            zip_path = os.path.join(tempfile.gettempdir(), "SkyboxPNGs.zip")
            try:
                resp = requests.get(SkyboxPNGsZIP)
                resp.raise_for_status()
                with open(zip_path, "wb") as f:
                    f.write(resp.content)
                unzip_file(zip_path, self.skybox_preview_dir)
                with open(marker, "w") as f:
                    f.write("done")
            except Exception as e:
                print(f"Failed to download/extract SkyboxPNGs.zip: {e}")

    def download_all_previews(self):
        pass

    def get_skybox_names(self):
        return self.available_skyboxes

    def init_ui(self):
        outer_layout = self.outer_layout

        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        title = QLabel("CDBL x RSBP")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: white;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        version = QLabel("Version 1.2")
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

        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.status_label.setStyleSheet("color: #b8f582; margin-bottom: 6px;")
        outer_layout.addWidget(self.status_label)

        outer_layout.addSpacing(18)

        tab_bar = QTabBar()
        tab_bar.addTab("Roblox")
        tab_bar.addTab("Skyboxes")
        tab_bar.addTab("Textures")
        tab_bar.addTab("Settings")
        tab_bar.addTab("Customization")
        tab_bar.addTab("Skybox Creator")
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

        outer_layout.addSpacing(12)

        self.stacked = QStackedWidget()
        self.stacked.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        roblox_page = QWidget()
        roblox_layout = QVBoxLayout(roblox_page)
        roblox_layout.setAlignment(Qt.AlignTop)
        roblox_label = QLabel("Roblox Launcher")
        roblox_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        roblox_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        roblox_layout.addWidget(roblox_label)

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

        roblox_layout.addStretch()

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

        skybox_page = QWidget()
        skybox_layout = QHBoxLayout(skybox_page)
        skybox_layout.setContentsMargins(0, 0, 0, 0)
        skybox_layout.setSpacing(18)

        left_side = QVBoxLayout()
        left_side.setAlignment(Qt.AlignTop)
        skybox_label = QLabel("Skybox Management")
        skybox_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        skybox_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        left_side.addWidget(skybox_label)

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

        button_width = 320

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

        right_side = QVBoxLayout()
        right_side.setAlignment(Qt.AlignTop)

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

        right_side.addSpacing(18)
        custom_sky_btn = QPushButton("[📂] Use Custom Sky Folder")
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
        self.apply_custom_sky_btn = QPushButton("[✔️] Apply Custom Skybox")
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

        skybox_layout.addLayout(left_side, 2)
        skybox_layout.addLayout(right_side, 3)
        self.stacked.addWidget(skybox_page)

        textures_page = QWidget()
        textures_layout = QVBoxLayout(textures_page)
        textures_layout.setAlignment(Qt.AlignTop)
        textures_label = QLabel("Texture Management")
        textures_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        textures_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        textures_layout.addWidget(textures_label)

        dark_btn_row = QHBoxLayout()
        dark_btn_row.setContentsMargins(0, 0, 0, 0)
        dark_btn_row.setAlignment(Qt.AlignVCenter)
        apply_dark_btn = QPushButton("[✔️] Apply Dark Textures")
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
        restore_dark_btn = QPushButton("[❌] Restore Default Textures")
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

        restore_btn = QPushButton("[❌] Full Restore")
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

        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setAlignment(Qt.AlignTop)
        settings_label = QLabel("Settings")
        settings_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        settings_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        settings_layout.addWidget(settings_label)

        warning_label = QLabel("⚠️ Settings only work on regular Roblox (not Bloxstrap/Fishstrap)!")
        warning_label.setStyleSheet("color: #ffb347; font-weight: bold; margin-bottom: 12px;")
        settings_layout.addWidget(warning_label)

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

        apply_btn = QPushButton("[✔️] Apply Settings")
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

        customization_page = QWidget()
        customization_layout = QVBoxLayout(customization_page)
        customization_layout.setAlignment(Qt.AlignTop)
        customization_label = QLabel("Customization")
        customization_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        customization_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        customization_layout.addWidget(customization_label)

        oof_section_label = QLabel("OOF Sound Management")
        oof_section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        oof_section_label.setStyleSheet("color: #b8f582; margin-bottom: 6px;")
        customization_layout.addWidget(oof_section_label)

        oof_btn_row = QHBoxLayout()
        apply_oof_btn = QPushButton("[✔️] Apply OOF Sound")
        apply_oof_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        apply_oof_btn.setStyleSheet("""
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
        apply_oof_btn.clicked.connect(self.apply_oof_sound)
        oof_btn_row.addWidget(apply_oof_btn)
        restore_oof_btn = QPushButton("[❌] Restore Default OOF Sound")
        restore_oof_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        restore_oof_btn.setStyleSheet("""
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
        restore_oof_btn.clicked.connect(self.restore_oof_sound)
        oof_btn_row.addWidget(restore_oof_btn)
        customization_layout.addLayout(oof_btn_row)

        customization_layout.addStretch()

        fast_flag_btn = QPushButton("Fast Flag Editor")
        fast_flag_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        fast_flag_btn.setStyleSheet("""
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
        fast_flag_btn.clicked.connect(self.launch_fast_flag_editor)
        customization_layout.addWidget(fast_flag_btn)

        self.stacked.addWidget(customization_page)
        
        skybox_creator_page = SkyboxGenerator()
        self.stacked.addWidget(skybox_creator_page)

        outer_layout.addWidget(self.stacked)
        tab_bar.currentChanged.connect(self.stacked.setCurrentIndex)
        tab_bar.setCurrentIndex(0)

        if self.skybox_list.count() > 0:
            self.skybox_list.setCurrentRow(0)
        else:
            self.skybox_preview.setText("No online skyboxes found.")

    def save_config(self):
        config = {
            "roblox_shortcut": self.roblox_shortcut,
            "last_custom_sky_folder": self.last_custom_sky_folder
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                try:
                    config = json.load(f)
                    self.roblox_shortcut = config.get("roblox_shortcut", "")
                    self.last_custom_sky_folder = config.get("last_custom_sky_folder", None)
                except json.JSONDecodeError:
                    print("[WARN] Could not read config file, starting fresh.")

    def launch_roblox(self):
        path = self.roblox_shortcut
        if not path:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return
        
        try:
            subprocess.Popen([path])
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Roblox:\n{str(e)}")

    def kill_roblox(self):
        try:
            subprocess.run(["taskkill", "/f", "/im", "RobloxPlayerBeta.exe"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            QMessageBox.information(self, "Success", "Roblox has been killed.")
        except subprocess.CalledProcessError:
            QMessageBox.warning(self, "Warning", "RobloxPlayerBeta.exe was not found running.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to kill Roblox:\n{str(e)}")

    def browse_shortcut(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Roblox Shortcut (.lnk or .exe)", "", 
                                                 "Roblox Executable (*.exe);;Roblox Shortcut (*.lnk);;All Files (*)")
        if path:
            self.roblox_shortcut = path
            self.shortcut_edit.setText(path)
            self.save_config()

    def install_roblox(self):
        pass

    def apply_skybox(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return
        
        selected_skybox = self.skybox_list.currentItem()
        if not selected_skybox:
            QMessageBox.warning(self, "Error", "Please select a skybox from the list.")
            return

        skybox_name = selected_skybox.text()
        print(f"Applying skybox: {skybox_name}")
        install_skybox(skybox_name, self.roblox_shortcut, self.skybox_dir)

    def restore_skybox(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return

        restore_skybox(self.roblox_shortcut, self.skybox_dir)

    def update_skybox_preview(self, name):
        if name:
            preview_path = os.path.join(self.skybox_preview_dir, name + ".png")
            if os.path.exists(preview_path):
                pixmap = QPixmap(preview_path)
                scaled_pixmap = pixmap.scaled(self.skybox_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.skybox_preview.setPixmap(scaled_pixmap)
            else:
                self.skybox_preview.setText("No Preview")
        else:
            self.skybox_preview.setText("No Preview")

    def use_custom_sky_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Custom Skybox Folder")
        if folder:
            self.last_custom_sky_folder = folder
            self.apply_custom_sky_btn.setEnabled(True)
            self.save_config()
            QMessageBox.information(self, "Success", f"Selected custom skybox folder: {folder}")

    def apply_custom_skybox(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return

        if not self.last_custom_sky_folder or not os.path.isdir(self.last_custom_sky_folder):
            QMessageBox.warning(self, "Error", "No valid custom skybox folder selected.")
            return

        install_skybox(self.last_custom_sky_folder, self.roblox_shortcut, custom=True)

    def apply_dark_textures(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return

        install_dark_textures(self.roblox_shortcut)

    def restore_dark_textures(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return
        
        restore_dark_textures(self.roblox_shortcut)

    def full_restore(self):
        if not self.roblox_shortcut:
            QMessageBox.warning(self, "Error", "No Roblox executable or shortcut path set!")
            return

        full_restore(self.roblox_shortcut)

    def apply_oof_sound(self):
        pass

    def restore_oof_sound(self):
        pass
        
    def apply_settings(self):
        pass

    def launch_fast_flag_editor(self):
        path = os.path.join(BASE_DIR, "func", "FastFlagEditor.exe")
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", "FastFlagEditor.exe not found!")
            return
        try:
            subprocess.Popen([path])
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Fast Flag Editor:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
