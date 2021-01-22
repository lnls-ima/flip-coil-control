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

        self.connect_signal_slots()

    def connect_signal_slots(self):
        """Create signal/slot connections."""
        self.ui.pbt_measure.clicked.connect(self.measure)
        self.ui.pbt_test.clicked.connect(self.test_steps)

    def save_log(self, array, name='', comments=''):
        name = name + _time.strftime('_%y_%m_%d_%H_%M', _time.localtime()) + '.dat'
        head = ('Turn1[V.s]\tTurn2[V.s]\tTurn3[V.s]\tTurn4[V.s]\tTurn5[V.s]\t' + 
                'Turn6[V.s]\tTurn7[V.s]\tTurn8[V.s]\tTurn9[V.s]\tTurn10[V.s]')
        comments = comments + '\n'
        _np.savetxt(name, array, delimiter='\t', comments=comments, header=head)

    def test_steps(self, init_pos=0):
        try:
            _ppmac.remove_backlash(init_pos)
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

    def measure(self, init_pos=0, rep=10, lim=2, interval=50, fdi_mode=False):
        try:
            _prg_dialog = _QProgressDialog('Measurement', 'Abort', 0, rep+1,
                                           self)
            _prg_dialog.setWindowTitle('Measurement Progress')
            _prg_dialog.setValue(0)
            _prg_dialog.show()
            _QApplication.processEvents()
            data_frw = _np.array([])
            data_bck = _np.array([])
            self.pos7f = _np.zeros((2, rep))
            self.pos7b = _np.zeros((2, rep))
            self.pos8f = _np.zeros((2, rep))
            self.pos8b = _np.zeros((2, rep))

            dp5_ida = -51209
            dp6_ida = 51170
            dp5_volta = 51218
            dp6_volta = -51166

            self.nplc = self.ui.sb_nplc.value()

            self.radius = self.ui.dsb_width.value() * 10**-3  # [m]
            self.n = self.ui.sb_turns.value()
            self.spd = self.parent_window.motors.ui.dsb_speed.value()  # [rev/s]
            self.steps_f = [dp5_ida, dp6_ida]  # steps
            self.steps_b = [dp5_volta, dp6_volta]  # steps

#             self.radius = 12.5e-3  # [m]
#             self.n = 1
            start_pos = 0  # [turns]
            end_pos = 0.5  # [turns]
            spd = 2
            speed = self.spd*102.4  # [rev/s]
            ta = -0.4  # acceleration time [ms]
            ts = 0  # jerk time [ms]
            wait = 2000  # time to wait between moves [ms]

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
                counts = _fdi.configure_integrator(time=3, interval=interval)
                _fdi.send('INP:COUP DC')
            else:
                counts = int(_np.ceil(3/(self.nplc/60)))
                _volt.configure_volt(nplc=self.nplc, time=3)
            _sleep(0.1)
            _ppmac.remove_backlash(init_pos)
            _sleep(10)
            for i in range(rep):
                if _prg_dialog.wasCanceled():
                    _prg_dialog.destroy()
                    return False

                if (any([abs(_ppmac.read_motor_pos([7])[0]) % 360000 > lim,
                         abs(_ppmac.read_motor_pos([8])[0]) % 360000 > lim])):
                    _ppmac.remove_backlash(init_pos)
                if fdi_mode:
                    _fdi.start_measurement()
                else:
                    _volt.start_measurement()
                _sleep(1)

                self.pos7f[0, i], self.pos8f[0, i] = (
                    _ppmac.read_motor_pos([7, 8]))
                _ppmac.write('#5j^' + str(self.steps_f[0]) +
                             ';#6j^' + str(self.steps_f[1]))

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
                self.pos7f[1, i], self.pos8f[1, i] = (
                    _ppmac.read_motor_pos([7, 8]))

                _sleep(10)

                if fdi_mode:
                    _fdi.start_measurement()
                else:
                    _volt.start_measurement()
                _sleep(1)

                self.pos7b[0, i], self.pos8b[0, i] = (
                    _ppmac.read_motor_pos([7, 8]))
                _ppmac.write('#5j^' + str(self.steps_b[0]) +
                             ';#6j^' + str(self.steps_b[1]))
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
                self.pos7b[1, i], self.pos8b[1, i] = (
                    _ppmac.read_motor_pos([7, 8]))

                _prg_dialog.setValue(i+1)

            self.data_frw = data_frw
            self.data_bck = data_bck

            self.save_log(data_frw, 'frw', 'Flip Coil')
            self.save_log(data_bck, 'bck', 'Flip Coil')
            self.save_log(self.pos7f, 'pos7f')
            self.save_log(self.pos8f, 'pos8f')
            self.save_log(self.pos7b, 'pos7b')
            self.save_log(self.pos8b, 'pos8b')

            _prg_dialog.destroy()
            _QMessageBox.information(self, 'Information',
                                     'Measurement Finished.',
                                     _QMessageBox.Ok)

            self.first_integral_calculus(dt=self.nplc/60, fdi_mode=fdi_mode)
            return True

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

    def first_integral_calculus(self, dt=2/60, fdi_mode=False):
        # analysis
        try:
            # _radius = 12.5e-3  # [m]
            _radius = self.radius
            _n = self.n  # number of coil turns
            # I = flux/(2*N*radius)
            if not fdi_mode:
                for i in range(self.data_frw.shape[1]):
                    _offset_f = self.data_frw[:40, i].mean()
                    _offset_b = self.data_bck[:40, i].mean()
                    _f_f = _np.array([0])
                    _f_b = _np.array([0])
                    for idx in range(len(self.data_frw[:, i])-1):
                        # dv = ((v[i+1] - v[i])/2)/0.05
                        # f = np.append(f, f[i]+dv)
                        _f_f_part = self.data_frw[:idx, i] - _offset_f
                        _f_b_part = self.data_bck[:idx, i] - _offset_b
                        _f_f = _np.append(_f_f, _np.trapz(_f_f_part, dx=dt))
                        _f_b = _np.append(_f_b, _np.trapz(_f_b_part, dx=dt))
                    if i == 0:
                        self.flx_f = _f_f
                        self.flx_b = _f_b
                    else:
                        self.flx_f = _np.vstack([self.flx_f, _f_f])
                        self.flx_b = _np.vstack([self.flx_b, _f_b])
#                 self.flx_f = _np.transpose(self.flx_f)
#                 self.flx_b = _np.transpose(self.flx_b)
            else:
                self.flx_f = _np.copy(self.data_frw)
                self.flx_b = _np.copy(self.data_bck)

            self.I_f = self.flx_f * 1/(2*_n*_radius)
            self.I_b = self.flx_b * 1/(2*_n*_radius)
            self.I = (self.flx_f - self.flx_b)/2 * 1/(2*_n*_radius)
            self.I_err = 1/2*(self.I_f.std()**2 + self.I_b.std()**2)**0.5

            self.If = self.I_f[61, :] - self.I_f[40, :]
            self.If_err = self.If.std()

            self.Ib = self.I_b[61, :] - self.I_b[40, :]
            self.Ib_err = self.Ib.std()

            self.Imeas = self.I[61, :] - self.I[40, :]
            self.Imeas_err = 1/2*(self.If_err**2 + self.Ib_err**2)**0.5

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False
