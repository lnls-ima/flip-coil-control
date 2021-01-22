"""Sub-package for configuration data."""

from .configuration import PpmacConfig as _PpmacConfig
from .configuration import ConnectionConfig as _ConnectionConfig
from .configuration import IntegratorConfig as _IntegratorConfig
from .configuration import MeasurementConfig as _MeasurementConfig

cfg_connection = _ConnectionConfig()
cfg_integrator = _IntegratorConfig()
cfg_ppmac = _PpmacConfig()
cfg_measurement = _MeasurementConfig()
