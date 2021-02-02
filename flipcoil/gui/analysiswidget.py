"""Analysis widget for the Flip Coil Control application."""

import os as _os
import sys as _sys
import numpy as _np
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    QApplication as _QApplication,
    QVBoxLayout as _QVBoxLayout,
    )
from qtpy.QtCore import Qt as _Qt
import qtpy.uic as _uic

import flipcoil.data as _data
from flipcoil.gui.utils import get_ui_file as _get_ui_file

import matplotlib
from PyQt5.uic.Compiler.qtproxies import QtWidgets
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as _FigureCanvas)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as _NavigationToolbar)
from matplotlib.figure import Figure


class MplCanvas(_FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = matplotlib.figure.Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class AnalysisWidget(_QWidget):
    """Analysis widget class for the Flip Coil Control application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.set_pyplot()

        self.cfg = _data.configuration.MeasurementConfig()
        self.meas = _data.measurement.MeasurementData()

        self.connect_signal_slots()

    @property
    def database_name(self):
        """Database name."""
        return _QApplication.instance().database_name

    @property
    def mongo(self):
        """MongoDB database."""
        return _QApplication.instance().mongo

    @property
    def server(self):
        """Server for MongoDB database."""
        return _QApplication.instance().server

    @property
    def directory(self):
        """Return the default directory."""
        return _QApplication.instance().directory

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        self.ui.cmb_plot.currentIndexChanged.connect(self.plot)
        self.ui.pbt_update.clicked.connect(self.update_meas_list)

    def set_pyplot(self):
        """Configures plot widget"""
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        _toolbar = _NavigationToolbar(self.canvas, self)

        _layout = _QVBoxLayout()
        _layout.addWidget(self.canvas)
        _layout.addWidget(_toolbar)

        self.wg_plot.setLayout(_layout)

    def update_meas_list(self):
        """Update measurement list in combobox."""
        try:
            self.meas.db_update_database(
                database_name=self.database_name,
                mongo=self.mongo, server=self.server)
            names = self.meas.db_get_values('name')

            current_text = self.ui.cmb_meas_name.currentText()
            self.ui.cmb_meas_name.clear()
            self.ui.cmb_meas_name.addItems([name for name in names])
            if len(current_text) == 0:
                self.ui.cmb_meas_name.setCurrentIndex(
                    self.ui.cmb_meas_name.count()-1)
            else:
                self.ui.cmb_meas_name.setCurrentText(current_text)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def load_measurement(self):
        """Loads selected measurement from database."""
        try:
            pass
#             self.parent_window.measurement.first_integral_calculus(
#                 cfg=self.cfg, meas=self.meas)
#             name = self.ui.cmb_cfg_name.currentText()
#             self.cfg.db_update_database(
#                 self.database_name,
#                 mongo=self.mongo, server=self.server)
#             _id = self.cfg.db_search_field('name', name)[0]['id']
#             self.cfg.db_read(_id)
#             self.load_cfg_on_ui()
#             _QMessageBox.information(self, 'Information',
#                                      'Configuration Loaded.',
#                                      _QMessageBox.Ok)
            return True
        except Exception:
            _QMessageBox.warning(self, 'Information',
                                 'Failed to load this configuration.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def plot(self):
        try:
            _meas = self.parent_window.measurement.meas

            self.canvas.axes.cla()
            if self.ui.cmb_plot.currentText() == 'Integrated Field Result':
                for i in range(_meas.I.shape[1]):
                    self.canvas.axes.plot(_meas.I[:, i], label=str(i))
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Results':
                for i in range(_meas.I_f.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.I_f[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Backward Results':
                for i in range(_meas.I_b.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.I_b[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Results':
                for i in range(_meas.I_f.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.I_f[:, i], _color + '-',
                                          label=str(i))
                    self.canvas.axes.plot(_meas.I_b[:, i], _color + '--')
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Voltage':
                for i in range(_meas.data_frw.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.data_frw[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Backward Voltage':
                for i in range(_meas.data_bck.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.data_bck[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Voltage':
                for i in range(_meas.data_frw.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_meas.data_frw[:, i], _color + '-',
                                          label=str(i))
                    self.canvas.axes.plot(_meas.data_bck[:, i], _color + '--')
                self.canvas.axes.set_xlabel('Time [*0.05s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Positioning Error':
                _dir = 'forward'
                if _dir == 'forward':
                    p0 = 0
                    p1 = -180000
                else:
                    p0 = 180000
                    p1 = 0

                self.canvas.axes.plot(p0 - _meas.pos7f[0, :], label='ErA+i')
                self.canvas.axes.plot(p1 - _meas.pos7f[1, :], label='ErA+f')
                self.canvas.axes.plot(p1 - _meas.pos7b[0, :],
                                      '--', label='ErA-i')
                self.canvas.axes.plot(p0 - _meas.pos7b[1, :],
                                      '--', label='ErA-f')
                self.canvas.axes.plot(p0 - _meas.pos8f[0, :], label='ErB+i')
                self.canvas.axes.plot(-1*p1 - _meas.pos8f[1, :], label='ErB+f')
                self.canvas.axes.plot(-1*p1 - _meas.pos8b[0, :],
                                      '--', label='ErB-i')
                self.canvas.axes.plot(p0 - _meas.pos8b[1, :],
                                      '--', label='ErB-f')
                _error_lim = 57*_np.ones(_meas.pos7f.shape[1])
                self.canvas.axes.plot(_error_lim, 'k--')
                self.canvas.axes.plot(-1*_error_lim, 'k--')
                self.canvas.axes.set_xlabel('Measurement #')
                self.canvas.axes.set_ylabel('Position Error [mdeg]')
#                 plt.title('Coil Position Error')
            self.canvas.axes.grid(1)
            self.canvas.axes.legend()
            self.canvas.figure.tight_layout()
            self.canvas.draw()

            _result = '{:.2f} +/- {:.2f}'.format(_meas.I_mean*10**6,
                                                 _meas.I_std*10**6)
            _result_f = '{:.2f} +/- {:.2f}'.format(_meas.If.mean()*10**6,
                                                   _meas.If_std*10**6)
            _result_b = '{:.2f} +/- {:.2f}'.format(_meas.Ib.mean()*10**6,
                                                   _meas.Ib_std*10**6)
            self.ui.le_result.setText(_result)
            self.ui.le_result_f.setText(_result_f)
            self.ui.le_result_b.setText(_result_b)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
