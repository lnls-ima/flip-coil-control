"""Analysis widget for the Flip Coil Control application."""

import os as _os
import sys as _sys
import numpy as _np
import time as _time
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
from flipcoil.gui.utils import (
    get_ui_file as _get_ui_file,
    sleep as _sleep,
    update_db_name_list as _update_db_name_list,
    )

from flipcoil.gui.viewcfgwidget import ViewCfgWidget as _ViewCfgWidget

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
        self.meas_fc = _data.measurement.MeasurementData()
        self.meas_sw = _data.measurement.MeasurementDataSW()

        self.amb_cfg = _data.configuration.MeasurementConfig()
        self.amb_meas_fc = _data.measurement.MeasurementData()
        self.amb_meas_sw = _data.measurement.MeasurementDataSW()

        self.meas = self.meas_sw
        self.amb_meas = self.amb_meas_sw
        self.plot = self.plot_sw

        self.connect_signal_slots()
        self.update_meas_list()

    def init_tab(self):
        self.load_measurement()

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
        self.ui.cmb_meas_name.currentIndexChanged.connect(
            self.load_measurement)
        self.ui.pbt_load_meas.clicked.connect(self.load_measurement)
        self.ui.cmb_plot.currentIndexChanged.connect(self.plot)
        self.ui.pbt_update.clicked.connect(self.update_meas_list)
        self.ui.pbt_viewcfg.clicked.connect(self.view_cfg)
        self.ui.rdb_sw.clicked.connect(self.change_meas_mode)
        self.ui.rdb_fc.clicked.connect(self.change_meas_mode)

    def view_cfg(self):
        try:
            self.viewcfg = _ViewCfgWidget()
            self.viewcfg.show()

            name = self.cfg.name + ' / ' + str(self.cfg.idn)
            self.viewcfg.ui.le_name_id.setText(name)
            self.viewcfg.ui.le_date.setText(self.cfg.date)
            self.viewcfg.ui.le_hour.setText(self.cfg.hour)

            self.viewcfg.ui.sb_frw5.setValue(self.cfg.steps_f[0])
            self.viewcfg.ui.sb_frw6.setValue(self.cfg.steps_f[1])
            self.viewcfg.ui.sb_bck5.setValue(self.cfg.steps_b[0])
            self.viewcfg.ui.sb_bck6.setValue(self.cfg.steps_b[1])

            if self.cfg.direction == 'ccw':
                self.viewcfg.ui.rdb_ccw.setChecked(True)
            else:
                self.viewcfg.ui.rdb_cw.setChecked(True)
            self.viewcfg.ui.dsp_start_pos.setValue(self.cfg.start_pos)  # [deg]
            self.viewcfg.ui.sb_nmeasurements.setValue(self.cfg.nmeasurements)
            self.viewcfg.ui.sb_rot_max_err.setValue(self.cfg.max_init_error)

            self.viewcfg.ui.sb_nplc.setValue(self.cfg.nplc)
            self.viewcfg.ui.dsb_duration.setValue(self.cfg.duration)

            self.viewcfg.ui.dsb_width.setValue(self.cfg.width * 10**3)  # [mm]
            self.viewcfg.ui.sb_turns.setValue(self.cfg.turns)
            self.parent_window.motors.ui.dsb_speed.setValue(self.cfg.speed)  # [rev/s]
            self.parent_window.motors.ui.dsb_accel.setValue(self.cfg.accel)  # [rev/s^2]
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

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
            self.ui.cmb_meas_name.currentIndexChanged.disconnect()
            _update_db_name_list(self.meas, self.ui.cmb_meas_name)
            self.ui.cmb_meas_name.currentIndexChanged.connect(
                self.load_measurement)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def load_measurement(self):
        """Loads selected measurement from database."""
        try:
            if self.ui.rdb_sw.isChecked():
                _first_integral_calculus = self.first_integral_calculus_sw
            else:
                _first_integral_calculus = self.first_integral_calculus
                self.cfg.db_update_database(
                    self.database_name,
                    mongo=self.mongo, server=self.server)
            self.meas.db_update_database(
                self.database_name,
                mongo=self.mongo, server=self.server)
            meas_list = []
            for i in range(self.ui.cmb_meas_name.count()):
                meas_list.append(self.ui.cmb_meas_name.itemText(i))
            meas_name = self.ui.cmb_meas_name.currentText()
            meas_cmb_idx = self.ui.cmb_meas_name.currentIndex()
            if all([meas_list.count(meas_name) > 1,
                    meas_cmb_idx > 0]):
                idx = -1
                for i in range(len(meas_list)):
                    if meas_name == meas_list[i]:
                        idx += 1
            else:
                idx = 0
            _id = self.meas.db_search_field('name', meas_name)[idx]['id']
            self.meas.db_read(_id)
            self.ui.le_comments.setText(self.meas.comments)

            if self.ui.rdb_sw.isChecked():
                self.first_integral_calculus_sw(self.meas)
                self.ui.le_cfg_name.setText('')
            else:
                self.cfg.db_read(self.meas.cfg_id)
                self.first_integral_calculus(cfg=self.cfg, meas=self.meas)

                cfg_name = self.cfg.name + ' / ' + str(self.cfg.idn)
                self.ui.le_cfg_name.setText(cfg_name)

            _QApplication.processEvents()
            self.plot()
#             _QMessageBox.information(self, 'Information',
#                                      'Measurement Loaded.',
#                                      _QMessageBox.Ok)
            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.warning(self, 'Information',
                                 'Failed to load this configuration.',
                                 _QMessageBox.Ok)
            return False

    def change_meas_mode(self):
        """Changes measurement mode to stretched wire (sw) or flip coil (fc)"""
        if self.ui.rdb_sw.isChecked():
            self.meas = self.meas_sw
            self.plot = self.plot_sw
            self.amb_meas = self.amb_meas_sw
        else:
            self.meas = self.meas_fc
            self.plot = self.plot_fc
            self.amb_meas = self.amb_meas_fc

        self.ui.cmb_plot.currentIndexChanged.connect(self.plot)
        self.update_meas_list()

    def first_integral_calculus(self, cfg, meas, fdi_mode=False):
        """Calculates first field integral from raw data.

        Args:
            cfg (MeasurementConfig): measurement configuration;
            meas (MeasurementData): measurement data.

        Returns:
            MeaseurementData instance if the calculations were successfull;
            None otherwise
        """
        try:
            # _width = 12.5e-3  # [m]
            _width = cfg.width
            _turns = cfg.turns  # number of coil turns
            _dt = cfg.nplc/60
            # I = flux/(2*N*width)
            if not fdi_mode:
                for i in range(meas.data_frw.shape[1]):
                    _offset_f = meas.data_frw[:40, i].mean()
                    _offset_b = meas.data_bck[:40, i].mean()
                    _f_f = _np.array([0])
                    _f_b = _np.array([0])
                    for idx in range(meas.data_frw[:, i].shape[0]-1):
                        # dv = ((v[i+1] - v[i])/2)/0.05
                        # f = np.append(f, f[i]+dv)
                        _f_f_part = meas.data_frw[:idx, i] - _offset_f
                        _f_b_part = meas.data_bck[:idx, i] - _offset_b
                        _f_f = _np.append(_f_f, _np.trapz(_f_f_part, dx=_dt))
                        _f_b = _np.append(_f_b, _np.trapz(_f_b_part, dx=_dt))
                    if i == 0:
                        meas.flx_f = _f_f
                        meas.flx_b = _f_b
                    else:
                        meas.flx_f = _np.vstack([meas.flx_f, _f_f])
                        meas.flx_b = _np.vstack([meas.flx_b, _f_b])
                meas.flx_f = meas.flx_f.transpose()
                meas.flx_b = meas.flx_b.transpose()
            else:
                meas.flx_f = _np.copy(meas.data_frw)
                meas.flx_b = _np.copy(meas.data_bck)

            meas.I_f = meas.flx_f * 1/(2*_turns*_width)
            meas.I_b = meas.flx_b * 1/(2*_turns*_width)
            meas.I = (meas.flx_f - meas.flx_b)/2 * 1/(2*_turns*_width)

            meas.If = meas.I_f[61, :] - meas.I_f[40, :]
            meas.If_std = meas.If.std()

            meas.Ib = meas.I_b[61, :] - meas.I_b[40, :]
            meas.Ib_std = meas.Ib.std()

            meas.I_mean = (meas.If.mean() - meas.Ib.mean())/2
            meas.I_std = 1/2*(meas.If_std**2 + meas.Ib_std**2)**0.5

            if meas.Iamb_id > 0:
                self.amb_cfg.db_update_database(
                    self.database_name,
                    mongo=self.mongo, server=self.server)
                self.amb_meas.db_update_database(
                    self.database_name,
                    mongo=self.mongo, server=self.server)

                self.ambient_field_calculus(meas)
            else:
                self.ui.le_Imeas.setText('')
                self.ui.le_Iamb.setText('')
                self.ui.le_Iamb_name.setText('')

            return meas

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def first_integral_calculus_sw(self, meas):
        """Calculates first field integral from stretched wire raw data.

        Args:
            cfg (MeasurementConfig): measurement configuration;
            meas (MeasurementData): measurement data.

        Returns:
            MeaseurementData instance if the calculations were successfull;
            None otherwise
        """
        try:
            # _width = 12.5e-3  # [m]
            _step = meas.step*1e-3  # [m]
            _turns = meas.turns  # number of coil turns
            _dt = meas.nplc/60

            shape = meas.data_frw.shape

            meas.flx_f = _np.zeros(shape)
            meas.flx_b = _np.zeros(shape)
            # I = flux/step

            # data[i, j, k]
            # i: position index
            # j: measurement voltage array index
            # k: measurement number index
            for i in range(shape[0]):
                pos = meas.transversal_pos[i]
#                 _offset_f = meas.data_frw[:40, i].mean()
#                 _offset_b = meas.data_bck[:40, i].mean()

                for k in range(shape[2]):
                    _f_f = _np.array([])
                    _f_b = _np.array([])
                    for idx in range(shape[1]):
                        # dv = ((v[i+1] - v[i])/2)/0.05
                        # f = np.append(f, f[i]+dv)
                        _f_f_part = meas.data_frw[i, :idx, k]  # - _offset_f
                        _f_b_part = meas.data_bck[i, :idx, k]  # - _offset_b
                        _f_f = _np.append(_f_f, _np.trapz(_f_f_part, dx=_dt))
                        _f_b = _np.append(_f_b, _np.trapz(_f_b_part, dx=_dt))
                    if k == 0:
                        flx_f = _f_f
                        flx_b = _f_b
                    else:
                        flx_f = _np.vstack([flx_f, _f_f])
                        flx_b = _np.vstack([flx_b, _f_b])
                meas.flx_f[i] = flx_f.transpose()
                meas.flx_b[i] = flx_b.transpose()

            meas.I_f = meas.flx_f / (_turns * _step)
            meas.I_b = meas.flx_b / (_turns * _step)
            meas.I = (meas.I_f - meas.I_b) / 2

            meas.If = _np.zeros([shape[0], shape[2]])
            meas.If_std = _np.zeros(shape[0])
            meas.Ib = _np.zeros([shape[0], shape[2]])
            meas.Ib_std = _np.zeros(shape[0])
            meas.I_mean = _np.zeros(shape[0])
            meas.I_std = _np.zeros(shape[0])

            for i in range(shape[0]):
                meas.If[i] = meas.I_f[i, 61, :] - meas.I_f[i, 27, :]
                meas.If_std[i] = meas.If[i].std()

                meas.Ib[i] = meas.I_b[i, 61, :] - meas.I_b[i, 27, :]
                meas.Ib_std[i] = meas.Ib[i].std()

                meas.I_mean[i] = (meas.If[i].mean() - meas.Ib[i].mean())/2
                meas.I_std[i] = 1/2 * (meas.If_std[i]**2 + meas.Ib_std[i]**2)**0.5

            if meas.Iamb_id > 0:
                self.amb_meas.db_update_database(
                    self.database_name,
                    mongo=self.mongo, server=self.server)
#
                self.ambient_field_calculus_sw(meas)
#             else:
#                 self.ui.le_Imeas.setText('')
#                 self.ui.le_Iamb.setText('')
#                 self.ui.le_Iamb_name.setText('')
#
#             return meas

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def ambient_field_calculus(self, meas):
        """Discounts ambient field from measurement and prints results."""
        try:
            self.amb_meas.db_read(meas.Iamb_id)
            self.amb_cfg.db_read(self.amb_meas.cfg_id)
            _result = '{:.2f} +/- {:.2f}'.format(meas.I_mean*10**6,
                                                 meas.I_std*10**6)

            meas.I_mean = meas.I_mean - self.amb_meas.I_mean
            meas.I_std = (meas.I_std**2 + self.amb_meas.I_std**2)**0.5

            _result1 = '{:.2f} +/- {:.2f}'.format(self.amb_meas.I_mean*10**6,
                                                  self.amb_meas.I_std*10**6)
            _amb_name = self.amb_meas.name + ' / ' + str(self.amb_meas.idn)

            self.ui.le_Imeas.setText(_result)
            self.ui.le_Iamb.setText(_result1)
            self.ui.le_Iamb_name.setText(_amb_name)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def ambient_field_calculus_sw(self, meas):
        """Discounts ambient field from measurement and prints results."""
        try:
            self.amb_meas.db_read(meas.Iamb_id)
            _result = '{:.2f} +/- {:.2f}'.format(meas.I_mean[0]*10**6,
                                                 meas.I_std[0]*10**6)

            meas.I_mean = meas.I_mean - self.amb_meas.I_mean
            meas.I_std = (meas.I_std**2 + self.amb_meas.I_std**2)**0.5

            _result1 = '{:.2f} +/- {:.2f}'.format(self.amb_meas.I_mean[0]*10**6,
                                                  self.amb_meas.I_std[0]*10**6)
            _amb_name = self.amb_meas.name + ' / ' + str(self.amb_meas.idn)

            self.ui.le_Imeas.setText(_result)
            self.ui.le_Iamb.setText(_result1)
            self.ui.le_Iamb_name.setText(_amb_name)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def plot_sw(self):
        """Plots measurement data.

        Args:
            plot_from_measurementwidget (bool): flag indicating wether to get
            measruement data and configurations from measuerement widget (if
            True) or analysis widget (if False, default)."""
        try:
            _meas = self.meas_sw
            _dt = _meas.nplc/60

            _t = _np.linspace(0, _meas.duration, _meas.I.shape[1])

            self.canvas.axes.cla()
            if self.ui.cmb_plot.currentText() == 'Integrated Field Result':
                for k in range(_meas.I.shape[2]):
                    self.canvas.axes.plot(_t, _meas.I[0, :, k], label=str(k))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Results':
                for k in range(_meas.I_f.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.I_f[0, :, k], _color + '-',
                                          label=str(k))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Backward Results':
                for k in range(_meas.I_b.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.I_b[0, :, k], _color + '-',
                                          label=str(k))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Results':
                for k in range(_meas.I_f.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.I_f[0, :, k], _color + '-',
                                          label=str(k))
                    self.canvas.axes.plot(_t, _meas.I_b[0, :, k], _color + '--')
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Voltage':
                for k in range(_meas.data_frw.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.data_frw[0, :, k],
                                          _color + '-', label=str(k))
                    _std = _meas.data_frw[0, :, k].std()
                    _min = _meas.data_frw[0, :, k].min()
                    _max = _meas.data_frw[0, :, k].max()
                    _vpp = _max - _min
                    print('M{0} std={1:.2E}, min={2:.2E}, '
                          'max={3:.2E}, Vpp={4:.2E}'.format(k, _std, _min,
                                                            _max, _vpp))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Backward Voltage':
                for k in range(_meas.data_bck.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.data_bck[0, :, k],
                                          _color + '-', label=str(k))
                    _std = _meas.data_bck[0, :, k].std()
                    _min = _meas.data_bck[0, :, k].min()
                    _max = _meas.data_bck[0, :, k].max()
                    _vpp = _max - _min
                    print('M{0} std={1:.2E}, min={2:.2E}, '
                          'max={3:.2E}, Vpp={4:.2E}'.format(k, _std, _min,
                                                            _max, _vpp))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Voltage':
                for k in range(_meas.data_frw.shape[2]):
                    _color = 'C' + str(k)
                    self.canvas.axes.plot(_t, _meas.data_frw[0, :, k],
                                          _color + '-', label=str(k))
                    self.canvas.axes.plot(_t, _meas.data_bck[0, :, k],
                                          _color + '--')
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Forward Voltage FFT':
                for k in range(_meas.data_frw.shape[2]):
                    _color = 'C' + str(k)
                    n = _meas.data_frw.shape[1]
                    fft = _np.fft.fft(_meas.data_frw[0, :, k])*2/n
                    freq = _np.fft.fftfreq(n, _dt)
                    self.canvas.axes.plot(freq[:n//2], _np.real(fft[:n//2]),
                                          _color + '-', label=str(k))
                self.canvas.axes.set_xlabel('Frequency [Hz]')
                self.canvas.axes.set_ylabel('Amplitude [V]')

            elif self.ui.cmb_plot.currentText() == 'Backward Voltage FFT':
                for k in range(_meas.data_bck.shape[2]):
                    _color = 'C' + str(k)
                    n = _meas.data_bck.shape[1]
                    fft = _np.fft.fft(_meas.data_bck[0, :, k])*2/n
                    freq = _np.fft.fftfreq(n, _dt)
                    self.canvas.axes.plot(freq[:n//2], _np.real(fft[:n//2]),
                                          _color + '-', label=str(k))
                self.canvas.axes.set_xlabel('Frequency [Hz]')
                self.canvas.axes.set_ylabel('Amplitude [V]')

            self.canvas.axes.grid(1)
            self.canvas.axes.legend()
            self.canvas.figure.tight_layout()
            self.canvas.draw()

            _result = '{:.2f} +/- {:.2f}'.format(_meas.I_mean[0]*10**6,
                                                 _meas.I_std[0]*10**6)
            _result_f = '{:.2f} +/- {:.2f}'.format(_meas.If[0].mean()*10**6,
                                                   _meas.If_std[0]*10**6)
            _result_b = '{:.2f} +/- {:.2f}'.format(_meas.Ib[0].mean()*10**6,
                                                   _meas.Ib_std[0]*10**6)
            self.ui.le_result.setText(_result)
            self.ui.le_result_f.setText(_result_f)
            self.ui.le_result_b.setText(_result_b)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def plot_fc(self):
        """Plots measurement data.

        Args:
            plot_from_measurementwidget (bool): flag indicating wether to get
            measruement data and configurations from measuerement widget (if
            True) or analysis widget (if False, default)."""
        try:
#             if plot_from_measurementwidget:
#                 _meas = self.parent_window.measurement.meas
#                 _cfg = self.parent_window.measurement.cfg
#             else:
            _meas = self.meas
            _cfg = self.cfg
            _dt = _cfg.nplc/60

#             if sw:
#                 _t = _np.linspace(0, _cfg.duration, _meas.I.shape[1])
#             else:
            _t = _np.linspace(0, _cfg.duration, _meas.I.shape[0])

            self.canvas.axes.cla()
            if self.ui.cmb_plot.currentText() == 'Integrated Field Result':
                for i in range(_meas.I.shape[1]):
#                     if sw:
#                         self.canvas.axes.plot(_t, _meas.I[0, :, i], label=str(i))
#                     else:
                    self.canvas.axes.plot(_t, _meas.I[:, i], label=str(i))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Results':
                for i in range(_meas.I_f.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.I_f[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Backward Results':
                for i in range(_meas.I_b.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.I_b[:, i], _color + '-',
                                          label=str(i))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Results':
                for i in range(_meas.I_f.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.I_f[:, i], _color + '-',
                                          label=str(i))
                    self.canvas.axes.plot(_t, _meas.I_b[:, i], _color + '--')
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('First Field Integral [T.m]')

            elif self.ui.cmb_plot.currentText() == 'Forward Voltage':
                for i in range(_meas.data_frw.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.data_frw[:, i],
                                          _color + '-', label=str(i))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Backward Voltage':
                for i in range(_meas.data_bck.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.data_bck[:, i],
                                          _color + '-', label=str(i))
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Forward/Backward Voltage':
                for i in range(_meas.data_frw.shape[1]):
                    _color = 'C' + str(i)
                    self.canvas.axes.plot(_t, _meas.data_frw[:, i],
                                          _color + '-', label=str(i))
                    self.canvas.axes.plot(_t, _meas.data_bck[:, i],
                                          _color + '--')
                self.canvas.axes.set_xlabel('Time [s]')
                self.canvas.axes.set_ylabel('Voltage [V]')

            elif self.ui.cmb_plot.currentText() == 'Positioning Error':
                _dir = 'forward'
                if _dir == 'forward':
                    p0 = 0
                    p1 = -180000
                else:
                    p0 = 180000
                    p1 = 0

#                 #Iy CCW
#                 pos7f = np.array([0, -180000])
#                 pos8f = np.array([0, 180000])
#                 #Iy CW
#                 pos7f = np.array([0, 180000])
#                 pos8f = np.array([0, -180000])
#                 #Ix CW
#                 pos7f = np.array([-90000, 90000])
#                 pos8f = np.array([90000, -90000])
#                 #Ix CCW
#                 pos7f = np.array([-90000, -270000])
#                 pos8f = np.array([90000, 270000])

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
