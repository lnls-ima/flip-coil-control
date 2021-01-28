# -*- coding: utf-8 -*-

"""Run the flip coil control application."""

from flipcoil.gui import flipcoilapp


THREAD = True


if THREAD:
    thread = flipcoilapp.run_in_thread()
else:
    flipcoilapp.run()
