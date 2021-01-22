"""PPMAC widget for the Flip Coil Control application."""

import os as _os
import sys as _sys
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    QApplication as _QApplication,
    )
from qtpy.QtCore import (
    Qt as _Qt,
    QTimer as _QTimer,
    )
import qtpy.uic as _uic

from flipcoil.gui.utils import (
    get_ui_file as _get_ui_file,
    sleep as _sleep,
    )
from flipcoil.devices import ppmac as _ppmac


class PpmacWidget(_QWidget):
    """PPMAC widget class for the Flip Coil Control application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.timer = _QTimer()
        self.timer.start(1000)

        self.connect_signal_slots()

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        self.ui.timer.timeout.connect(self.update_position)
        self.ui.pbt_home.clicked.connect(self.home)
        self.ui.pbt_move.clicked.connect(self.move)

    def update_position(self):
        try:
            if hasattr(_ppmac, 'ppmac'):
                if all([not _ppmac.ppmac.closed,
                        self.parent().currentWidget() == self]):
                    self.pos = _ppmac.read_motor_pos([7, 8])
                    self.ui.lcd_pos5.display(self.pos[0])
                    _sleep(0.1)
                    self.ui.lcd_pos6.display(self.pos[1])
                    _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def home(self):
        try:
            print(self.parent().currentWidget() == self)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def move(self):
        try:
            _steps = [self.ui.sb_steps5.value(), self.ui.sb_steps6.value()]

            _ppmac.write('#5j^' + str(_steps[0]) +
                         ';#6j^' + str(_steps[1]))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
