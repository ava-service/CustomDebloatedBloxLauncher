# Version information
# Update this for each release
APP_VERSION = "V1-2"

import sys
import os
import subprocess
import json
import urllib.request
import requests
import shutil
import webbrowser
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QMessageBox, QTabBar, QStackedWidget, QSizePolicy, QFrame, QListWidget,
    QLineEdit, QFileDialog, QFormLayout, QCheckBox, QDialog, QTextEdit, QComboBox
)
from PySide6.QtGui import QPixmap, QPainter, QFont, QIcon, QColor
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Property, QRect, QThread, Signal
from func.ApplySkybox import install_skybox, install_assets
from func.ApplyDark import install_dark_textures
from func.Restore import restore_skybox, full_restore, restore_dark_textures
from func.APIFunc import download_file, unzip_file, delete_all_downloads
from func.FastFlags import (
    get_all_versions_paths, check_for_fast_flags, read_fast_flags, write_fast_flags, 
    create_fast_flag_file, enable_fast_flags, disable_fast_flags, are_fast_flags_enabled, get_available_launchers, fix_json_syntax
)

class FastFlagsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fast Flags")
        self.setFixedSize(1000, 750)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font: 10pt "Segoe UI";
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font: 9pt "Segoe UI";
                min-height: 18px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 5px;
                color: #ffffff;
                font: 9pt "Consolas";
                padding: 8px;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font: 9pt "Segoe UI";
                min-height: 18px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 5px solid #ffffff;
                width: 0;
                height: 0;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 5px;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font: bold 9pt "Segoe UI";
                min-height: 18px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
            QCheckBox {
                color: #ffffff;
                font: 9pt "Segoe UI";
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #555;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 2px solid #0078d4;
                border-radius: 3px;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #666;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Initialize dialog properties
        self.available_launchers = get_available_launchers()
        if not self.available_launchers:
            self.available_launchers = ["Roblox"]
        self.current_launcher = self.available_launchers[0]
        
        # Initialize the UI
        self.init_ui()
        
        # Load current flags after UI is set up
        self.load_current_flags()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header section
        header_layout = QHBoxLayout()
        
        # Title and description
        title_layout = QVBoxLayout()
        title = QLabel("Fast Flags")
        title.setStyleSheet("font: bold 16pt 'Segoe UI'; color: #ffffff; margin-bottom: 3px;")
        title_layout.addWidget(title)
        
        description = QLabel("Modify Roblox client behavior with any custom flags")
        description.setStyleSheet("font: 10pt 'Segoe UI'; color: #aaaaaa;")
        title_layout.addWidget(description)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Right side controls
        controls_layout = QVBoxLayout()
        controls_layout.setAlignment(Qt.AlignRight)
        
        # Launcher selection
        launcher_label = QLabel("Target Launcher")
        launcher_label.setStyleSheet("font: 9pt 'Segoe UI'; color: #aaaaaa; margin-bottom: 3px;")
        controls_layout.addWidget(launcher_label)
        
        self.launcher_combo = QComboBox()
        self.launcher_combo.addItems(self.available_launchers)
        self.launcher_combo.setCurrentText(self.current_launcher)
        self.launcher_combo.currentTextChanged.connect(self.on_launcher_changed)
        self.launcher_combo.setMinimumWidth(140)
        controls_layout.addWidget(self.launcher_combo)
        
        # Enable/Disable buttons
        controls_layout.addSpacing(8)
        toggle_label = QLabel("Fast Flags Control")
        toggle_label.setStyleSheet("font: 9pt 'Segoe UI'; color: #aaaaaa; margin-bottom: 3px;")
        controls_layout.addWidget(toggle_label)
        
        # Button container
        button_container = QHBoxLayout()
        button_container.setSpacing(5)
        
        self.enable_flags_btn = QPushButton("On")
        self.enable_flags_btn.setFixedSize(65, 30)
        self.enable_flags_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d5a2d;
                color: #8effc6;
                border: none;
                border-radius: 4px;
                font: bold 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #3d7a3d;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        self.enable_flags_btn.clicked.connect(self.enable_fast_flags)
        button_container.addWidget(self.enable_flags_btn)
        
        self.disable_flags_btn = QPushButton("Off")
        self.disable_flags_btn.setFixedSize(65, 30)
        self.disable_flags_btn.setStyleSheet("""
            QPushButton {
                background-color: #5a2d2d;
                color: #ff8e8e;
                border: none;
                border-radius: 4px;
                font: bold 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #7a3d3d;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #aaa;
            }
        """)
        self.disable_flags_btn.clicked.connect(self.disable_fast_flags)
        button_container.addWidget(self.disable_flags_btn)
        
        controls_layout.addLayout(button_container)
        
        # Add controls to header
        header_layout.addLayout(controls_layout)
        
        # Update button states initially
        self.update_fast_flags_buttons()

        layout.addLayout(header_layout)

        # Main content area
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left side - Flag management
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # Add flag section
        add_section = QLabel("Add Flag")
        add_section.setStyleSheet("font: bold 12pt 'Segoe UI'; color: #ffffff; margin-bottom: 5px;")
        left_layout.addWidget(add_section)
        
        # Flag name input
        flag_name_label = QLabel("Flag Name")
        flag_name_label.setStyleSheet("font: 9pt 'Segoe UI'; color: #aaaaaa; margin-bottom: 2px;")
        left_layout.addWidget(flag_name_label)
        
        self.flag_name_input = QLineEdit()
        self.flag_name_input.setPlaceholderText("e.g., FFlagExampleFlag, CustomFlag, etc.")
        left_layout.addWidget(self.flag_name_input)
        
        # Flag value input
        flag_value_label = QLabel("Value")
        flag_value_label.setStyleSheet("font: 9pt 'Segoe UI'; color: #aaaaaa; margin-bottom: 2px; margin-top: 8px;")
        left_layout.addWidget(flag_value_label)
        
        self.flag_value_input = QLineEdit()
        self.flag_value_input.setPlaceholderText("true, false, number, string, etc.")
        left_layout.addWidget(self.flag_value_input)
        
        # Add flag button
        add_flag_btn = QPushButton("Add Flag")
        add_flag_btn.clicked.connect(self.add_flag)
        add_flag_btn.setStyleSheet("margin-top: 8px;")
        left_layout.addWidget(add_flag_btn)
        
        # Preset flags section
        left_layout.addSpacing(20)
        preset_section = QLabel("Preset Flags")
        preset_section.setStyleSheet("font: bold 12pt 'Segoe UI'; color: #ffffff; margin-bottom: 8px;")
        left_layout.addWidget(preset_section)
        
        # Create preset buttons with proper sizing
        presets = [
            ("Unlock FPS", "DFIntTaskSchedulerTargetFps", "0"),
            ("Better Font", "FFlagEnableNewFontNameMappingABTest", "false"),
            ("Disable Telemetry", "FFlagDebugDisableTelemetryEphemeralCounter", "true"),
            ("Force Vulkan", "FFlagDebugGraphicsPreferVulkan", "true"),
            ("Reduce Input Lag", "DFIntDebugFRMQualityLevelOverride", "1"),
            ("Better Shadows", "FIntRenderShadowIntensity", "75")
        ]
        
        for name, flag, value in presets:
            btn = QPushButton(name)
            btn.setMinimumWidth(200)
            btn.setFixedHeight(32)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333333;
                    color: #ffffff;
                    text-align: left;
                    padding: 6px 12px;
                    margin-bottom: 3px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            btn.clicked.connect(lambda checked, f=flag, v=value: self.add_preset_flag(f, v))
            left_layout.addWidget(btn)
        
        left_layout.addStretch()
        content_layout.addLayout(left_layout, 1)

        # Right side - Current flags display
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        # Current flags header with controls
        flags_header = QHBoxLayout()
        current_label = QLabel("Current Flags")
        current_label.setStyleSheet("font: bold 12pt 'Segoe UI'; color: #ffffff;")
        flags_header.addWidget(current_label)
        
        flags_header.addStretch()
        
        # Action buttons with proper sizing
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(70, 30)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                padding: 5px 10px;
                font: 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #404040;
            }
        """)
        refresh_btn.clicked.connect(self.load_current_flags)
        flags_header.addWidget(refresh_btn)
        
        repair_btn = QPushButton("Repair JSON")
        repair_btn.setFixedSize(85, 30)
        repair_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c5c2e;
                padding: 5px 10px;
                font: 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #7a7a3d;
            }
        """)
        repair_btn.clicked.connect(self.repair_json_files)
        flags_header.addWidget(repair_btn)
        
        import_btn = QPushButton("Import JSON")
        import_btn.setFixedSize(85, 30)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e5c2e;
                padding: 5px 10px;
                font: 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #3d7a3d;
            }
        """)
        import_btn.clicked.connect(self.import_json_flags)
        flags_header.addWidget(import_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedSize(70, 30)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #d13438;
                padding: 5px 10px;
                font: 8pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_flags)
        flags_header.addWidget(clear_btn)
        
        right_layout.addLayout(flags_header)
        
        # Flags display with proper height
        self.current_flags_text = QTextEdit()
        self.current_flags_text.setReadOnly(True)
        self.current_flags_text.setMinimumHeight(450)
        right_layout.addWidget(self.current_flags_text)
        
        content_layout.addLayout(right_layout, 2)
        layout.addLayout(content_layout)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(80, 35)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def update_fast_flags_buttons(self):
        """Update the state of fast flags buttons based on current status."""
        enabled = are_fast_flags_enabled(self.current_launcher)
        self.enable_flags_btn.setEnabled(not enabled)
        self.disable_flags_btn.setEnabled(enabled)

    def enable_fast_flags(self):
        """Enable fast flags for the selected launcher."""
        try:
            print(f"[DEBUG] Enable fast flags: launcher={self.current_launcher}")
            
            # Call the enable function
            enabled = enable_fast_flags(self.current_launcher)
            print(f"[DEBUG] Enable result: {enabled}")
            
            # Refresh the display and update buttons
            self.load_current_flags()
            self.update_fast_flags_buttons()
            
            if enabled:
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"Fast flags enabled for {self.current_launcher}!")
            else:
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"No disabled fast flags found for {self.current_launcher}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to enable fast flags:\n{e}")
            self.update_fast_flags_buttons()

    def disable_fast_flags(self):
        """Disable fast flags for the selected launcher."""
        try:
            print(f"[DEBUG] Disable fast flags: launcher={self.current_launcher}")
            
            # Call the disable function
            disabled = disable_fast_flags(self.current_launcher)
            print(f"[DEBUG] Disable result: {disabled}")
            
            # Refresh the display and update buttons
            self.load_current_flags()
            self.update_fast_flags_buttons()
            
            if disabled:
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"Fast flags disabled for {self.current_launcher}!")
            else:
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"No active fast flags found for {self.current_launcher}.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to disable fast flags:\n{e}")
            self.update_fast_flags_buttons()

    def on_launcher_changed(self, launcher):
        """Handle launcher selection change."""
        self.current_launcher = launcher
        # Update button states for new launcher
        self.update_fast_flags_buttons()
        # Refresh flags display for new launcher
        self.load_current_flags()

    def load_current_flags(self):
        """Load and display current fast flags for the selected launcher."""
        try:
            flags = read_fast_flags(self.current_launcher)
            if flags:
                flag_text = ""
                for flag, value in sorted(flags.items()):
                    # Format the value properly for display
                    if isinstance(value, str):
                        formatted_value = f'"{value}"'
                    else:
                        formatted_value = str(value).lower() if isinstance(value, bool) else str(value)
                    flag_text += f"{flag}: {formatted_value}\n"
                self.current_flags_text.setPlainText(flag_text)
            else:
                self.current_flags_text.setPlainText(f"No fast flags currently set for {self.current_launcher}.")
        except Exception as e:
            self.current_flags_text.setPlainText(f"Error loading flags: {e}")

    def add_flag(self):
        """Add a new fast flag."""
        flag_name = self.flag_name_input.text().strip()
        flag_value = self.flag_value_input.text().strip()
        
        if not flag_name or not flag_value:
            QMessageBox.warning(self, "Invalid Input", "Please enter both flag name and value.")
            return
        
        self._add_flag_internal(flag_name, flag_value)

    def add_preset_flag(self, flag_name, flag_value):
        """Add a preset fast flag."""
        self._add_flag_internal(flag_name, flag_value)

    def _add_flag_internal(self, flag_name, flag_value):
        """Internal method to add a flag."""
        # Convert value to appropriate type
        converted_value = self.convert_flag_value(flag_value)
        
        try:
            # Read current flags for selected launcher
            current_flags = read_fast_flags(self.current_launcher)
            current_flags[flag_name] = converted_value
            
            # Ensure ClientAppSettings.json exists for selected launcher
            create_fast_flag_file(self.current_launcher)
            
            # Write updated flags for selected launcher
            write_fast_flags(current_flags, self.current_launcher)
            
            # Clear inputs and refresh display
            self.flag_name_input.clear()
            self.flag_value_input.clear()
            self.load_current_flags()
            
            if hasattr(self.parent(), 'status_label'):
                self.parent().status_label.setText(f"Fast flag '{flag_name}' added to {self.current_launcher}!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add fast flag:\n{e}")

    def convert_flag_value(self, value):
        """Convert string value to appropriate type."""
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            try:
                # Try to convert to int
                return int(value)
            except ValueError:
                try:
                    # Try to convert to float
                    return float(value)
                except ValueError:
                    # Keep as string
                    return value

    def clear_all_flags(self):
        """Clear all fast flags for the selected launcher."""
        reply = QMessageBox.question(self, "Clear All Flags", 
                                   f"Are you sure you want to clear all fast flags for {self.current_launcher}?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                write_fast_flags({}, self.current_launcher)
                self.load_current_flags()
                if hasattr(self.parent(), 'status_label'):
                    self.parent().status_label.setText(f"All fast flags cleared for {self.current_launcher}!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to clear fast flags:\n{e}")

    def repair_json_files(self):
        """Repair corrupted JSON files for the selected launcher."""
        reply = QMessageBox.question(
            self, 
            "Repair JSON Files", 
            f"This will attempt to repair any corrupted ClientAppSettings.json files for {self.current_launcher}.\n\n"
            "Corrupted files will be backed up with a .corrupted.bak extension.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                files = check_for_fast_flags(self.current_launcher)
                repaired_count = 0
                
                for file in files:
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                        
                        if not content:
                            continue
                            
                        # Try to parse as-is first
                        try:
                            json.loads(content)
                            # File is already valid
                            continue
                        except json.JSONDecodeError:
                            # Try to fix it
                            fixed_content = fix_json_syntax(content)
                            
                            try:
                                data = json.loads(fixed_content)
                                
                                # Create backup of original
                                backup_path = file + '.corrupted.bak'
                                with open(backup_path, 'w', encoding='utf-8') as backup_f:
                                    backup_f.write(content)
                                
                                # Write repaired version
                                with open(file, 'w', encoding='utf-8') as f:
                                    json.dump(data, f, indent=4)
                                
                                repaired_count += 1
                                print(f"[DEBUG] Repaired {file}")
                                
                            except json.JSONDecodeError:
                                # Could not fix, reset to empty
                                backup_path = file + '.corrupted.bak'
                                with open(backup_path, 'w', encoding='utf-8') as backup_f:
                                    backup_f.write(content)
                                
                                with open(file, 'w', encoding='utf-8') as f:
                                    json.dump({}, f, indent=4)
                                
                                repaired_count += 1
                                print(f"[DEBUG] Reset {file} to empty JSON")
                                
                    except Exception as e:
                        print(f"[ERROR] Could not repair {file}: {e}")
                
                self.load_current_flags()
                
                if repaired_count > 0:
                    if hasattr(self.parent(), 'status_label'):
                        self.parent().status_label.setText(f"Repaired {repaired_count} JSON files for {self.current_launcher}!")
                    QMessageBox.information(
                        self, 
                        "Repair Complete", 
                        f"Successfully repaired {repaired_count} JSON files.\n\n"
                        "Original corrupted files have been backed up with .corrupted.bak extension."
                    )
                else:
                    QMessageBox.information(self, "No Repairs Needed", "All JSON files are already valid.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Repair Error", f"Failed to repair JSON files:\n{e}")

    def import_json_flags(self):
        """Import fast flags from JSON text or file."""
        # Create import dialog
        import_dialog = QDialog(self)
        import_dialog.setWindowTitle("Import Fast Flags JSON")
        import_dialog.setFixedSize(550, 450)  # Increased size
        import_dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout(import_dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Import Fast Flags")
        title.setStyleSheet("font: bold 14pt 'Segoe UI'; color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(f"Paste JSON text below or click 'Load from File' to import flags for {self.current_launcher}:")
        instructions.setStyleSheet("font: 10pt 'Segoe UI'; color: #aaaaaa; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # JSON text area
        json_text = QTextEdit()
        json_text.setPlaceholderText('{\n  "FFlagExampleFlag": true,\n  "CustomSetting": 100,\n  "AnyFlagName": "any value"\n}')
        json_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 5px;
                color: #ffffff;
                font: 10pt "Consolas";
                padding: 10px;
            }
        """)
        layout.addWidget(json_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        load_file_btn = QPushButton("Load from File")
        load_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e5c2e;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font: bold 9pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #3d7a3d;
            }
        """)
        
        def load_from_file():
            file_path, _ = QFileDialog.getOpenFileName(
                import_dialog, 
                "Select JSON File", 
                "", 
                "JSON Files (*.json);;All Files (*)"
            )
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    json_text.setPlainText(content)
                except Exception as e:
                    QMessageBox.critical(import_dialog, "Error", f"Failed to load file:\n{e}")
        
        load_file_btn.clicked.connect(load_from_file)
        button_layout.addWidget(load_file_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(import_dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font: bold 9pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        def import_flags():
            json_content = json_text.toPlainText().strip()
            if not json_content:
                QMessageBox.warning(import_dialog, "Warning", "Please enter JSON content or load from file.")
                return
            
            try:
                # Parse JSON
                flags_data = json.loads(json_content)
                
                if not isinstance(flags_data, dict):
                    QMessageBox.warning(import_dialog, "Invalid JSON", "JSON must be an object/dictionary.")
                    return
                
                # Accept all flags - no validation restrictions
                valid_flags = flags_data
                
                if not valid_flags:
                    QMessageBox.information(import_dialog, "Nothing to Import", "No flags to import.")
                    return
                
                # Merge with existing flags for selected launcher
                current_flags = read_fast_flags(self.current_launcher)
                
                # Count new vs updated flags
                new_flags = 0
                updated_flags = 0
                
                for key, value in valid_flags.items():
                    if key in current_flags:
                        if current_flags[key] != value:
                            updated_flags += 1
                    else:
                        new_flags += 1
                
                # Confirm import
                message = f"Import {len(valid_flags)} flags to {self.current_launcher}?\n\n"
                if new_flags > 0:
                    message += f"• {new_flags} new flags\n"
                if updated_flags > 0:
                    message += f"• {updated_flags} updated flags\n"
                
                reply = QMessageBox.question(
                    import_dialog,
                    "Confirm Import",
                    message,
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Merge and save for selected launcher
                    current_flags.update(valid_flags)
                    
                    # Ensure ClientAppSettings.json exists for selected launcher
                    create_fast_flag_file(self.current_launcher)
                    
                    # Write updated flags for selected launcher
                    write_fast_flags(current_flags, self.current_launcher)
                    
                    # Refresh display
                    self.load_current_flags()
                    
                    # Close import dialog
                    import_dialog.accept()
                    
                    # Show success message
                    if hasattr(self.parent(), 'status_label'):
                        self.parent().status_label.setText(f"Imported {len(valid_flags)} flags to {self.current_launcher}!")
                    QMessageBox.information(self, "Import Successful", f"Successfully imported {len(valid_flags)} flags to {self.current_launcher}!")
                
            except json.JSONDecodeError as e:
                QMessageBox.critical(import_dialog, "Invalid JSON", f"Invalid JSON format:\n{e}")
            except Exception as e:
                QMessageBox.critical(import_dialog, "Import Error", f"Failed to import flags:\n{e}")
        
        import_btn.clicked.connect(import_flags)
        button_layout.addWidget(import_btn)
        
        layout.addLayout(button_layout)
        
        # Show dialog
        import_dialog.exec()

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
        latest = data.get("tag_name", "").lstrip("v")  # Remove 'v' if present
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

class SoundDownloadWorker(QThread):
    finished = Signal(str, str)  # sound_path, error

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            resp = requests.get(self.url)
            resp.raise_for_status()
            with open(self.save_path, "wb") as f:
                f.write(resp.content)
            self.finished.emit(self.save_path, "")
        except Exception as e:
            self.finished.emit("", str(e))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        print("[DEBUG] Initializing MainWindow...")
        print("[DEBUG] Checking for updates...")
        check_for_update()
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
        # Always use an absolute path for the skybox directory
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
        tab_bar.addTab("Customization")
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

        # --- Customization Tab ---
        customization_page = QWidget()
        customization_layout = QVBoxLayout(customization_page)
        customization_layout.setAlignment(Qt.AlignTop)
        customization_label = QLabel("Customization")
        customization_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        customization_label.setStyleSheet("color: #fff; margin-bottom: 8px;")
        customization_layout.addWidget(customization_label)

        # --- OOF Section Label ---
        oof_section_label = QLabel("OOF Sound")
        oof_section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        oof_section_label.setStyleSheet("color: #b8f582; margin-bottom: 4px;")
        customization_layout.addWidget(oof_section_label)

        oof_btn_row = QHBoxLayout()
        oof_btn_row.setAlignment(Qt.AlignLeft)
        button_width = 220  # Set a consistent width for all buttons

        apply_oof_btn = QPushButton("Apply OG OOF")
        apply_oof_btn.setFixedHeight(36)
        apply_oof_btn.setFixedWidth(button_width)
        apply_oof_btn.setStyleSheet("""
            QPushButton {
                background-color: #22303a;
                color: #8edcff;
                border-radius: 10px;
                padding: 6px 18px;
                font: bold 10pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #2c425a;
                color: #fff;
            }
        """)
        apply_oof_btn.clicked.connect(self.apply_og_oof)

        restore_oof_btn = QPushButton("Restore Default OOF")
        restore_oof_btn.setFixedHeight(36)
        restore_oof_btn.setFixedWidth(button_width)
        restore_oof_btn.setStyleSheet("""
            QPushButton {
                background-color: #223a2d;
                color: #8effc6;
                border-radius: 10px;
                padding: 6px 18px;
                font: bold 10pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #2c5a42;
                color: #fff;
            }
        """)
        restore_oof_btn.clicked.connect(self.restore_og_oof)

        oof_btn_row.addWidget(apply_oof_btn)
        oof_btn_row.addWidget(restore_oof_btn)
        customization_layout.addLayout(oof_btn_row)

        # --- Fast Flags Section Label ---
        fast_flags_section_label = QLabel("Fast Flags")
        fast_flags_section_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        fast_flags_section_label.setStyleSheet("color: #b8f582; margin-top: 18px; margin-bottom: 4px;")
        customization_layout.addWidget(fast_flags_section_label)

        # Fast Flags button (same size as OOF buttons)
        fast_flags_btn = QPushButton("Fast Flags")
        fast_flags_btn.setFixedHeight(36)
        fast_flags_btn.setFixedWidth(button_width)
        fast_flags_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e3b5e;
                color: #9bb5ff;
                border-radius: 10px;
                padding: 6px 18px;
                font: bold 10pt "Segoe UI";
            }
            QPushButton:hover {
                background-color: #3d4f7a;
                color: #fff;
            }
        """)
        fast_flags_btn.clicked.connect(self.open_fast_flags_dialog)
        customization_layout.addWidget(fast_flags_btn)

        customization_layout.addStretch()
        self.stacked.addWidget(customization_page)

        outer_layout.addWidget(self.stacked)

        # Connect tab changes to stacked widget
        tab_bar.currentChanged.connect(self.stacked.setCurrentIndex)

        # Set initial preview if any skybox is selected
        if hasattr(self, "skybox_list") and self.skybox_list.count() > 0:
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
        local_app_data = os.getenv("LOCALAPPDATA")
        extract_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Skyboxes", skybox_name)
        os.makedirs(extract_dir, exist_ok=True)

        # Step 1: Download the patch first.
        self.status_label.setText("Downloading patch for skybox...")
        self._worker_patch = DownloadWorker(SkyboxPatch, extract_subfolder="SkyboxPatch")

        def on_patch_finished(patch_zip_path, error):
            self._worker_patch = None  # Clear patch worker
            if error:
                self.status_label.setText("Failed to download patch.")
                QMessageBox.critical(self, "Apply Skybox", f"Failed to download patch:\n{error}")
                return

            # Step 2: Patch is ready, now download the actual skybox.
            self.status_label.setText(f"Downloading skybox '{skybox_name}'...")
            self._worker_skybox = DownloadWorker(zip_url)

            def on_skybox_finished(skybox_zip_path, skybox_error):
                self._worker_skybox = None  # Clear skybox worker
                if skybox_error:
                    self.status_label.setText("Failed to download skybox.")
                    QMessageBox.critical(self, "Apply Skybox", f"Failed to download skybox:\n{skybox_error}")
                    return
                try:
                    # Step 3: Unzip, flatten, and install everything.
                    self.status_label.setText(f"Extracting skybox '{skybox_name}'...")
                    QApplication.processEvents()
                    unzip_file(skybox_zip_path, extract_dir)
                    # Flatten any nested folders
                    for root, dirs, files in os.walk(extract_dir):
                        if root == extract_dir:
                            continue
                        for f in files:
                            src = os.path.join(root, f)
                            dst = os.path.join(extract_dir, f)
                            if not os.path.exists(dst):
                                shutil.move(src, dst)
                    for d in dirs:
                        dir_path = os.path.join(root, d)
                        if os.path.isdir(dir_path) and not os.listdir(dir_path):
                            os.rmdir(dir_path)

                    self.status_label.setText(f"Applying skybox '{skybox_name}'...")
                    QApplication.processEvents()
                    install_assets()  # This will now find the patched assets
                    install_skybox(extract_dir)
                    self.status_label.setText(f"Skybox '{skybox_name}' installed! Restart Roblox to see the changes.")
                    QMessageBox.information(self, "Apply Skybox", f"Skybox '{skybox_name}' installed successfully.\nRestart Roblox to see the changes.")
                except Exception as e:
                    self.status_label.setText("Failed to apply skybox.")
                    QMessageBox.critical(self, "Apply Skybox", f"Failed to install skybox:\n{e}")

            self._worker_skybox.finished.connect(on_skybox_finished)
            self._worker_skybox.start()

        self._worker_patch.finished.connect(on_patch_finished)
        self._worker_patch.start()

    def apply_custom_skybox(self):
        if not self.last_custom_sky_folder or not os.path.isdir(self.last_custom_sky_folder):
            self.status_label.setText("No custom sky folder selected.")
            QMessageBox.warning(self, "Apply Custom Skybox", "No custom sky folder selected.")
            return

        # Download the patch first to ensure assets are available
        self.status_label.setText("Downloading patch for skybox...")
        self._worker_patch = DownloadWorker(SkyboxPatch, extract_subfolder="SkyboxPatch")

        def on_patch_finished(zip_path, error):
            self._worker_patch = None
            if error:
                self.status_label.setText("Failed to download patch.")
                QMessageBox.critical(self, "Apply Custom Skybox", f"Failed to download patch:\n{error}")
                return

            # Patch is ready, now apply the custom skybox
            self.status_label.setText("Applying custom skybox...")
            try:
                install_assets()
                install_skybox(self.last_custom_sky_folder)
                delete_all_downloads()
                self.status_label.setText("Custom skybox applied! Restart Roblox to see the changes.")
                QMessageBox.information(self, "Apply Custom Skybox", "Custom skybox applied successfully.\nRestart Roblox to see the changes.")
            except Exception as e:
                self.status_label.setText("Failed to apply custom skybox.")
                QMessageBox.critical(self, "Apply Custom Skybox", f"Failed to apply custom skybox:\n{e}")
            self.update_skybox_preview(self.last_custom_sky_folder)

        self._worker_patch.finished.connect(on_patch_finished)
        self._worker_patch.start()

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
                
    def apply_og_oof(self):
        print("[DEBUG] Starting apply_og_oof")
        self.status_label.setText("Downloading OG OOF sound...")
        local_app_data = os.getenv("LOCALAPPDATA")
        sounds_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Sounds")
        os.makedirs(sounds_dir, exist_ok=True)
        og_oof_path = os.path.join(sounds_dir, "og-oof.ogg")
        print(f"[DEBUG] OG OOF path: {og_oof_path}")

        def after_download(sound_path, error):
            print(f"[DEBUG] after_download called for apply_og_oof, error: {error}")
            if error:
                self.status_label.setText("Failed to download OG OOF sound.")
                print(f"[ERROR] Failed to download OG OOF sound: {error}")
                QMessageBox.critical(self, "OG OOF", f"Failed to download OG OOF sound:\n{error}")
                self._worker_oof = None
                return
                
            replaced = False
            for versions_root in get_all_versions_paths():
                print(f"[DEBUG] Checking versions_root: {versions_root}")
                for version in os.listdir(versions_root):
                    sounds_path = os.path.join(versions_root, version, "content", "sounds")
                    ouch_path = os.path.join(sounds_path, "ouch.ogg")
                    print(f"[DEBUG] Attempting to replace: {ouch_path}")
                    if os.path.exists(sounds_path):
                        try:
                            shutil.copy2(sound_path, ouch_path)
                            replaced = True
                            print(f"[DEBUG] Replaced {ouch_path}")
                        except Exception as e:
                            print(f"[WARN] Could not replace {ouch_path}: {e}")
                            
            # This block needs to be inside after_download, with proper indentation
            if replaced:
                self.status_label.setText("OG OOF sound applied!")
                print("[DEBUG] OG OOF sound applied!")
                QMessageBox.information(self, "OG OOF", "OG OOF sound applied!\nRestart Roblox to hear the change.")
            else:
                self.status_label.setText("Could not find any Roblox sounds folders.")
                print("[WARN] Could not find any Roblox sounds folders.")
                QMessageBox.warning(self, "OG OOF", "Could not find any Roblox sounds folders.")
            
            # Set worker to None at the end
            self._worker_oof = None

        # Start the worker only once
        print("[DEBUG] Launching SoundDownloadWorker for OG OOF")
        self._worker_oof = SoundDownloadWorker(OgOof, og_oof_path)
        self._worker_oof.finished.connect(after_download)
        self._worker_oof.start()

    def restore_og_oof(self):
        print("[DEBUG] Starting restore_og_oof")
        self.status_label.setText("Downloading default OOF sound...")
        local_app_data = os.getenv("LOCALAPPDATA")
        sounds_dir = os.path.join(local_app_data, "CustomBloxLauncher", "Sounds")
        os.makedirs(sounds_dir, exist_ok=True)
        default_oof_path = os.path.join(sounds_dir, "DefaultOOF.ogg")
        print(f"[DEBUG] Default OOF path: {default_oof_path}")

        def after_download(sound_path, error):
            print(f"[DEBUG] after_download called for restore_og_oof, error: {error}")
            if error:
                self.status_label.setText("Failed to download default OOF sound.")
                print(f"[ERROR] Failed to download default OOF sound: {error}")
                QMessageBox.critical(self, "Restore OOF", f"Failed to download default OOF sound:\n{error}")
                self._worker_restore_oof = None
                return
            
            replaced = False
            for versions_root in get_all_versions_paths():
                print(f"[DEBUG] Checking versions_root: {versions_root}")
                for version in os.listdir(versions_root):
                    sounds_path = os.path.join(versions_root, version, "content", "sounds")
                    ouch_path = os.path.join(sounds_path, "ouch.ogg")
                    print(f"[DEBUG] Attempting to replace: {ouch_path}")
                    if os.path.exists(sounds_path):
                        try:
                            shutil.copy2(sound_path, ouch_path)
                            replaced = True
                            print(f"[DEBUG] Replaced {ouch_path}")
                        except Exception as e:
                            print(f"[WARN] Could not replace {ouch_path}: {e}")
            
            # This block is now correctly indented inside after_download
            if replaced:
                self.status_label.setText("Default OOF sound restored!")
                print("[DEBUG] Default OOF sound restored!")
                QMessageBox.information(self, "Restore OOF", "Default OOF sound restored!\nRestart Roblox to hear the change.")
            else:
                self.status_label.setText("Could not find any Roblox sounds folders.")
                print("[WARN] Could not find any Roblox sounds folders.")
                QMessageBox.warning(self, "Restore OOF", "Could not find any Roblox sounds folders.")
            
            # This is also correctly indented
            self._worker_restore_oof = None

        # This block starts the worker and is correctly indented within the main method
        print("[DEBUG] Launching SoundDownloadWorker for Default OOF")
        self._worker_restore_oof = SoundDownloadWorker(DefaultOOF, default_oof_path)
        self._worker_restore_oof.finished.connect(after_download)
        self._worker_restore_oof.start()
        
    def open_fast_flags_dialog(self):
        """Opens the Fast Flags configuration dialog."""
        dialog = FastFlagsDialog(self)
        dialog.exec()
                
                
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
                            continue
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

