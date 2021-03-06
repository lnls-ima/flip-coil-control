
import os
from setuptools import setup


basedir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(basedir, 'VERSION'), 'r') as _f:
    __version__ = _f.read().strip()


setup(
    name='flipcoil',
    version=__version__,
    description='Flip coil control application',
    url='https://github.com/lnls-ima/flip-coil-control',
    author='lnls-ima',
    license='MIT License',
    packages=['flipcoil'],
    install_requires=[
        'pyvisa',
        'numpy',
        'scipy',
        'pandas',
#         'pyqtgraph',
        'pyserial',
        'matplotlib',
#         'minimalmodbus',
        'qtpy',
    ],
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False)
