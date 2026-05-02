# hw_decoding.py

import subprocess
import shutil
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

def get_decoding_options():
    """
    Scans the system using Linux commands to identify available graphics cards
    and returns a list of available hardware decoding options.
    """
    options = [("CPU (Software Decoding)", "no")]
    try:
        gpu_info = subprocess.check_output(["lspci"], text=True).lower()
    except Exception:
        gpu_info = ""

    # Check for Intel
    if "intel" in gpu_info:
        options.append(("Intel GPU", "vaapi"))

    # Check for AMD
    if "amd" in gpu_info or "ati" in gpu_info:
        options.append(("AMD GPU", "vaapi"))

    # Check for Nvidia (Proprietary drivers)
    if "nvidia" in gpu_info:
        if shutil.which("nvidia-smi"):
            try:
                cc_out = subprocess.check_output(
                    ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"], 
                    text=True
                )
                major_cc = int(cc_out.split('.')[0])
                # Older cards (older than Pascal/Maxwell usually) might face issues with direct nvdec
                if major_cc < 6:
                    options.append(("Nvidia GPU (Maxwell/Older)", "nvdec-copy"))
                else:
                    options.append(("Nvidia GPU (Modern Cards)", "nvdec"))
            except Exception:
                options.append(("Nvidia GPU", "nvdec-copy"))
        else:
            options.append(("Nvidia GPU", "nvdec-copy"))

    # Check for Nvidia open-source drivers (Nouveau)
    try:
        lsmod_out = subprocess.getoutput("lsmod")
        if "nouveau" in lsmod_out.lower():
            options.append(("Nvidia Open Source Driver (Nouveau)", "vaapi"))
    except Exception:
        pass

    return options


class DecodingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hardware Decoding")
        self.setFixedSize(400, 250)
        self.setModal(True)
        
        # Default value
        self.selected_hwdec = "no"

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("🖥️ Select Decoding Device:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl)

        # Generate buttons based on detected hardware
        options = get_decoding_options()
        for name, hw_arg in options:
            btn = QPushButton(name)
            # Use lambda to pass the parameter correctly on click
            btn.clicked.connect(lambda checked, h=hw_arg: self.select_option(h))
            layout.addWidget(btn)

    def select_option(self, hw_arg):
        self.selected_hwdec = hw_arg
        self.accept()