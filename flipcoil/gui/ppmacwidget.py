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

        self.x_sf = 2e-8
        self.y_sf = 2e-8
        self.angular_sf = 1e-3

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
                    with self.parent_window.lock_ppmac:
                        self.pos = _ppmac.read_motor_pos([1, 2, 3, 4, 7, 8])
                    self.ui.lcd_pos1.display(self.pos[0]*self.x_sf)
                    self.ui.lcd_pos1.display(self.pos[1]*self.y_sf)
                    self.ui.lcd_pos1.display(self.pos[2]*self.x_sf)
                    self.ui.lcd_pos1.display(self.pos[3]*self.y_sf)
                    self.ui.lcd_pos5.display(self.pos[4]*self.angular_sf)
                    self.ui.lcd_pos6.display(self.pos[5]*self.angular_sf)
                    _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def home(self):
        try:
            _home5 = -31860
            _home6 = -21861
            _ppmac.write('enable plc HomeA')
            _sleep(30)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def home_x(self):
        try:
            _ppmac.write('enable plc HomeX')
            _sleep(30)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def home_y(self):
        try:
            _ppmac.write('enable plc HomeY')
            _sleep(30)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def move(self):
        try:
            _steps = [self.ui.sb_steps5.value(), self.ui.sb_steps6.value()]
            if self.ui.rdb_abs.isChecked():
                _mode = '='
            else:
                _mode = '^'
            _ppmac.write('#5j' + _mode + str(_steps[0]) +
                         ';#6j' + _mode + str(_steps[1]))
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def move_x(self):
        try:
            _pos = self.ui.dsb_x.value()/self.x_sf
            if self.ui.rdb_abs_xy.isChecked():
                _mode = '='
            else:
                _mode = '^'
            _msg = '#1,3j' + _mode + str(_pos)
            _ppmac.write(_msg)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def move_y(self):
        try:
            _pos = self.ui.dsb_y.value()/self.y_sf
            if self.ui.rdb_abs_xy.isChecked():
                _mode = '='
            else:
                _mode = '^'
            _msg = '#2,4j' + _mode + str(_pos)
            _ppmac.write(_msg)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
