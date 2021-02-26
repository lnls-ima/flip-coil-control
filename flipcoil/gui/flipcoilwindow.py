"""Main window for the Flip Coil Control application"""

import sys as _sys
import traceback as _traceback
from qtpy.QtWidgets import (
    QFileDialog as _QFileDialog,
    QMainWindow as _QMainWindow,
    QApplication as _QApplication,
    QDesktopWidget as _QDesktopWidget,
    )
from qtpy.QtCore import QTimer as _QTimer
import qtpy.uic as _uic

from flipcoil.gui import utils as _utils

from flipcoil.gui.analysiswidget import AnalysisWidget \
    as _AnalysisWidget
from flipcoil.gui.connectionwidget import ConnectionWidget \
    as _ConnectionWidget
from flipcoil.gui.powersupplywidget import PowerSupplyWidget \
    as _PowerSupplyWidget
from flipcoil.gui.measurementwidget import MeasurementWidget \
    as _MeasurementWidget
from flipcoil.gui.ppmacwidget import PpmacWidget \
    as _PpmacWidget


class FlipCoilWindow(_QMainWindow):
    """Main Window class for the Flip Coil control application."""

    _update_positions_interval = _utils.UPDATE_POSITIONS_INTERVAL

    def __init__(
            self, parent=None, width=_utils.WINDOW_WIDTH,
            height=_utils.WINDOW_HEIGHT):
        """Set up the ui and add main tabs."""
        super().__init__(parent)

        # setup the ui
        uifile = _utils.get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)
        self.resize(width, height)

        # clear the current tabs
        self.ui.twg_main.clear()

        # define tab names and corresponding widgets
        self.tab_names = [
            'connection',
            'motors',
            'power supply',
            'measurement',
            'analysis',
            ]

        self.tab_widgets = [
            _ConnectionWidget(),
            _PpmacWidget(),
            _PowerSupplyWidget(),
            _MeasurementWidget(),
            _AnalysisWidget(),
            ]

        # connect signals and slots
#         self.connect_signal_slots()

        # add widgets to main tab
        self.ui.twg_main.clear()
        for i in range(len(self.tab_names)):
            tab_name = self.tab_names[i]
            tab = self.tab_widgets[i]
            setattr(self, tab_name.replace(' ', ''), tab)
            self.ui.twg_main.addTab(tab, tab_name.capitalize())
            setattr(tab, 'parent_window', self)

        for tab in self.tab_widgets:
            tab.init_tab()

    def centralize_window(self):
        """Centralize window."""
        window_center = _QDesktopWidget().availableGeometry().center()
        self.move(
            window_center.x() - self.geometry().width()/2,
            window_center.y() - self.geometry().height()/2)

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        pass
