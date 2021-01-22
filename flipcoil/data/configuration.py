"""Flip Coil configuration module"""

import collections as _collections
import imautils.db.database as _database
from builtins import int


# Conection Config
class ConnectionConfig(_database.DatabaseAndFileDocument):
    """Read, write and store connection configuration data."""

    label = 'Connection'
    collection_name = 'connections'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('fdi_enable',
            {'field': 'fdi_enable', 'dtype': int, 'not_null': True}),
        ('pmac_enable',
            {'field': 'pmac_enable', 'dtype': int, 'not_null': True}),
        ('ps_enable',
            {'field': 'ps_enable', 'dtype': int, 'not_null': True}),
        ('fdi_address',
            {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
        ('ppmac_address',
            {'field': 'ppmac_address', 'dtype': str, 'not_null': True}),
        ('fdi_address',
            {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
        ('ps_port',
            {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
    ])

    def __init__(
            self, database_name=None, mongo=False, server=None):
        """Initialize object.

        Args:
            filename (str): connection configuration filepath.
            database_name (str): database file path (sqlite) or name (mongo).
            idn (int): id in database table (sqlite) / collection (mongo).
            mongo (bool): flag indicating mongoDB (True) or sqlite (False).
            server (str): MongoDB server.

        """
        super().__init__(
            database_name=database_name, mongo=mongo, server=server)


# FDI config
    # Trig Sour
    # Mode (flux, volt)
    # Timer base
class IntegratorConfig(_database.DatabaseAndFileDocument):
    """Read, write and store FDI2056 integrator configuration data."""

    label = 'Integrator'
    collection_name = 'integrator'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('trigger_source',
            {'field': 'trigger_source', 'dtype': str, 'not_null': True}),
        ('mode',
            {'field': 'mode', 'dtype': str, 'not_null': True}),
        ('timer_base',
            {'field': 'timer_base', 'dtype': float, 'not_null': True}),
    ])

    def __init__(
            self, database_name=None, mongo=False, server=None):
        """Initialize object.

        Args:
            filename (str): connection configuration filepath.
            database_name (str): database file path (sqlite) or name (mongo).
            idn (int): id in database table (sqlite) / collection (mongo).
            mongo (bool): flag indicating mongoDB (True) or sqlite (False).
            server (str): MongoDB server.

        """
        super().__init__(
            database_name=database_name, mongo=mongo, server=server)


# PPMAC config
    # vel
    # acc
    # jerk
    # gather
    # enc5, 6 ref
class PpmacConfig(_database.DatabaseAndFileDocument):
    """Read, write and store ppmac configuration data."""

    label = 'PPMAC'
    collection_name = 'ppmac'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('speed',
            {'field': 'speed', 'dtype': float, 'not_null': True}),
        ('accel',
            {'field': 'accel', 'dtype': float, 'not_null': True}),
        ('jerk',
            {'field': 'jerk', 'dtype': float, 'not_null': True}),
        ('enc_ref5',
            {'field': 'enc_ref5', 'dtype': float, 'not_null': True}),
        ('enc_ref6',
            {'field': 'enc_ref6', 'dtype': float, 'not_null': True}),
    ])

    def __init__(
            self, database_name=None, mongo=False, server=None):
        """Initialize object.

        Args:
            filename (str): connection configuration filepath.
            database_name (str): database file path (sqlite) or name (mongo).
            idn (int): id in database table (sqlite) / collection (mongo).
            mongo (bool): flag indicating mongoDB (True) or sqlite (False).
            server (str): MongoDB server.

        """       
        super().__init__(
            database_name=database_name, mongo=mongo, server=server)


# Agilent config


# Power Supply config


# Measurement config
    # N coil turns
    # Coil radius
    # pos inicial
    # duration
    # integration interval
    # dp5,6 ida, volta
    # elim
class MeasurementConfig(_database.DatabaseAndFileDocument):
    """Read, write and store measurement configuration data."""

    label = 'MeasurementCfg'
    collection_name = 'measurementcfgs'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('n_turns',
            {'field': 'n_turns', 'dtype': int, 'not_null': True}),
        ('coil_width',
            {'field': 'coil_width', 'dtype': float, 'not_null': True}),
        ('meas_duration',
            {'field': 'meas_duration', 'dtype': float, 'not_null': True}),
        ('integration_interval',
            {'field': 'integration_interval', 'dtype': float, 'not_null': True}),
        ('initial_pos',
            {'field': 'initial_pos', 'dtype': float, 'not_null': True}),
        ('direction',
            {'field': 'direction', 'dtype': int, 'not_null': True}),
        ('delta_fwr_steps5',
            {'field': 'delta_fwr_steps5', 'dtype': float, 'not_null': True}),
        ('delta_fwr_steps6',
            {'field': 'delta_fwr_steps6', 'dtype': float, 'not_null': True}),
        ('delta_bck_steps5',
            {'field': 'delta_bck_steps5', 'dtype': float, 'not_null': True}),
        ('delta_bck_steps6',
            {'field': 'delta_bck_steps6', 'dtype': float, 'not_null': True}),
    ])

    def __init__(
            self, database_name=None, mongo=False, server=None):
        """Initialize object.

        Args:
            filename (str): connection configuration filepath.
            database_name (str): database file path (sqlite) or name (mongo).
            idn (int): id in database table (sqlite) / collection (mongo).
            mongo (bool): flag indicating mongoDB (True) or sqlite (False).
            server (str): MongoDB server.

        """       
        super().__init__(
            database_name=database_name, mongo=mongo, server=server)
