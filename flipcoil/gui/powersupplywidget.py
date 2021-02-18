"""Power Supply widget"""

import os as _os
import sys as _sys
import traceback as _traceback
from qtpy.QtCore import Qt as _Qt
from qtpy.QtWidgets import (
    QApplication as _QApplication,
    QDialog as _QDialog,
    QMessageBox as _QMessageBox,
    QTableWidgetItem as _QTableWidgetItem,
    )

import qtpy.uic as _uic

import numpy as _np

from flipcoil.gui.utils import (
    get_ui_file as _get_ui_file,
    sleep as _sleep,
    update_db_name_list as _update_db_name_list,
    )

from flipcoil.devices import ps as _ps
import flipcoil.data as _data


class PowerSupplyWidget(_QDialog):
    """Flip Coil power supply configuration and control widget."""

    def __init__(self, parent=None):
        """Set up the ui and create connections."""
        super().__init__(parent)

        # setup the ui
        uifile = _get_ui_file(self)
        self.ui = _uic.loadUi(uifile, self)

        self.cfg = _data.configuration.PowerSupplyConfig()

        self.ps = _ps

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
        self.ui.pbt_refresh.clicked.connect(self.display_current)
        self.ui.pbt_configure_pid.clicked.connect(self.configure_pid)
        self.ui.pbt_configure_ps.clicked.connect(self.configure_ps)
        self.ui.pbt_turn_on_off.clicked.connect(self.turn_on_off)
        self.ui.pbt_send.clicked.connect(self.send_setpoint)
        self.ui.pbt_reset_interlocks.clicked.connect(self.reset_interlocks)
        self.ui.pbt_add_row.clicked.connect(lambda: self.add_row(
            self.ui.tw_currents))
        self.ui.pbt_remove_row.clicked.connect(lambda: self.remove_row(
            self.ui.tw_currents))
        self.ui.pbt_clear_table.clicked.connect(lambda: self.clear_table(
            self.ui.tw_currents))
        self.ui.pbt_save_cfg.clicked.connect(self.save_cfg)
        self.ui.pbt_load_cfg.clicked.connect(self.load_cfg)
        self.ui.pbt_update_cfg.clicked.connect(self.update_cfg_list)

    def update_cfg_list(self):
        """Updates configuration name list in combobox."""
        try:
            _update_db_name_list(self.cfg, self.ui.cmb_cfg_name)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def update_cfg_from_ui(self):
        """Updates current power supply configuration from ui widgets.

        Returns:
            True if successfull;
            False otherwise."""
        try:
            self.cfg.name = self.ui.cmb_cfg_name.currentText()
            self.cfg.ps_type = self.ui.cmb_ps_type.currentIndex() + 2
            self.cfg.dclink = self.ui.sb_dclink.value()
            self.cfg.current_setpoint = self.ui.dsb_current_setpoint.value()
            self.cfg.min_current = self.ui.dsb_min_current.value()
            self.cfg.max_current = self.ui.dsb_max_current.value()
            self.cfg.kp = self.ui.dsb_kp.value()
            self.cfg.ki = self.ui.dsb_ki.value()
            self.cfg.current_array = self.table_to_array(self.ui.tw_currents)
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
            self.ui.cmb_ps_type.setCurrentIndex(self.cfg.ps_type - 2)
            self.ui.sb_dclink.setValue(self.cfg.dclink)
            self.ui.dsb_current_setpoint.setValue(self.cfg.current_setpoint)
            self.ui.dsb_min_current.setValue(self.cfg.min_current)
            self.ui.dsb_max_current.setValue(self.cfg.max_current)
            self.ui.dsb_kp.setValue(self.cfg.kp)
            self.ui.dsb_ki.setValue(self.cfg.ki)
            self.array_to_table(self.cfg.current_array, self.ui.tw_currents)
            _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def add_row(self, tw):
        """Adds row into tbl_currents tableWidget."""
        try:
            _tw = tw
            _idx = _tw.rowCount()
            _tw.insertRow(_idx)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def remove_row(self, tw):
        """Removes selected row from tbl_currents tableWidget."""
        try:
            _tw = tw
            _idx = _tw.currentRow()
            _tw.removeRow(_idx)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def clear_table(self, tw):
        """Clears tbl_currents tableWidget."""
        try:
            _tw = tw
            _tw.clearContents()
            _ncells = _tw.rowCount()
            while _ncells >= 0:
                _tw.removeRow(_ncells)
                _ncells = _ncells - 1
                _QApplication.processEvents()
        except Exception:
            _traceback.print_exc(file=_sys.stdout)

    def table_to_array(self, tw):
        """Returns tbl_currents tableWidget values in a numpy array."""
        try:
            _tw = tw
            _ncells = _tw.rowCount()
            _current_array = []
            if _ncells > 0:
                for i in range(_ncells):
                    _tw.setCurrentCell(i, 0)
                    if _tw.currentItem() is not None:
                        _current_array.append(float(_tw.currentItem().text()))
                return _np.array(_current_array)
            else:
                return _np.array([])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.warning(self, 'Warning',
                                 'Could not convert table to array.\n'
                                 'Check if all inputs are numbers.',
                                 _QMessageBox.Ok)
            return _np.array([])

    def array_to_table(self, array, tw):
        """Inserts array values into tbl_currents tableWidget."""
        try:
            _tw = tw
            _ncells = _tw.rowCount()
            _array = array
            if _ncells > 0:
                self.clear_table(_tw)
            for i in range(len(_array)):
                _tw.insertRow(i)
                _item = _QTableWidgetItem()
                _tw.setItem(i, 0, _item)
                _item.setText(str(_array[i]))
                _QApplication.processEvents()
                _sleep(0.01)
            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.warning(self, 'Warning',
                                 'Could not insert array values into table.',
                                 _QMessageBox.Ok)
            return False

    def set_address(self, address):
        """Sets power supply address.

        Args:
            address (int): power supply new address.
        Returns:
            True in case of success.
            False otherwise."""

        if _ps.ser.is_open:
            _ps.SetSlaveAdd(address)
            return True
        else:
            _QMessageBox.warning(self, 'Warning',
                                 'Power Supply serial port is closed.',
                                 _QMessageBox.Ok)
            return False

    def set_op_mode(self, mode=0):
        """Sets power supply operation mode.

        Args:
            mode (int): 0 for SlowRef, 1 for SigGen.
        Returns:
            True in case of success.
            False otherwise."""

        _ps.select_op_mode(mode)
        _sleep(0.1)
        if _ps.read_ps_opmode() == mode:
            return True
        return False

    def configure_ps(self):
        """Configures Power Supply."""
        self.update_cfg_from_ui()

    def turn_on_off(self):
        """Turns power supply on and off."""
        try:

            _ps_type = self.cfg.ps_type
            self.set_address(_ps_type)

            _status_ps = _ps.read_ps_onoff()
            # Status PS is OFF
            if not _status_ps:
                try:
                    _ps.read_iload1()
                except Exception:
                    _traceback.print_exc(file=_sys.stdout)
                    _QMessageBox.warning(self, 'Warning',
                                         'Could not read the current.',
                                         _QMessageBox.Ok)
                    return

                _status_interlocks = _ps.read_ps_softinterlocks()

                # PS 1000 A needs to turn dc link on
                if _ps_type == 2:
                    _QMessageBox.warning(self, 'Warning',
                                         'F1000 is using an outdated firmware.'
                                         ' Please connect another power '
                                         'supply.',
                                         _QMessageBox.Ok)
                    return
                    _ps.SetSlaveAdd(_ps_type - 1)
                    # Turn ON PS DClink
                    try:
                        # Turn ON the DC Link of the PS
                        _ps.turn_on()
                        _sleep(1)
                        if _ps.read_ps_onoff() != 1:
                            _QMessageBox.warning(self, 'Warning',
                                                 'Power Supply Capacitor Bank '
                                                 'did not initialize.',
                                                 _QMessageBox.Ok)
                            return
                    except Exception:
                        _QMessageBox.warning(self, 'Warning',
                                             'Power Supply Capacitor Bank '
                                             'did not initialize.',
                                             _QMessageBox.Ok)
                        return
                    # Closing DC link Loop
                    try:
                        _ps.closed_loop()        # Closed Loop
                        _sleep(1)
                        if _ps.read_ps_openloop() == 1:
                            _QMessageBox.warning(self, 'Warning',
                                                 'Power Supply circuit loop is'
                                                 ' not closed.',
                                                 _QMessageBox.Ok)
                            return
                    except Exception:
                        _QMessageBox.warning(self, 'Warning', 'Power Supply '
                                             'circuit loop is not closed.',
                                             _QMessageBox.Ok)
                        return
                    # Set ISlowRef for DC Link (Capacitor Bank)
                    # Operation mode selection for Slowref
                    if not self.set_op_mode(0):
                        _QMessageBox.warning(self, 'Warning', 'Could not set '
                                             'the slowRef operation mode.',
                                             _QMessageBox.Ok)
                        return
                    # 90 V
                    _dclink_value = self.cfg.dclink
                    # Set 90 V for Capacitor Bank (default value according to
                    # the ELP Group)
                    _ps.set_slowref(_dclink_value)
                    _sleep(1)
                    _feedback_DCLink = _ps.read_vdclink()
                    # Waiting few seconds until voltage stabilization before
                    # starting PS Current
                    _i = 100
                    while _feedback_DCLink < _dclink_value and _i > 0:
                        _feedback_DCLink = _ps.read_vdclink()
                        _QApplication.processEvents()
                        _sleep(0.5)
                        _i = _i - 1
                    if _i == 0:
                        _QMessageBox.warning(self, 'Warning', 'DC link '
                                             'setpoint is not set.\nCheck '
                                             'configurations.',
                                             _QMessageBox.Ok)
                        _ps.turn_off()
                        return
                # Turn on Power Supply
                _ps.SetSlaveAdd(_ps_type)  # Set power supply address
                self.configure_pid()
                _ps.turn_on()
                _sleep(1)
                if not _ps.read_ps_onoff():
                    if _ps_type == 2:
                        _ps.SetSlaveAdd(_ps_type - 1)
                    # turn_off PS DC Link
                    _ps.turn_off()
                    _QMessageBox.warning(self, 'Warning',
                                         'The Power Supply did not start.',
                                         _QMessageBox.Ok)
                    return
                # Closed Loop
                _ps.closed_loop()
                _sleep(0.1)
                if _ps_type == 2:
                    _sleep(0.9)
                if _ps.read_ps_openloop() == 1:
                    _ps.SetSlaveAdd(_ps_type - 1)
                    # turn_off PS DC Link
                    _ps.turn_off()
                    _QMessageBox.warning(self, 'Warning', 'Power Supply '
                                         'circuit loop is not closed.',
                                         _QMessageBox.Ok)
                    return
                self.display_current()
                _QMessageBox.information(self, 'Information', 'The Power '
                                         'Supply started successfully.',
                                         _QMessageBox.Ok)
            # Turn off power supply
            else:
                _ps.SetSlaveAdd(_ps_type)
                _ps.turn_off()
                _sleep(1)
                _status = _ps.read_ps_onoff()
                if _status:
                    _QMessageBox.warning(self, 'Warning', 'Could not turn the'
                                         ' power supply off.\nPlease, try '
                                         'again.',
                                         _QMessageBox.Ok)
                    return
                # Turn of dc link
                if _ps_type == 2:
                    _ps.SetSlaveAdd(_ps_type - 1)
                    _ps.turn_off()
                    _sleep(0.1)
                    if _ps_type == 2:
                        _sleep(0.9)
                    _status = _ps.read_ps_onoff()
                    if _status:
                        _QMessageBox.warning(self, 'Warning', 'Could not turn'
                                             ' the power supply off.\n'
                                             'Please, try again.',
                                             _QMessageBox.Ok)
                _QMessageBox.information(self, 'Information',
                                         'Power supply was turned off.',
                                         _QMessageBox.Ok)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.warning(self, 'Warning',
                                 'Failed to change the power supply state.',
                                 _QMessageBox.Ok)
            return

    def display_current(self):
        """Displays power supply current on ui.

        Returns:
            True if succsessfull;
            False otherwise."""
        try:
            _ps.SetSlaveAdd(self.cfg.ps_type)
            _actual_current = round(float(_ps.read_iload1()), 3)
            self.ui.lcd_actual_current.display(_actual_current)
            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            _QMessageBox.warning(self, 'Warning',
                                 'Could not display the current.',
                                 _QMessageBox.Ok)
            return False

    def configure_pid(self):
        """Configures power supply PID parameters from UI."""
        _ans = _QMessageBox.question(self, 'PID settings', 'Be aware that this'
                                     ' will overwrite the current '
                                     'configurations.\nAre you sure you want '
                                     'to configure the PID parameters?',
                                     _QMessageBox.Yes |
                                     _QMessageBox.No)
        if _ans == _QMessageBox.Yes:
            try:
                self.cfg.kp = self.ui.dsb_kp.value()
                self.cfg.ki = self.ui.dsb_ki.value()
                _ps_type = self.cfg.ps_type
                _ps.SetSlaveAdd(_ps_type)

                if _ps_type == 3:
                    _umin = 0
                else:
                    _umin = -0.90

                if _ps_type in [2, 3, 4]:
                    _dsp_id = 0
                elif _ps_type == 5:
                    _dsp_id = 1
                elif _ps_type == 6:
                    _dsp_id = 2
                elif _ps_type == 7:
                    _dsp_id = 3

                _ps.set_dsp_coeffs(3, _dsp_id, [self.cfg.kp, self.cfg.ki,
                                                0.90, _umin])
                _QMessageBox.information(self, 'Information',
                                         'PID configured.',
                                         _QMessageBox.Ok)
                return True
            except Exception:
                _traceback.print_exc(file=_sys.stdout)
                _QMessageBox.warning(self, 'Warning',
                                     'Power Supply PID configuration fault.',
                                     _QMessageBox.Ok)
                return False

    def send_setpoint(self):
        try:
            _ps.SetSlaveAdd(self.cfg.ps_type)
            self.cfg.current_setpoint = self.ui.dsb_current_setpoint.value()
            _setpoint = self.cfg.current_setpoint

            if self.cfg.min_current <= _setpoint <= self.cfg.max_current:
                _ps.set_slowref(_setpoint)
                for _ in range(30):
                    _compare = round(float(_ps.read_iload1()), 3)
                    self.display_current()
                    if abs(_compare - _setpoint) <= 0.5:
                        _QMessageBox.information(self, 'Information',
                                                 'Current properly set.',
                                                 _QMessageBox.Ok)
                        return True
                    _QApplication.processEvents()
                    _sleep(1)
                _QMessageBox.warning(self, 'Warning',
                                     'Current was not properly set.',
                                     _QMessageBox.Ok)
                return False
            else:
                _QMessageBox.warning(self, 'Warning',
                                     'Current value is out of range.',
                                     _QMessageBox.Ok)
                return False
        except Exception:
            _QMessageBox.warning(self, 'Warning',
                                 'Current was not properly set.',
                                 _QMessageBox.Ok)
            return False

    def reset_interlocks(self):
        try:
            _ps_type = self.cfg.ps_type
            _interlock = 0

            if _ps_type == 2:
                _ps.SetSlaveAdd(_ps_type - 1)
                _ps.reset_interlocks()
                _sleep(0.1)
    #             _interlock = _interlock + (_ps.read_ps_hardinterlocks() +
    #                                        _ps.read_ps_softinterlocks())
                _interlock = 0

            _ps.SetSlaveAdd(_ps_type)
            _ps.reset_interlocks()
            _sleep(0.1)
            _interlock = _interlock + (_ps.read_ps_hardinterlocks() +
                                       _ps.read_ps_softinterlocks())

            if not _interlock:
                _QMessageBox.information(self, 'Information',
                                         'Interlocks cleared.',
                                         _QMessageBox.Ok)
            else:
                _QMessageBox.warning(self, 'Warning',
                                     'Interlocks could not be cleared.',
                                     _QMessageBox.Ok)
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
