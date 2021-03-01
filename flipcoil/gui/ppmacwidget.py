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
    update_db_name_list as _update_db_name_list,
    load_db_from_name as _load_db_from_name,
    )
from flipcoil.devices import ppmac as _ppmac
import flipcoil.data as _data


class PpmacWidget(_QWidget):
    """PPMAC widget class for the Flip Coil Control application."""

    def __init__(self, parent=None):
        """Set up the ui."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.x_sf = 2e-8  # meters/count
        self.y_sf = 2e-8  # meters/count

        self.angular_sf = 1e-3  # deg/count

        self.steps_per_turn = 102400  # roation motor steps/turn

        self.timer = _QTimer()
        self.timer.start(1000)

        self.ppmac = _ppmac
        self.cfg = _data.configuration.PpmacConfig()

        self.update_cfg_list()
#         self.load_cfg()
        self.update_cfg_from_ui()
        self.connect_signal_slots()

    def init_tab(self):
        name = self.ui.cmb_cfg_name.currentText()
        _load_db_from_name(self.cfg, name)
        self.load_cfg_into_ui()

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
        self.ui.timer.timeout.connect(self.update_position)
        self.ui.pbt_move.clicked.connect(self.move)
        self.ui.pbt_move_xy.clicked.connect(self.move_xy)
        self.ui.pbt_home.clicked.connect(self.home)
        self.ui.pbt_home_x.clicked.connect(self.home_x)
        self.ui.pbt_home_y.clicked.connect(self.home_y)
        self.ui.pbt_configure.clicked.connect(self.configure_ppmac)
        self.ui.pbt_save_cfg.clicked.connect(self.save_cfg)
        self.ui.pbt_load_cfg.clicked.connect(self.load_cfg)
        self.ui.pbt_update_cfg.clicked.connect(self.update_cfg_list)

    def update_position(self):
        """Updates position displays on ui."""
        try:
            if hasattr(_ppmac, 'ppmac'):
                if all([not _ppmac.ppmac.closed,
                        self.parent().currentWidget() == self]):
                    self.pos = _ppmac.read_motor_pos([1, 2, 3, 4, 7, 8])
                    self.ui.lcd_pos1.display(self.pos[0]*self.cfg.x_sf*10**3)
                    self.ui.lcd_pos2.display(self.pos[1]*self.cfg.y_sf*10**3)
                    self.ui.lcd_pos3.display(self.pos[2]*self.cfg.x_sf*10**3)
                    self.ui.lcd_pos4.display(self.pos[3]*self.cfg.y_sf*10**3)
                    self.ui.lcd_pos5.display(self.pos[4]*self.angular_sf)
                    self.ui.lcd_pos6.display(self.pos[5]*self.angular_sf)
                    _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

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
            self.cfg.speed = self.ui.dsb_speed.value()
            self.cfg.accel = self.ui.dsb_accel.value()
            self.cfg.jerk = self.ui.dsb_jerk.value()
            self.cfg.rot_sf = self.ui.dsb_rot_sf.value()
            self.cfg.rot_max_err = self.ui.sb_rot_max_err.value()
            self.cfg.steps_per_turn = self.ui.sb_steps_per_turn.value()
            self.cfg.home_offset5 = self.ui.sb_home_offset5.value()
            self.cfg.home_offset6 = self.ui.sb_home_offset6.value()

            self.cfg.pos_x = self.ui.dsb_pos_x.value()
            self.cfg.speed_x = self.ui.dsb_speed_x.value()
            self.cfg.accel_x = self.ui.dsb_accel_x.value()
            self.cfg.jerk_x = self.ui.dsb_jerk_x.value()
            self.cfg.min_x = self.ui.dsb_min_x.value()
            self.cfg.max_x = self.ui.dsb_max_x.value()
            self.cfg.x_sf = self.ui.dsb_x_sf.value()
            self.cfg.home_offset1 = self.ui.sb_home_offset1.value()
            self.cfg.home_offset3 = self.ui.sb_home_offset3.value()

            self.cfg.pos_y = self.ui.dsb_pos_y.value()
            self.cfg.speed_y = self.ui.dsb_speed_y.value()
            self.cfg.accel_y = self.ui.dsb_accel_y.value()
            self.cfg.jerk_y = self.ui.dsb_jerk_y.value()
            self.cfg.min_y = self.ui.dsb_min_y.value()
            self.cfg.max_y = self.ui.dsb_max_y.value()
            self.cfg.y_sf = self.ui.dsb_y_sf.value()
            self.cfg.home_offset2 = self.ui.sb_home_offset2.value()
            self.cfg.home_offset4 = self.ui.sb_home_offset4.value()

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
            self.ui.dsb_speed.setValue(self.cfg.speed)
            self.ui.dsb_accel.setValue(self.cfg.accel)
            self.ui.dsb_jerk.setValue(self.cfg.jerk)
            self.ui.dsb_rot_sf.setValue(self.cfg.rot_sf)
            self.ui.sb_rot_max_err.setValue(self.cfg.rot_max_err)
            self.ui.sb_steps_per_turn.setValue(self.cfg.steps_per_turn)
            self.ui.sb_home_offset5.setValue(self.cfg.home_offset5)
            self.ui.sb_home_offset6.setValue(self.cfg.home_offset6)

            self.ui.dsb_pos_x.setValue(self.cfg.pos_x)
            self.ui.dsb_speed_x.setValue(self.cfg.speed_x)
            self.ui.dsb_accel_x.setValue(self.cfg.accel_x)
            self.ui.dsb_jerk_x.setValue(self.cfg.jerk_x)
            self.ui.dsb_min_x.setValue(self.cfg.min_x)
            self.ui.dsb_max_x.setValue(self.cfg.max_x)
            self.ui.dsb_x_sf.setValue(self.cfg.x_sf)
            self.ui.sb_home_offset1.setValue(self.cfg.home_offset1)
            self.ui.sb_home_offset3.setValue(self.cfg.home_offset3)

            self.ui.dsb_pos_y.setValue(self.cfg.pos_y)
            self.ui.dsb_speed_y.setValue(self.cfg.speed_y)
            self.ui.dsb_accel_y.setValue(self.cfg.accel_y)
            self.ui.dsb_jerk_y.setValue(self.cfg.jerk_y)
            self.ui.dsb_min_y.setValue(self.cfg.min_y)
            self.ui.dsb_max_y.setValue(self.cfg.max_y)
            self.ui.dsb_y_sf.setValue(self.cfg.y_sf)
            self.ui.sb_home_offset2.setValue(self.cfg.home_offset2)
            self.ui.sb_home_offset4.setValue(self.cfg.home_offset4)
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def configure_ppmac(self):
        """Configures PPMAC motor parameters using ui values."""
        try:
            self.update_cfg_from_ui()

            _spd = self.cfg.speed * self.steps_per_turn * 10**-3  # [turns/s]
            if self.cfg.accel != 0:
                _ta = -1/self.cfg.accel * 1/self.steps_per_turn * 10**6  # [turns/s^2]
            else:
                _ta = 0
            if self.cfg.jerk != 0:
                _ts = -1/self.cfg.jerk * 1/self.steps_per_turn * 10**9  # [turns/s^3]
            else:
                _ts = 0

            _spd_x = self.cfg.speed_x / self.cfg.x_sf * 10**-3
            if self.cfg.accel_x != 0:
                _ta_x = (-1/self.cfg.accel_x)*self.cfg.x_sf*10**6
            else:
                _ta_x = 0
            if self.cfg.jerk_x != 0:
                _ts_x = (-1/self.cfg.jerk_x)*self.cfg.x_sf*10**9
            else:
                _ts_x = 0

            _spd_y = self.cfg.speed_y / self.cfg.y_sf * 10**-3
            if self.cfg.accel_y != 0:
                _ta_y = (-1/self.cfg.accel_y)*self.cfg.y_sf*10**6
            else:
                _ta_y = 0
            if self.cfg.jerk_y != 0:
                _ts_y = (-1/self.cfg.jerk_y)*self.cfg.y_sf*10**9
            else:
                _ta_y = 0

            self.timer.stop()
            # Configures rotation motors:
            for i in [5, 6]:
                if i == 5:
                    _home_offset = self.cfg.home_offset5
                else:
                    _home_offset = self.cfg.home_offset6
                msg = ('Motor[{0}].JogSpeed={1};'
                       'Motor[{0}].JogTa={2};'
                       'Motor[{0}].JogTs={3};'
                       'Motor[{0}].HomeOffset={4}'.format(i, _spd, _ta, _ts,
                                                          _home_offset))
#                 with _ppmac.lock_ppmac:
                _ppmac.write(msg)

            # Configures X motors:
            for i in [1, 3]:
                msg = ('Motor[{0}].JogSpeed={1};'
                       'Motor[{0}].JogTa={2};'
                       'Motor[{0}].JogTs={3}'.format(i, _spd_x, _ta_x, _ts_x))
#                 with _ppmac.lock_ppmac:
                _ppmac.write(msg)

            # Configures Y motors:
            for i in [2, 4]:
                msg = ('Motor[{0}].JogSpeed={1};'
                       'Motor[{0}].JogTa={2};'
                       'Motor[{0}].JogTs={3}'.format(i, _spd_x, _ta_x, _ts_x))
#                 with _ppmac.lock_ppmac:
                _ppmac.write(msg)
                self.timer.start(1000)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)

    def home(self):
        """Home rotation motors.

        Returns:
            True if successfull;
            False otherwise."""
        try:
            self.timer.stop()
            _home5 = self.cfg.home_offset5
            _home6 = self.cfg.home_offset6
            _msg = 'Motor[7].HomeOffset={0};Motor[8].HomeOffset={1}'.format(
                _home5, _home6)
#             with _ppmac.lock_ppmac:
            _ppmac.write(_msg)
            _ppmac.write('enable plc HomeA')
            _sleep(3)
            while (all([not _ppmac.motor_homed(5),
                        not _ppmac.motor_homed(6)])):
                _sleep(1)
            self.ppmac.remove_backlash(0)
#             self.ui.chb_homed.setChecked(True)
            self.timer.start(1000)
            return True
        except Exception:
            self.ui.chb_homed.setChecked(False)
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)
            return False

    def home_x(self):
        """Home X motors.

        Returns:
            True if successfull;
            False otherwise."""
        try:
            self.timer.stop()
#             with _ppmac.lock_ppmac:
            _ppmac.write('#1,3j/')
            _ppmac.write('enable plc HomeX')
            _sleep(3)
#             while (all([not _ppmac.motor_homed(1),
#                         not _ppmac.motor_homed(3)])):
#                 _sleep(1)
#             self.ui.chb_homed_x.setChecked(True)
            self.timer.start(1000)
            return True
        except Exception:
            self.ui.chb_homed_x.setChecked(False)
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)
            return False

    def home_y(self):
        """Home Y motors.

        Returns:
            True if successfull;
            False otherwise"""
        try:
            self.timer.stop()
#             with _ppmac.lock_ppmac:
            _ppmac.write('#2,4j/')
            _ppmac.write('enable plc HomeY')
            _sleep(3)
            self.timer.start(1000)
#             while (all([not _ppmac.motor_homed(2),
#                         not _ppmac.motor_homed(4)])):
#                 _sleep(1)
#                 self.ui.chb_homed_y.setChecked(True)
            return True
        except Exception:
            self.ui.chb_homed_y.setChecked(False)
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)
            return False

    def move(self):
        """Move rotation motors."""
        try:
            _steps = [self.ui.sb_steps5.value(), self.ui.sb_steps6.value()]
            if self.ui.rdb_abs.isChecked():
                _mode = '='
            else:
                _mode = '^'
#             with _ppmac.lock_ppmac:
            self.timer.stop()
            _ppmac.write('#5j' + _mode + str(_steps[0]) +
                         ';#6j' + _mode + str(_steps[1]))
            self.timer.start(1000)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)

    def move_xy(self):
        """Move X and Y motors."""
        try:
            _x_lim = [self.ui.dsb_min_x.value()*10**3,
                      self.ui.dsb_max_x.value()*10**3]
            _y_lim = [self.ui.dsb_min_y.value()*10**3,
                      self.ui.dsb_max_y.value()*10**3]
            _pos_x = self.ui.dsb_pos_x.value()  # *10**-3/self.cfg.x_sf
            _pos_y = self.ui.dsb_pos_y.value()  # *10**-3/self.cfg.y_sf

            if _x_lim[0] <= _pos_x <= _x_lim[1]:
                _pos_x = _pos_x*10**-3/self.cfg.x_sf
            else:
                _QMessageBox.warning(self, 'Information',
                                     'X position out of range.',
                                     _QMessageBox.Ok)
                return False

            if _y_lim[0] <= _pos_y <= _y_lim[1]:
                _pos_y = _pos_y*10**-3/self.cfg.y_sf
            else:
                _QMessageBox.warning(self, 'Information',
                                     'Y position out of range.',
                                     _QMessageBox.Ok)
                return False

            if self.ui.rdb_abs_xy.isChecked():
                _mode = '='
            else:
                _mode = '^'

#             with _ppmac.lock_ppmac:
            self.timer.stop()
            _ppmac.write('#1..4j/')
            _msg_x = '#1,3j' + _mode + str(_pos_x)
            _msg_y = '#2,4j' + _mode + str(_pos_y)
            _ppmac.write(_msg_x + ';' + _msg_y)
            self.timer.start(1000)

            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            self.timer.start(1000)
            return False
