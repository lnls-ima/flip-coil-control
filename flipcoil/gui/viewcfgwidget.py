"""View measurement configuration widget"""

import os as _os
import sys as _sys
import traceback as _traceback
from qtpy.QtCore import Qt as _Qt
from qtpy.QtWidgets import (
    QApplication as _QApplication,
    QDialog as _QDialog,
    QMessageBox as _QMessageBox,
    )

import qtpy.uic as _uic

from flipcoil.gui.utils import get_ui_file as _get_ui_file


class ViewCfgWidget(_QDialog):
    """Flip Coil measurement progress dialog."""

    def __init__(self, parent=None):
        """Set up the ui and create connections."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.connect_signal_slots()

    def connect_signal_slots(self):
        pass

    def update_postions(self):
        pass

    def update_progress_bar(self):
        pass
