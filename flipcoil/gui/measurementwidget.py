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
    update_db_name_list as _update_db_name_list,
    load_db_from_name as _load_db_from_name,
    )
from flipcoil.devices import (
    ppmac as _ppmac,
    fdi as _fdi,
    ps as _ps,
    volt as _volt,
    )
from pywin.framework import startup
from numpy.distutils.system_info import accelerate_info


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

        self.volt = _volt

        self.cfg = _data.configuration.MeasurementConfig()
        self.meas = _data.measurement.MeasurementData()
        self.meas_sw = _data.measurement.MeasurementDataSW()

        self.update_cfg_list()
#         self.load_cfg()
        self.connect_signal_slots()

    def init_tab(self):
        self.motors = self.parent_window.motors
        self.analysis = self.parent_window.analysis
        self.ps = self.parent_window.powersupply

        name = self.ui.cmb_cfg_name.currentText()
        _load_db_from_name(self.cfg, name)
        self.load_cfg_into_ui()

#         self.load_cfg()

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
        self.ui.pbt_measure.clicked.connect(self.meas_dialog)
        self.ui.pbt_test.clicked.connect(self.test_steps)
        self.ui.pbt_save_cfg.clicked.connect(self.save_cfg)
        self.ui.pbt_load_cfg.clicked.connect(self.load_cfg)
        self.ui.pbt_update_cfg.clicked.connect(self.update_cfg_list)

    def save_log(self, array, name='', comments=''):
        """Saves log on file."""
        name = name + _time.strftime('_%y_%m_%d_%H_%M', _time.localtime()) + '.dat'
        head = ('Turn1[V.s]\tTurn2[V.s]\tTurn3[V.s]\tTurn4[V.s]\tTurn5[V.s]\t' + 
                'Turn6[V.s]\tTurn7[V.s]\tTurn8[V.s]\tTurn9[V.s]\tTurn10[V.s]')
        comments = comments + '\n'
        _np.savetxt(name, array, delimiter='\t', comments=comments, header=head)

    def test_steps(self):
        """Tests steps from ui values and prints initial and final positions.
        """
        # Y1/2: CCW/CW M5 (0 a -pi)  M6 (0 a pi)
        # X1/2: CCW/CW M5 (pi/2 a -pi/2) M6 (-pi/2 a pi/2)
        try:
            if self.ui.rdb_sw.isChecked():
                raise RuntimeError

            _start_pos = int(self.ui.dsp_start_pos.value()*10**3)
            _ppmac.remove_backlash(_start_pos)
#             _ppmac.align_motors(interval=3)
            _sleep(5)
            _frw_steps = [self.ui.sb_frw5.value(), self.ui.sb_frw6.value()]
            _bck_steps = [self.ui.sb_bck5.value(), self.ui.sb_bck6.value()]

#             with _ppmac.lock_ppmac:
            self.motors.timer.stop()
            _ppmac.write('#5j^' + str(_frw_steps[0]) +
                         ';#6j^' + str(_frw_steps[1]))
            _sleep(5)
            pos7f, pos8f = _ppmac.read_motor_pos([7, 8])
#             with _ppmac.lock_ppmac:
            _ppmac.write('#5j^' + str(_bck_steps[0]) +
                         ';#6j^' + str(_bck_steps[1]))
            print(pos7f, pos8f)
            _sleep(5)
            pos7b, pos8b = _ppmac.read_motor_pos([7, 8])
            print(pos7b, pos8b)
            self.motors.timer.start(1000)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.motors.timer.start(1000)

    def update_cfg_list(self):
        """Updates configuration name list in combobox."""
        try:
            _update_db_name_list(self.cfg, self.ui.cmb_cfg_name)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_cfg_from_ui(self):
        """Updates current measurement configuration from ui widgets.

        Returns:
            True if successfull;
            False otherwise."""
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
            self.cfg.max_init_error = (
                self.motors.ui.sb_rot_max_err.value())

            self.cfg.nplc = self.ui.dsb_nplc.value()
            self.cfg.duration = self.ui.dsb_duration.value()

            self.cfg.width = self.ui.dsb_width.value() * 10**-3  # [m]
            self.cfg.turns = self.ui.sb_turns.value()
            self.cfg.speed = self.motors.ui.dsb_speed.value()  # [turns/s]
            self.cfg.accel = self.motors.ui.dsb_accel.value()  # [turns/s^2]
            self.cfg.jerk = self.motors.ui.dsb_jerk.value()  # [turns/s^3]

            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

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
            self.load_cfg_into_ui()
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

    def load_cfg_into_ui(self):
        """Loads database configuration into ui widgets."""
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
            self.motors.ui.sb_rot_max_err.setValue(
                self.cfg.max_init_error)

            self.ui.dsb_nplc.setValue(self.cfg.nplc)
            self.ui.dsb_duration.setValue(self.cfg.duration)

            self.ui.dsb_width.setValue(self.cfg.width * 10**3)  # [mm]
            self.ui.sb_turns.setValue(self.cfg.turns)
            self.motors.ui.dsb_speed.setValue(self.cfg.speed)  # [rev/s]
            self.motors.ui.dsb_accel.setValue(self.cfg.accel)  # [rev/s^2]
            self.motors.ui.dsb_jerk.setValue(self.cfg.jerk)  # [rev/s^3]
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def meas_dialog(self):
        """Creates measurement dialog."""
        self.dialog = _MeasurementDialog()
        self.dialog.show()
        self.dialog.accepted.connect(self.start_measurement)
        self.dialog.rejected.connect(self.cancel_measurement)

        if self.ui.rdb_sw.isChecked():
            _meas = self.meas_sw
        else:
            _meas = self.meas

        try:
            _meas.db_update_database(self.database_name, mongo=self.mongo,
                                         server=self.server)
            last_id = _meas.db_get_last_id()
            name = '_'.join(
                _meas.db_get_value('name', last_id).split('_')[:1])
            self.dialog.ui.le_meas_name.setText(name)

            comments = _meas.db_get_value('comments', last_id)
            self.dialog.ui.le_comments.setText(comments)
#             _update_db_name_list(self.meas, self.dialog.ui.cmb_meas_name)
#             self.meas.db_update_database(database_name=self.database_name,
#                                          mongo=self.mongo, server=self.server)
#             _idn = self.meas.db_get_last_id()
#             if _idn > 0:
#                 _comments = self.meas.db_get_value('comments', _idn)
#                 self.dialog.ui.te_comments.setText(_comments)
            self.update_iamb_list()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_iamb_list(self):
        """Updates Iamb list on measurement dialog."""
        if self.ui.rdb_sw.isChecked():
            _meas = self.meas_sw
        else:
            _meas = self.meas

        _meas.db_update_database(
            self.database_name,
            mongo=self.mongo, server=self.server)

        self.dialog.amb_list = _meas.db_search_field('Iamb_id', 0)
        self.dialog.ui.cmb_Iamb.addItems(
            [item['name'] for item in self.dialog.amb_list])
        self.dialog.ui.cmb_Iamb.setCurrentIndex(len(self.dialog.amb_list)-1)

    def cancel_measurement(self):
        """Cancels measurement and destroys measurement dialog."""
        self.dialog.destroy()

    def start_measurement(self):
        """Starts measurement or scan according to configurations. If number
        of measurements > 1, each step in a scan will be repeated before
        changing the setpoint."""

        try:
            self.update_cfg_from_ui()
            _ppmac.flag_abort = False
            if self.ui.rdb_sw.isChecked():
                _meas = self.meas_sw
                _meas.mode = 'sw'
                _measure_first_integral = self.measure_first_intgral_sw

                _meas.motion_axis = self.ui.cmb_motion_axis.currentText()
                _meas.start_pos = self.ui.dsb_scan_start.value()  # [mm]
                _meas.end_pos = self.ui.dsb_scan_end.value()  # [mm]
                _meas.step = self.ui.dsb_scan_step.value()  # [mm]
            else:
                _meas = self.meas
                _meas.mode = 'fc'
                _measure_first_integral = self.measure_first_intgral

            scan_flag = self.dialog.ui.chb_scan.isChecked()
            repeats = self.dialog.ui.sb_repetitions.value()
            _meas.turns = self.ui.sb_turns.value()
            _meas.nplc = self.ui.dsb_nplc.value()
            _meas.duration = self.ui.dsb_duration.value()
            _meas.nmeasurements = self.ui.sb_nmeasurements.value()

            if not scan_flag:
                # update meas.name and meas.comments
                _meas.comments = self.dialog.ui.le_comments.text()

                # measure
#                 if self.ui.rdb_sw.isChecked():
#                     raise RuntimeError

                for i in range(repeats):
                    if _ppmac.flag_abort:
                        _QMessageBox.information(self, 'Warning',
                                                 'Measurement Aborted.',
                                                 _QMessageBox.Ok)
                        return False
                    name = self.dialog.ui.le_meas_name.text()
                    if _meas.mode == 'fc':
                        name = (name + '_' + self.cfg.direction +
                                _time.strftime('_%y%m%d_%H%M'))
                    else:
                        name = (name + _time.strftime('_%y%m%d_%H%M'))
                    _meas.name = name
                    _meas.hour = _time.strftime('%H:%M:%S')
                    _measure_first_integral()

            if scan_flag:
                param = self.dialog.ui.cmb_scan_param.currentText()
                start = self.dialog.ui.dsb_scan_start.value()
                end = self.dialog.ui.dsb_scan_end.value()
                step = self.dialog.ui.dsb_scan_step.value()
                if step == 0:
                    n_steps = 1
                else:
                    # number of steps
                    n_steps = int(1 + _np.ceil((end-start)/step))

#                 if _meas.mode == 'sw':
#                     _meas.comments = self.dialog.ui.le_comments.text()
#                     name = (self.dialog.ui.le_meas_name.text() +
#                             _time.strftime('_%y%m%d_%H%M'))
#                     _meas.name = name
#                     _meas.hour = _time.strftime('%H:%M:%S')
# 
#                     _measure_first_integral()
#                     _QMessageBox.information(self, 'Information',
#                                              'Measurement Finished.',
#                                              _QMessageBox.Ok)
#                     return True

                # get previous parameter
                if 'X' in param:
                    if _meas.mode == 'sw' and _meas.motion_axis == 'X':
                        _QMessageBox.information(self, 'Warning',
                                                 'Motion axis and scan axis '
                                                 'must not be the same.\n'
                                                 'Measurement Aborted.',
                                                 _QMessageBox.Ok)
                        return False
                    previous_param = self.motors.ui.dsb_pos_x.value()
                elif 'Y' in param:
                    if _meas.mode == 'sw' and _meas.motion_axis == 'Y':
                        _QMessageBox.information(self, 'Warning',
                                                 'Motion axis and scan axis '
                                                 'must not be the same.\n'
                                                 'Measurement Aborted.',
                                                 _QMessageBox.Ok)
                        return False
                    previous_param = self.motors.ui.dsb_pos_y.value()
                elif 'Speed' in param:
                    previous_param = self.cfg.speed
                elif 'Acceleration' in param:
                    previous_param = self.cfg.accel
                elif 'Jerk' in param:
                    previous_param = self.cfg.jerk

                for i in range(n_steps):
                    if _ppmac.flag_abort:
                        _QMessageBox.information(self, 'Warning',
                                                 'Measurement Aborted.',
                                                 _QMessageBox.Ok)
                        return False
                    # change setpoint
                    setpoint = start + i * step
                    if i == n_steps - 1:
                        setpoint = end

                    if 'X' in param:
                        p_str = '_X={0:.2f}_'.format(setpoint)
                        _x_lim = [self.motors.ui.dsb_min_x.value()*10**3,
                                  self.motors.ui.dsb_max_x.value()*10**3]
                        if _x_lim[0] <= setpoint <= _x_lim[1]:
                            self.motors.ui.dsb_pos_x.setValue(setpoint)
                            self.motors.move_xy()
                            _sleep(10)
                        else:
                            _QMessageBox.information(self, 'Warning',
                                                     'X out of range.',
                                                     _QMessageBox.Ok)
                            raise ValueError
                    elif 'Y' in param:
                        p_str = '_Y={0:.2f}_'.format(setpoint)
                        _y_lim = [self.motors.ui.dsb_min_y.value()*10**3,
                                  self.motors.ui.dsb_max_y.value()*10**3]
                        if _y_lim[0] <= setpoint <= _y_lim[1]:
                            self.motors.ui.dsb_pos_y.setValue(setpoint)
                            self.motors.move_xy()
                            _sleep(10)
                        else:
                            _QMessageBox.information(self, 'Warning',
                                                     'Y out of range.',
                                                     _QMessageBox.Ok)
                            raise ValueError
                    elif 'Speed' in param:
                        p_str = '_Spd={0:.2f}_'.format(setpoint)
                        self.cfg.speed = setpoint
                    elif 'Acceleration' in param:
                        p_str = '_Acc={0:.2f}_'.format(setpoint)
                        self.cfg.accel = setpoint
                    elif 'Jerk' in param:
                        p_str = '_Jrk={0:.2f}_'.format(setpoint)
                        self.cfg.jerk = setpoint
                    elif 'Current' in param:
                        p_str = '_I={0:.2f}_'.format(setpoint)
                        if self.ps.ps.read_ps_onoff():
                            self.ps.ui.dsb_current_setpoint.setValue(setpoint)
                            _min = self.ps.cfg.min_current
                            _max = self.ps.cfg.max_current
                            if _min <= setpoint <= _max:
                                self.ps.ps.set_slowref(setpoint)
                                _sleep(10)
                            else:
                                _QMessageBox.information(self, 'Warning',
                                                         'Current out of '
                                                         'range.',
                                                         _QMessageBox.Ok)
                                raise ValueError
                        else:
                            _QMessageBox.information(self, 'Warning',
                                                     'Power supply is'
                                                     ' turned off.',
                                                     _QMessageBox.Ok)
                            return False

                    # update meas.name, meas.comments:
                    comments = self.dialog.ui.le_comments.text()
                    comments = comments + ' Scan: ' + p_str.strip('_') + '.'
                    _meas.comments = comments

                    # measure
                    for i in range(repeats):
                        name = self.dialog.ui.le_meas_name.text()
                        name = (name + '_' + self.cfg.direction + p_str +
                                _time.strftime('_%y%m%d_%H%M'))
                        _meas.hour = _time.strftime('%H:%M:%S')
                        _meas.name = name

                        _measure_first_integral()

                # set previous parameter
#                 if 'X' in param:
#                     self.motors.ui.dsb_pos_x.setValue(previous_param)
#                 elif 'Y' in param:
#                     self.motors.ui.dsb_pos_y.setValue(previous_param)
                if 'Speed' in param:
                    self.cfg.speed = previous_param
                elif 'Acceleration' in param:
                    self.cfg.accel = previous_param
                elif 'Jerk' in param:
                    self.cfg.jerk = previous_param
                elif 'Current' in param:
                    self.ps.ui.dsb_current_setpoint.setValue(setpoint)
                    self.ps.ps.set_slowref(setpoint)
                    _sleep(5)
                    self.ps.ps.turn_off()

            _QMessageBox.information(self, 'Information',
                                     'Measurement Finished.',
                                     _QMessageBox.Ok)
            return True

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.information(self, 'Warning',
                                     'Measurement Failed.',
                                     _QMessageBox.Ok)
            return False

    def measure_first_intgral_sw(self):
        """Runs first field integral measurement in stretched wire mode."""
        try:
            _meas = self.meas_sw
            if self.dialog.ui.chb_Iamb.isChecked():
                self.meas_sw.Iamb_id = 0
            else:
                _id = self.dialog.ui.cmb_Iamb.currentIndex()
                self.meas_sw.Iamb_id = self.dialog.amb_list[_id]['id']
#             turns = self.ui.sb_turns.value()
#             nplc = self.ui.dsb_nplc.value()
#             duration = self.ui.dsb_duration.value()
#             nmeasurements = self.ui.sb_nmeasurements.value()
#             self.meas.cfg_id = self.ui.cmb_cfg_name.currentIndex() + 1
            ##Teste manual
#             start = self.dialog.ui.dsb_scan_start.value()  # [mm]
#             end = self.dialog.ui.dsb_scan_end.value()  # [mm]
#             step = self.dialog.ui.dsb_scan_step.value()  # [mm]
#             param = self.dialog.ui.cmb_scan_param.currentText()
#             self.meas_sw.mode = 'sw'
#             self.meas_sw.turns = turns
            motion_axis = self.meas_sw.motion_axis
            nmeasurements = self.meas_sw.nmeasurements
            nplc = self.meas_sw.nplc
            duration = self.meas_sw.duration
            start = self.meas_sw.start_pos
            end = self.meas_sw.end_pos
            step = self.meas_sw.step

            # PPMAC configurations
            ppmac_cfg = self.motors.cfg
            if motion_axis == 'X':
                speed = ppmac_cfg.speed_x  # [mm/s]
                accel = ppmac_cfg.accel_x  # [mm/s^2]
                jerk = ppmac_cfg.jerk_x  # [mm/s^3]
                _ppmac.write('#2,4,5,6k')
                _ppmac.write('#1,3j/')
                move_axis = self.motors.move_x
            elif motion_axis == 'Y':
                speed = ppmac_cfg.speed_y  # [mm/s]
                accel = ppmac_cfg.accel_y  # [mm/s^2]
                jerk = ppmac_cfg.jerk_y  # [mm/s^3]
                _ppmac.write('#1,3,5,6k')
                _ppmac.write('#2,4j/')
                move_axis = self.motors.move_y
            self.motors.configure_ppmac()

            self.meas_sw.speed = speed
            self.meas_sw.accel = accel
            self.meas_sw.jerk = jerk

            if end < start:
                _QMessageBox.information(self, 'Warning',
                                         'End position should be greater than '
                                         'start position.\n'
                                         'Measurement Aborted.',
                                         _QMessageBox.Ok)
                return False
            elif start == end:
                n_steps = 1
                self.meas_sw.transversal_pos = _np.array([start])
            else:
                if (end - start) < step:
                    self.meas_sw.transversal_pos = _np.array([start, end])
                else:
                    # number of steps
                    n_steps = int(1 + _np.ceil((end-start) / step))
                    # warning if n_steps is not an integer?
                    # check if start and end pos are inside limits
                    self.meas_sw.transversal_pos = _np.linspace(start, end,
                                                                n_steps)

            _prg_dialog = _QProgressDialog('Measurement', 'Abort', 0,
                                           nmeasurements + 1, self)
            _prg_dialog.setWindowTitle('Measurement Progress')
            _prg_dialog.show()
            _QApplication.processEvents()

            data_frw = []
            data_bck = []

            self.motors.timer.stop()

            _sleep(1)

            counts = int(_np.ceil(3/(self.meas_sw.nplc/60)))
            _volt.configure_volt(nplc=nplc, time=duration)
            _sleep(0.5)

            _prg_dialog.setValue(0)

            for pos in self.meas_sw.transversal_pos:
                _init_pos = pos - step/2  # [mm]
                _end_pos = pos + step/2  # [mm]
                data_frw_aux = _np.array([])
                data_bck_aux = _np.array([])

                for i in range(self.meas_sw.nmeasurements):
                    if _prg_dialog.wasCanceled():
                        _prg_dialog.destroy()
                        _ppmac.flag_abort = True
                        return False

                    # Forward measurement
                    # go to init pos
                    move_axis(_init_pos)
                    _sleep(3)  # wait vibrations damping
                    _volt.start_measurement()
                    _t0 = _time.time()
                    _sleep(1)
                    # move step
                    move_axis(_end_pos)
                    _sleep(3)

                    if _time.time() - _t0 <= duration + 1:
                        _sleep(duration + 1 + _t0 - _time.time())

                    _data = _volt.get_readings_from_memory(5)[::-1]
                    if i == 0:
                        data_frw_aux = _np.append(data_frw_aux, _data)
                    else:
                        data_frw_aux = _np.vstack([data_frw_aux, _data])

                    _sleep(3)

                    # Backward measurement
                    _volt.start_measurement()
                    _t0 = _time.time()
                    _sleep(1)
                    # move - step
                    move_axis(_init_pos)
                    _sleep(3)

                    if _time.time() - _t0 <= duration + 1:
                        _sleep(duration + 1 + _t0 - _time.time())

                    _data = _volt.get_readings_from_memory(5)[::-1]

                    if i == 0:
                        data_bck_aux = _np.append(data_bck_aux, _data)
                    else:
                        data_bck_aux = _np.vstack([data_bck_aux, _data])
                    _prg_dialog.setValue(i+1)

                data_frw.append(data_frw_aux.transpose())
                data_bck.append(data_bck_aux.transpose())

            # data[i, j, k]
            # i: position index
            # j: measurement voltage array index
            # k: measurement number index
            self.meas_sw.data_frw = _np.array(data_frw)
            self.meas_sw.data_bck = _np.array(data_bck)

            # data analisys
            self.analysis.first_integral_calculus_sw(self.meas_sw)
            self.save_sw_measurement()
            self.analysis.update_meas_list()
            _count = self.analysis.cmb_meas_name.count() - 1
            self.analysis.cmb_meas_name.setCurrentIndex(_count)

            self.motors.timer.start(1000)
            _prg_dialog.destroy()
            return True

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.information(self, 'Warning',
                                     'Measurement Failed.',
                                     _QMessageBox.Ok)
            self.motors.timer.start(1000)
            return False

    def measure_first_integral(self, fdi_mode=False):
        """Runs first field integral measurement.

        Returns:
            True if successfull;
            False otherwise.
        """
        try:
#             _ppmac.flag_abort = False
#             self.update_cfg_from_ui()

#             self.meas.comments = self.dialog.ui.te_comments.toPlainText()
            if self.dialog.ui.chb_Iamb.isChecked():
                self.meas.Iamb_id = 0
            else:
                _id = self.dialog.ui.cmb_Iamb.currentIndex()
                self.meas.Iamb_id = self.dialog.amb_list[_id]['id']
            self.meas.cfg_id = self.ui.cmb_cfg_name.currentIndex() + 1

            ppmac_cfg = self.motors.cfg
            speed = self.cfg.speed * ppmac_cfg.steps_per_turn * 10**-3  # [turns/s]
            if self.cfg.accel != 0:
                ta = -1/self.cfg.accel * 1/ppmac_cfg.steps_per_turn * 10**6  # [turns/s^2]
            else:
                ta = 0
            if self.cfg.jerk != 0:
                ts = -1/self.cfg.jerk * 1/ppmac_cfg.steps_per_turn * 10**9  # [turns/s^3]
            else:
                ts = 0
            start_pos = int(self.cfg.start_pos*10**3)
#             ta = -0.4  # acceleration time [ms]
#             ts = 0  # jerk time [ms]
#             wait = 2000  # time to wait between moves [ms]
            _dir = 1 if self.cfg.direction == 'ccw' else -1

            _prg_dialog = _QProgressDialog('Measurement', 'Abort', 0,
                                           self.cfg.nmeasurements + 1, self)
            _prg_dialog.setWindowTitle('Measurement Progress')
            _prg_dialog.show()
            _QApplication.processEvents()

            data_frw = _np.array([])
            data_bck = _np.array([])
            self.meas.pos7f = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos7b = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos8f = _np.zeros((2, self.cfg.nmeasurements))
            self.meas.pos8b = _np.zeros((2, self.cfg.nmeasurements))

#             auto_current = self.dialog.ui.chb_auto_current.isChecked()
#             if auto_current:
#                 currents = _np.copy(
#                     self.ps.cfg.current_array)
#                 if len(currents) == 0:
#                     auto_current = False

#             with _ppmac.lock_ppmac:
            self.motors.timer.stop()
            _ppmac.write('#1..4k')
            _sleep(1)
            self.meas.x_pos = (_ppmac.read_motor_pos([1, 3]) *
                               self.motors.x_sf)
            self.meas.y_pos = (_ppmac.read_motor_pos([2, 4]) *
                               self.motors.y_sf)

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
#             self.meas.name = (self.dialog.ui.le_meas_name.currentText() +
#                               _time.strftime('_%y%m%d_%H%M'))
            _prg_dialog.setValue(0)
            for i in range(self.cfg.nmeasurements):
                if _prg_dialog.wasCanceled():
                    _prg_dialog.destroy()
                    _ppmac.flag_abort = True
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
#                 with _ppmac.lock_ppmac:
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

                _sleep(5)

                if fdi_mode:
                    _fdi.start_measurement()
                else:
                    _volt.start_measurement()
                _sleep(1)

                self.meas.pos7b[0, i], self.meas.pos8b[0, i] = (
                    _ppmac.read_motor_pos([7, 8]))
#                 with _ppmac.lock_ppmac:
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

            _meas = self.analysis.first_integral_calculus(
                cfg=self.cfg, meas=self.meas)
            if _meas is not None:
                self.meas = _meas
            else:
                _QMessageBox.warning(self, 'Warning',
                                     'Calculations failed.',
                                     _QMessageBox.Ok)
                return False
            self.save_measurement()
            self.analysis.update_meas_list()
            _count = self.analysis.cmb_meas_name.count() - 1
            self.analysis.cmb_meas_name.setCurrentIndex(_count)
#             self.analysis.plot(plot_from_measurementwidget=True)

            self.motors.timer.start(1000)
            _prg_dialog.destroy()
            return True

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.information(self, 'Warning',
                                     'Measurement Failed.',
                                     _QMessageBox.Ok)
            self.motors.timer.start(1000)
            return False

    def save_measurement(self):
        """Saves current measurement into database."""
        try:
            self.meas.db_update_database(
                        self.database_name,
                        mongo=self.mongo, server=self.server)
            self.meas.db_save()
            self.analysis.update_meas_list()
            return True
        except Exception:
            _QMessageBox.warning(self, 'Information',
                                 'Failed to save this measurement.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False

    def save_sw_measurement(self):
        """Saves current measurement into database."""
        try:
            self.meas_sw.db_update_database(
                        self.database_name,
                        mongo=self.mongo, server=self.server)
            self.meas_sw.db_save()
#             self.analysis.update_meas_list()
            return True
        except Exception:
            _QMessageBox.warning(self, 'Information',
                                 'Failed to save this measurement.',
                                 _QMessageBox.Ok)
            _traceback.print_exc(file=_sys.stdout)
            return False
