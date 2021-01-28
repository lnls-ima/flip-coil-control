"""Measurement widget for the Flip Coil Control application."""

import os as _os
import sys as _sys
import numpy as _np
import time as _time
import traceback as _traceback

from qtpy.QtWidgets import (
    QWidget as _QWidget,
    QMessageBox as _QMessageBox,
    QApplication as _QApplication,
    QProgressDialog as _QProgressDialog,
    )
from qtpy.QtCore import Qt as _Qt
import qtpy.uic as _uic

import flipcoil.data as _data
from flipcoil.gui.measurementdialog import MeasurementDialog \
    as _MeasurementDialog
from flipcoil.gui.utils import (
    get_ui_file as _get_ui_file,
    sleep as _sleep,
    )
from flipcoil.devices import (
    ppmac as _ppmac,
    fdi as _fdi,
    ps as _ps,
    volt as _volt,
    )


class MeasurementWidget(_QWidget):
    """Measurement widget class for the Flip Coil Control application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.flag_rm_backlash = True
        self.flag_save = False

        self.cfg = _data.configuration.MeasurementConfig()
        self.meas = _data.measurement.MeasurementData()

        self.update_cfg_list()
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
        self.ui.pbt_measure.clicked.connect(self.measure)
        self.ui.pbt_test.clicked.connect(self.test_steps)
        self.ui.pbt_save_cfg.clicked.connect(self.save_cfg)
        self.ui.pbt_load_cfg.clicked.connect(self.load_cfg)
        self.ui.pbt_update_cfg.clicked.connect(self.update_cfg_list)

    def save_log(self, array, name='', comments=''):
        name = name + _time.strftime('_%y_%m_%d_%H_%M', _time.localtime()) + '.dat'
        head = ('Turn1[V.s]\tTurn2[V.s]\tTurn3[V.s]\tTurn4[V.s]\tTurn5[V.s]\t' + 
                'Turn6[V.s]\tTurn7[V.s]\tTurn8[V.s]\tTurn9[V.s]\tTurn10[V.s]')
        comments = comments + '\n'
        _np.savetxt(name, array, delimiter='\t', comments=comments, header=head)

    def test_steps(self):
        try:
            _start_pos = int(self.ui.dsp_start_pos.value()*10**3)
            _ppmac.remove_backlash(_start_pos)
            _sleep(5)
            _frw_steps = [self.ui.sb_frw5.value(), self.ui.sb_frw6.value()]
            _bck_steps = [self.ui.sb_bck5.value(), self.ui.sb_bck6.value()]

            _ppmac.write('#5j^' + str(_frw_steps[0]) +
                         ';#6j^' + str(_frw_steps[1]))
            _sleep(5)
            pos7f, pos8f = _ppmac.read_motor_pos([7, 8])
            _ppmac.write('#5j^' + str(_bck_steps[0]) +
                         ';#6j^' + str(_bck_steps[1]))
            print(pos7f, pos8f)
            _sleep(5)
            pos7b, pos8b = _ppmac.read_motor_pos([7, 8])
            print(pos7b, pos8b)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_cfg_list(self):
        try:
            self.cfg.db_update_database(
                database_name=self.database_name,
                mongo=self.mongo, server=self.server)
            names = self.cfg.db_get_values('name')

            current_text = self.ui.cmb_cfg_name.currentText()
            self.ui.cmb_cfg_name.clear()
            self.ui.cmb_cfg_name.addItems([name for name in names])
            if len(current_text) == 0:
                self.ui.cmb_cfg_name.setCurrentIndex(
                    self.ui.cmb_cfg_name.count()-1)
            else:
                self.ui.cmb_cfg_name.setCurrentText(current_text)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_cfg_from_ui(self):
        try:
            self.cfg.name = self.ui.cmb_cfg_name.currentText()

            dp5_ida = self.ui.sb_frw5.value()  # -51209
            dp6_ida = self.ui.sb_frw6.value()  # 51170
            dp5_volta = self.ui.sb_bck5.value()  # 51218
            dp6_volta = self.ui.sb_bck6.value()  # -51166
            self.cfg.steps_f = [dp5_ida, dp6_ida]  # steps
            self.cfg.steps_b = [dp5_volta, dp6_volta]  # steps

            self.cfg.direction = (self.ui.rdb_ccw.isChecked() * 'ccw' +
                                  self.ui.rdb_cw.isChecked() * 'cw')
            self.cfg.start_pos = self.ui.dsp_start_pos.value()  # [deg]
            self.cfg.nmeasurements = self.ui.sb_nmeasurements.value()
            self.cfg.max_init_error = self.ui.dsb_max_err.value()

            self.cfg.nplc = self.ui.sb_nplc.value()
            self.cfg.duration = self.ui.dsb_duration.value()

            self.cfg.width = self.ui.dsb_width.value() * 10**-3  # [m]
            self.cfg.turns = self.ui.sb_turns.value()
            self.cfg.speed = self.parent_window.motors.ui.dsb_speed.value()  # [rev/s]
            self.cfg.accel = self.parent_window.motors.ui.dsb_accel.value()  # [rev/s^2]
            self.cfg.jerk = self.parent_window.motors.ui.dsb_jerk.value()

            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def save_cfg(self):
        """Saves current ui configuration into database."""
        try:
            self.update_cfg_from_ui()
            self.cfg.db_update_database(
                        self.database_name,
                        mongo=self.mongo, server=self.server)
            self.cfg.db_save()
            self.update_cfg_list()
            _QMessageBox.information(self, 'Information',
                                     'Configuration Saved.',
                                     _QMessageBox.Ok)
            return True
        except Exception:
            _QMessageBox.warning(self, 'Information',
                                 'Failed to save this configuration.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def load_cfg(self):
        """Load configuration from database."""
        try:
            name = self.ui.cmb_cfg_name.currentText()
            self.cfg.db_update_database(
                self.database_name,
                mongo=self.mongo, server=self.server)
            _id = self.cfg.db_search_field('name', name)[0]['id']
            self.cfg.db_read(_id)
            self.load_cfg_on_ui()
            _QMessageBox.information(self, 'Information',
                                     'Configuration Loaded.',
                                     _QMessageBox.Ok)
            return True
        except Exception:
            _QMessageBox.warning(self, 'Information',
                                 'Failed to load this configuration.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def load_cfg_on_ui(self):
        try:
            self.ui.cmb_cfg_name.setCurrentText(self.cfg.name)

            self.ui.sb_frw5.setValue(self.cfg.steps_f[0])
            self.ui.sb_frw6.setValue(self.cfg.steps_f[1])
            self.ui.sb_bck5.setValue(self.cfg.steps_b[0])
            self.ui.sb_bck6.setValue(self.cfg.steps_b[1])

            if self.cfg.direction == 'ccw':
                self.ui.rdb_ccw.setChecked(True)
            else:
                self.ui.rdb_cw.setChecked(True)
            self.ui.dsp_start_pos.setValue(self.cfg.start_pos)  # [deg]
            self.ui.sb_nmeasurements.setValue(self.cfg.nmeasurements)
            self.ui.dsb_max_err.setValue(self.cfg.max_init_error)

            self.ui.sb_nplc.setValue(self.cfg.nplc)
            self.ui.dsb_duration.setValue(self.cfg.duration)

            self.ui.dsb_width.setValue(self.cfg.width * 10**3)  # [mm]
            self.ui.sb_turns.setValue(self.cfg.turns)
            self.parent_window.motors.ui.dsb_speed.setValue(self.cfg.speed)  # [rev/s]
            self.parent_window.motors.ui.dsb_accel.setValue(self.cfg.accel)  # [rev/s^2]
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def measure(self):
        self.dialog = _MeasurementDialog()
        self.dialog.show()
        self.dialog.accepted.connect(self.measure_first_integral)
        self.dialog.rejected.connect(self.cancel_measurement)

    def cancel_measurement(self):
        self.dialog.destroy()

    def measure_first_integral(self, fdi_mode=False):
        try:
            self.meas.meas_name = self.dialog.ui.cmb_meas_name.currentText()
            self.meas.Iamb = self.ui.chb_Iamb.isChecked()*1
            self.meas.cfg_id = 0

            speed = self.cfg.speed*102.4  # [rev/s]
            start_pos = int(self.cfg.start_pos*10**3)
            ta = -0.4  # acceleration time [ms]
            ts = 0  # jerk time [ms]
            wait = 2000  # time to wait between moves [ms]

            _prg_dialog = _QProgressDialog('Measurement', 'Abort', 0,
                                           self.cfg.nmeasurements + 1, self)
            _prg_dialog.setWindowTitle('Measurement Progress')
            _prg_dialog.setValue(0)
            _prg_dialog.show()
            _QApplication.processEvents()
            data_frw = _np.array([])
            data_bck = _np.array([])
            self.meas.pos7f = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos7b = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos8f = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos8b = _np.zeros((2, self.cfg.nmeasurements))

            _ppmac.write('#1..4k')
            msg = ('startPos=' + str(start_pos) +
                   ';Av=' + str(speed) + ';Aac=' + str(ta) +
                   ';Aj=' + str(ts) + ';wait=' + str(wait))
            _ppmac.write(msg)
            msg = ('Motor[{0}].JogSpeed={1};'
                   'Motor[{0}].JogTa={2};'
                   'Motor[{0}].JogTs={3}'.format(5, speed, ta, ts))
            _ppmac.write(msg)
            msg = ('Motor[{0}].JogSpeed={1};'
                   'Motor[{0}].JogTa={2};'
                   'Motor[{0}].JogTs={3}'.format(6, speed, ta, ts))
            _ppmac.write(msg)

            if fdi_mode:
                counts = _fdi.configure_integrator(time=self.cfg.duration,
                                                   interval=50)
                _fdi.send('INP:COUP DC')
            else:
                counts = int(_np.ceil(3/(self.cfg.nplc/60)))
                _volt.configure_volt(nplc=self.cfg.nplc, time=self.cfg.duration)
            _sleep(0.5)
#             _ppmac.remove_backlash(start_pos)
#             _sleep(10)
            for i in range(self.cfg.nmeasurements):
                if _prg_dialog.wasCanceled():
                    _prg_dialog.destroy()
                    return False

                if (self.flag_rm_backlash and
                    any([abs(_ppmac.read_motor_pos([7])[0]) % 360000 > self.cfg.max_init_error,
                         abs(_ppmac.read_motor_pos([8])[0]) % 360000 > self.cfg.max_init_error])):
                    _ppmac.remove_backlash(start_pos)
                if fdi_mode:
                    _fdi.start_measurement()
                else:
                    _volt.start_measurement()
                _sleep(1)

                self.meas.pos7f[0, i], self.meas.pos8f[0, i] = (
                    _ppmac.read_motor_pos([7, 8]))
                _ppmac.write('#5j^' + str(self.cfg.steps_f[0]) +
                             ';#6j^' + str(self.cfg.steps_f[1]))

                if fdi_mode:
                    while(_fdi.get_data_count() < counts - 1):
                        _sleep(0.1)
                    _data = _fdi.get_data()
                else:
                    _sleep(3)
        #             while(volt.get_data_count() < counts):
        #                 _sleep(0.1)
                    _data = _volt.get_readings_from_memory(5)
                if i == 0:
                    data_frw = _np.append(data_frw, _data)
                else:
                    data_frw = _np.vstack([data_frw, _data])
                self.meas.pos7f[1, i], self.meas.pos8f[1, i] = (
                    _ppmac.read_motor_pos([7, 8]))

                _sleep(10)

                if fdi_mode:
                    _fdi.start_measurement()
                else:
                    _volt.start_measurement()
                _sleep(1)

                self.meas.pos7b[0, i], self.meas.pos8b[0, i] = (
                    _ppmac.read_motor_pos([7, 8]))
                _ppmac.write('#5j^' + str(self.cfg.steps_b[0]) +
                             ';#6j^' + str(self.cfg.steps_b[1]))
                if fdi_mode:
                    while(_fdi.get_data_count() < counts - 1):
                        _sleep(0.1)
                    _data = _fdi.get_data()
                    _fdi.send('INP:COUP GND')
                else:
                    _sleep(3)
        #             while(volt.get_data_count() < counts):
        #                 time.sleep(0.1)
                    _data = _volt.get_readings_from_memory(5)
                if i == 0:
                    data_bck = _np.append(data_bck, _data)
                else:
                    data_bck = _np.vstack([data_bck, _data])
                self.meas.pos7b[1, i], self.meas.pos8b[1, i] = (
                    _ppmac.read_motor_pos([7, 8]))

                _prg_dialog.setValue(i+1)

            self.meas.data_frw = data_frw.transpose()
            self.meas.data_bck = data_bck.transpose()

            if self.flag_save:
                self.save_log(self.meas.data_frw, 'frw', 'Flip Coil')
                self.save_log(self.meas.data_bck, 'bck', 'Flip Coil')
                self.save_log(self.meas.pos7f, 'pos7f')
                self.save_log(self.meas.pos8f, 'pos8f')
                self.save_log(self.meas.pos7b, 'pos7b')
                self.save_log(self.meas.pos8b, 'pos8b')

            _prg_dialog.destroy()
            _QMessageBox.information(self, 'Information',
                                     'Measurement Finished.',
                                     _QMessageBox.Ok)

            self.first_integral_calculus(dt=self.cfg.nplc/60, fdi_mode=fdi_mode)
            return True

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

    def first_integral_calculus(self, dt=2/60, fdi_mode=False):
        # analysis
        try:
            # _width = 12.5e-3  # [m]
            _width = self.cfg.width
            _turns = self.cfg.turns  # number of coil turns
            # I = flux/(2*N*width)
            if not fdi_mode:
                for i in range(self.meas.data_frw.shape[1]):
                    _offset_f = self.meas.data_frw[:40, i].mean()
                    _offset_b = self.meas.data_bck[:40, i].mean()
                    _f_f = _np.array([0])
                    _f_b = _np.array([0])
                    for idx in range(self.meas.data_frw[:, i].shape[0]-1):
                        # dv = ((v[i+1] - v[i])/2)/0.05
                        # f = np.append(f, f[i]+dv)
                        _f_f_part = self.meas.data_frw[:idx, i] - _offset_f
                        _f_b_part = self.meas.data_bck[:idx, i] - _offset_b
                        _f_f = _np.append(_f_f, _np.trapz(_f_f_part, dx=dt))
                        _f_b = _np.append(_f_b, _np.trapz(_f_b_part, dx=dt))
                    if i == 0:
                        self.meas.flx_f = _f_f
                        self.meas.flx_b = _f_b
                    else:
                        self.meas.flx_f = _np.vstack([self.meas.flx_f, _f_f])
                        self.meas.flx_b = _np.vstack([self.meas.flx_b, _f_b])
                self.meas.flx_f = self.meas.flx_f.transpose()
                self.meas.flx_b = self.meas.flx_b.transpose()
            else:
                self.meas.flx_f = _np.copy(self.meas.data_frw)
                self.meas.flx_b = _np.copy(self.meas.data_bck)

            self.meas.I_f = self.meas.flx_f * 1/(2*_turns*_width)
            self.meas.I_b = self.meas.flx_b * 1/(2*_turns*_width)
            self.meas.I = (self.meas.flx_f - self.meas.flx_b)/2 * 1/(2*_turns*_width)

            self.meas.If = self.meas.I_f[61, :] - self.meas.I_f[40, :]
            self.meas.If_std = self.meas.If.std()

            self.meas.Ib = self.meas.I_b[61, :] - self.meas.I_b[40, :]
            self.meas.Ib_std = self.meas.Ib.std()

            self.meas.I_mean = self.meas.I[61, :] - self.meas.I[40, :]
            self.meas.I_std = 1/2*(self.meas.If_std**2 + self.meas.Ib_std**2)**0.5

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False
