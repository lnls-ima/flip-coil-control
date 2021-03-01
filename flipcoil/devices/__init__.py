"""This package contains all flip coil devices."""
from imautils.devices.PmacLV_IMS import EthernetCom as Ppmac_eth
from imautils.devices.FDI2056 import EthernetCom as Fdi_eth
from imautils.devices.pydrs import SerialDRS
from imautils.devices import Agilent3458ALib as _Agilent3458ALib
from imautils.devices import Agilent34970ALib as _Agilent34970ALib
import time as _time
import numpy as _np
import sys as _sys
import threading as _threading
import traceback as _traceback
import socket as _socket


from flipcoil.gui.utils import (
    sleep as _sleep,
    )


class MultiChannel(_Agilent34970ALib.Agilent34970AGPIB):
    """Multichannel class."""

    def send(self, command):
        try:
            self.inst.write(command)
            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

    def config_temp_volt(self):
        try:
            self.send('*RST')
            self.send('*CLS')
            _cmd = ':CONF:TEMP FRTD,85, (@101:103); VOLT:DC (@104:105);'
            self.send(_cmd)
            _sleep(0.3)
            _cmd = ':ROUT:SCAN (@101:105)'
            self.send(_cmd)
            return True
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

    def read_temp_volt(self, wait=0.5):
        self.send(':READ?')
        _sleep(wait)
        _ans = self.inst.read('\n').split(',')
        for i in range(len(_ans)):
            _ans[i] = float(_ans[i])
        return _ans

#     def read_val(self):
#         self.send(':READ?')
#         _sleep(0.85)
#         _ans = self.read_from_device()
#         return _ans


class Multimeter(_Agilent3458ALib.Agilent3458AGPIB):
    """Multimeter class."""

    def configure(self, aper, mrange):
        """Configure multimeter.
        Args:
            aper (float): A/D converter integration time in ms.
            mrange (float): measurement range in volts.
        """
        self.send_command(self.commands.func_volt)
        self.send_command(self.commands.tarm_auto)
        self.send_command(self.commands.trig_auto)
        self.send_command(self.commands.nrdgs_ext)
        self.send_command(self.commands.arange_off)
        self.send_command(self.commands.fixedz_on)
        self.send_command(self.commands.range + str(mrange))
        self.send_command(self.commands.math_off)
        self.send_command(self.commands.azero_once)
        self.send_command(self.commands.trig_buffer_off)
        self.send_command(self.commands.delay_0)
        self.send_command(
            self.commands.aper + '{0:.10f}'.format(aper/1000))
        self.send_command(self.commands.disp_off)
        self.send_command(self.commands.scratch)
        self.send_command(self.commands.end_gpib_always)
        self.send_command(self.commands.mem_fifo)

    # Configure multimeter
    def configure_volt(self, nplc=3, time=3):
        _rgds = int(_np.ceil(time/(nplc/60)))
        self.configure(50, 0)  # integration time 50ms and 100mV Range
        self.send_command('NPLC {}'.format(nplc))  # volt.send_command('APER 0.05')
        self.send_command('TRIG HOLD')
        self.send_command('DIM Rdgs({})'.format(_rgds))
        self.send_command('INBUF ON')
        self.send_command('NRDGS {}, AUTO'.format(_rgds))
        self.configure_reading_format('DREAL')
        self.send_command('DISP ON')

    def configure_reading_format(self, formtype):
        """Configure multimeter reading format.
        Args:
            formtype (str): format type [SREAL, DREAL].
        """
        self.send_command(self.commands.mem_fifo)
        if formtype == 'SREAL':
            self.send_command(self.commands.oformat_sreal)
            self.send_command(self.commands.mformat_sreal)
        elif formtype == 'DREAL':
            self.send_command(self.commands.oformat_dreal)
            self.send_command(self.commands.mformat_dreal)

    def start_measurement(self):
        volt.configure_reading_format('DREAL')
        volt.send_command('TRIG SGL')

    def get_data_count(self):
        volt.send_command(volt.commands.mcount)
        return int(volt.read_from_device().strip('\r\n'))

    def error_query(self):
        volt.send_command('ERR?')
        return int(volt.read_from_device().strip('\r\n'))


class Fdi(Fdi_eth):
    def configure_integrator(self, time=3, interval=50, base_frq=1000,
                             calibrate=0):
        self.main_settings(100, "Timer")  # gain, source
        # fdi.send('CALC:FLUX 0')  # configures to integrate between triggers
        self.send('FORM:TIMESTAMP:ENABLE 0')  # disables timestamp
        # fdi.send('TRIG:SOUR BUS') # trigger source from software
        # fdi.send('INP:COUP DC')  # Couples coil to the integrator
        # TRIG:SOUR TIMER
        # CALC:FLUX 1
        self.send('TRIG:TIM ' + str(base_frq) + ' Hz')  # 3 eletric power cycles
        self.send('CALC:FLUX 1')  # integrates flux during all measurement
        measurement_time = time  # total measurement time [s]
        measurement_interval = interval  # interval beetween triggers, in [ms]
        counts = 1 + int(measurement_time/(measurement_interval*10**-3))
        ecounts = int(measurement_interval*10**-3*base_frq)
#         print(counts, ecounts)
        self.send('TRIG:COUN ' + str(counts))
        self.send('TRIG:ECO ' + str(ecounts))
        if calibrate:
            self.calibrate()
        return counts


class Ppmac(Ppmac_eth):
    # deltatau functions
    def __init__(self):
        super().__init__()
        self.lock_ppmac = _threading.RLock()
        self.flag_abort = False

    def motor_stopped(self, n=5):
#         with self.lock_ppmac:
        try:
            msg = 'Motor[' + str(n) + '].DesVelZero'
            self.write(msg)
            _sleep(0.1)
            ans = self.read().split(msg)[-1]
            return int(ans.split(msg)[-1].split('=')[-1].split('\r')[0])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def in_motion(self):
#         with self.lock_ppmac:
        try:
            msg = 'motionFlag'
            self.write(msg)
            _sleep(0.1)
            ans = self.read().split(msg)[-1]
            return int(ans.split('=')[-1][0])
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def read_motor_pos(self, motors=[]):
#         with self.lock_ppmac:
        try:
            msg = '#'
            msg = msg + str(motors).strip('[]').replace(' ', '')
            msg = msg + 'p'
            self.write(msg)
            _sleep(0.1)
            ans = self.read()
            ans1 = ans.split(msg)[-1].strip('\r\n\x06').split(' ')
            pos = _np.array([float(val) for val in ans1])
            return pos
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def read_axis_pos(self, axis='', coord=1):
#         with self.lock_ppmac:
        try:
            if all([axis is not None,
                    axis != '']):
                msg = '&' + str(coord) + axis + 'p'
                self.write(msg)
                ans = self.read()
                ans1 = ans.split(msg)[-1].strip('\r\n\x06')
                return float(ans1)
            else:
                print(axis)
                return None
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def motor_homed(self, motor):
#         with self.lock_ppmac:
        try:
#             try:
            self.read()
#             except _socket.timeout:
#                 pass
            _sleep(1)
            self.write("Motor{0}Homed".format(motor))
            _ans = self.read()
            if int(_ans.split('=')[-1].strip('\r\n\x06')):
                return True
            else:
                return False
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def remove_backlash(self, target_pos=0, elim=2, ccw=1, max_tries=100):
        try:
            target_pos_steps = int(target_pos*102400/360000)
            if ccw > 0:
                ccw = 1
            else:
                ccw = -1
            dp = 10000  # 51200
            dp5 = -1*dp
            dp6 = dp
            lim = elim
            n_tries = 0

            self.write('#5j=' + str(ccw*(dp + -1*target_pos_steps)) +
                       ';#6j=' + str(ccw*(-1*dp + target_pos_steps)))
            _sleep(0.1)
            while not self.motor_stopped(5):
                _sleep(0.1)
            _sleep(1)
            self.write('#5j^' + str(-1*ccw*dp) +
                       ';#6j^' + str(ccw*dp))
            _sleep(0.1)
            while not self.motor_stopped(5):
                _sleep(0.1)
            _sleep(1)
            p_list = self.read_motor_pos([5, 6, 7, 8])

            while(any([abs(-1*target_pos - p_list[-2]) > lim,
                       abs(target_pos - p_list[-1]) > lim]) and
                       n_tries < max_tries):
                dp5 = dp5 + ccw*int((-1*target_pos - p_list[-2])*102400/360000)
                dp6 = dp6 + ccw*int((target_pos - p_list[-1])*102400/360000)
                self.write('#5j=' + str(ccw*(dp + -1*target_pos_steps)) +
                           ';#6j=' + str(ccw*(-1*dp + target_pos_steps)))
                _sleep(0.1)
                while not self.motor_stopped(5):
                    _sleep(0.1)
                _sleep(1)
                self.write('#5j^' + str(ccw*dp5) +
                           ';#6j^' + str(ccw*dp6))
                _sleep(0.1)
                while not self.motor_stopped(5):
                    _sleep(0.1)
                _sleep(1)
                p_list = self.read_motor_pos([5, 6, 7, 8])
                n_tries = n_tries + 1

            if n_tries < max_tries:
                self.homez(5)
                self.homez(6)
                return True
            else:
                return False
        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return None

    def align_motors(self, limit=2, max_tries=100):
        try:
            sf = 102400/360000  # [steps/mdeg]
    #         limit = cfg.max_pos_error
            p_list = self.read_motor_pos([7, 8])
            steps = _np.array([1000, -1000]) - 1*sf*p_list
            self.write('#5j^{0};#6j^{1}'.format(steps))
            _sleep(0.1)
            while not self.motor_stopped(5):
                _sleep(0.1)
            p_list = self.read_motor_pos([7, 8])
            p_sign_init = _np.sign(p_list)

            while all([not -1*limit <= p_list[0] <= limit,
                       not -1*limit <= p_list[1] <= limit,
                       max_tries > 0]):
                max_tries -= 1
                p_list = self.read_motor_pos([7, 8])
                steps = -1*sf*p_list
                for i in range(len(steps)):
                    if steps[i] < 5:
                        steps[i] = 1
                self.write('#5j^{0};#6j^{1}'.format(steps))
                _sleep(0.1)
                while not self.motor_stopped(5):
                    _sleep(0.1)
                _sleep(1)
                p_list = self.read_motor_pos([7, 8])
                p_sign = _np.sign(p_list)
                if all([not -1*limit <= p_list[0] <= limit,
                        not -1*limit <= p_list[1] <= limit,
                        not p_sign == p_sign_init]):
                    steps = _np.array([1000, -1000]) - 1*sf*p_list
                    self.write('#5j^{0};#6j^{1}'.format(steps))
                    _sleep(0.1)
                    while not self.motor_stopped(5):
                        _sleep(0.1)
                    p_list = self.read_motor_pos([7, 8])
                    p_sign_init = _np.sign(p_list)

            if max_tries > 0:
                return True
            else:
                return False

        except Exception:
            _traceback.print_exc(file=_sys.stdout)
            return False

#     def remove_backlash2(self, target_pos=0, elim=2, ccw=1, max_tries=100,
#                          bck_steps=1000):
#         with self.lock_ppmac:
#             target_pos_steps = int(target_pos*102400/360000)
#             if ccw > 0:
#                 ccw = 1
#             else:
#                 ccw = -1
#             dp = 10000  # 51200
#             dp = bck_steps
#             dp5 = -1*dp
#             dp6 = dp
#             lim = elim
#             n_tries = 0
# 
#             self.write('#5j=' + str(ccw*(dp + -1*target_pos_steps)) +
#                        ';#6j=' + str(ccw*(-1*dp + target_pos_steps)))
#             _sleep(0.1)
#             while not self.motor_stopped(5):
#                 _sleep(0.1)
#             _sleep(1)
#             self.write('#5j^' + str(-1*ccw*dp) +
#                        ';#6j^' + str(ccw*dp))
#             _sleep(0.1)
#             while not self.motor_stopped(5):
#                 _sleep(0.1)
#             _sleep(1)
#             p_list = self.read_motor_pos([5, 6, 7, 8])
# 
#             while(any([abs(-1*target_pos - p_list[-2]) > lim,
#                        abs(target_pos - p_list[-1]) > lim]) and
#                        n_tries < max_tries):
#                 dp5 = dp5 + ccw*int((-1*target_pos - p_list[-2])*102400/360000)
#                 dp6 = dp6 + ccw*int((target_pos - p_list[-1])*102400/360000)
#                 self.write('#5j=' + str(ccw*(dp + -1*target_pos_steps)) +
#                            ';#6j=' + str(ccw*(-1*dp + target_pos_steps)))
#                 _sleep(0.1)
#                 while(self.motor_stopped(5)):
#                     _sleep(0.1)
#                 _sleep(1)
#                 self.write('#5j^' + str(ccw*dp5) +
#                            ';#6j^' + str(ccw*dp6))
#                 _sleep(0.1)
#                 while not self.motor_stopped(5):
#                     _sleep(0.1)
#                 _sleep(1)
#                 p_list = self.read_motor_pos([5, 6, 7, 8])
#                 n_tries = n_tries + 1
# 
#                 if self.flag_abort:
#                     self.flag_abort = False
#                     return False
# 
#             if n_tries < max_tries:
#                 self.homez(5)
#                 self.homez(6)
#                 return True
#             else:
#                 return False


ppmac = Ppmac()
fdi = Fdi()
ps = SerialDRS()
volt = Multimeter(log=True)
mult = MultiChannel()
