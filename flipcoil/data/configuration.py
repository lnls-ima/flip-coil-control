"""Flip Coil configuration module"""

import collections as _collections
import imautils.db.database as _database
import numpy as _np


# Conection Config
# class ConnectionConfig(_database.DatabaseAndFileDocument):
#     """Read, write and store connection configuration data."""
# 
#     label = 'Connection'
#     collection_name = 'connections'
#     db_dict = _collections.OrderedDict([
#         ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
#         ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
#         ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
#         ('software_version',
#             {'field': 'software_version', 'dtype': str, 'not_null': False}),
#         ('fdi_enable',
#             {'field': 'fdi_enable', 'dtype': int, 'not_null': True}),
#         ('pmac_enable',
#             {'field': 'pmac_enable', 'dtype': int, 'not_null': True}),
#         ('ps_enable',
#             {'field': 'ps_enable', 'dtype': int, 'not_null': True}),
#         ('fdi_address',
#             {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
#         ('ppmac_address',
#             {'field': 'ppmac_address', 'dtype': str, 'not_null': True}),
#         ('fdi_address',
#             {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
#         ('ps_port',
#             {'field': 'fdi_address', 'dtype': str, 'not_null': True}),
#     ])
# 
#     def __init__(
#             self, database_name=None, mongo=False, server=None):
#         """Initialize object.
# 
#         Args:
#             filename (str): connection configuration filepath.
#             database_name (str): database file path (sqlite) or name (mongo).
#             idn (int): id in database table (sqlite) / collection (mongo).
#             mongo (bool): flag indicating mongoDB (True) or sqlite (False).
#             server (str): MongoDB server.
# 
#         """
#         super().__init__(
#             database_name=database_name, mongo=mongo, server=server)


# class IntegratorConfig(_database.DatabaseAndFileDocument):
#     """Read, write and store FDI2056 integrator configuration data."""
#
#     label = 'Integrator'
#     collection_name = 'integrator'
#     db_dict = _collections.OrderedDict([
#         ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
#         ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
#         ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
#         ('software_version',
#             {'field': 'software_version', 'dtype': str, 'not_null': False}),
#         ('trigger_source',
#             {'field': 'trigger_source', 'dtype': str, 'not_null': True}),
#         ('mode',
#             {'field': 'mode', 'dtype': str, 'not_null': True}),
#         ('timer_base',
#             {'field': 'timer_base', 'dtype': float, 'not_null': True}),
#     ])
#
#     def __init__(
#             self, database_name=None, mongo=False, server=None):
#         """Initialize object.
#
#         Args:
#             filename (str): connection configuration filepath.
#             database_name (str): database file path (sqlite) or name (mongo).
#             idn (int): id in database table (sqlite) / collection (mongo).
#             mongo (bool): flag indicating mongoDB (True) or sqlite (False).
#             server (str): MongoDB server.
#
#         """
#         super().__init__(
#             database_name=database_name, mongo=mongo, server=server)


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
        ('name',
            {'field': 'name', 'dtype': str, 'not_null': True}),
        ('speed',
            {'field': 'speed', 'dtype': float, 'not_null': True}),
        ('accel',
            {'field': 'accel', 'dtype': float, 'not_null': True}),
        ('jerk',
            {'field': 'jerk', 'dtype': float, 'not_null': True}),
        ('enc_ref1',
            {'field': 'enc_ref1', 'dtype': int, 'not_null': True}),
        ('enc_ref2',
            {'field': 'enc_ref2', 'dtype': int, 'not_null': True}),
        ('enc_ref3',
            {'field': 'enc_ref3', 'dtype': int, 'not_null': True}),
        ('enc_ref4',
            {'field': 'enc_ref4', 'dtype': int, 'not_null': True}),
        ('enc_ref5',
            {'field': 'enc_ref5', 'dtype': int, 'not_null': True}),
        ('enc_ref6',
            {'field': 'enc_ref6', 'dtype': int, 'not_null': True}),
    ])

    def __init__(self, database_name=None, mongo=False, server=None):
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


class MeasurementConfig(_database.DatabaseAndFileDocument):
    """Read, write and store measurement configuration data."""

    label = 'MeasurementCfg'
    collection_name = 'measurement_cfg'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('name',
            {'field': 'name', 'dtype': str, 'not_null': True, 'unique': True}),
        ('width',
            {'field': 'width', 'dtype': float, 'not_null': True}),
        ('turns',
            {'field': 'turns', 'dtype': float, 'not_null': True}),
        ('direction',
            {'field': 'direction', 'dtype': str, 'not_null': True}),
        ('start_pos',
            {'field': 'start_pos', 'dtype': float, 'not_null': True}),
        ('steps_f',
            {'field': 'steps_f', 'dtype': _np.ndarray, 'not_null': True}),
        ('steps_b',
            {'field': 'steps_b', 'dtype': _np.ndarray, 'not_null': True}),
        ('speed',
            {'field': 'speed', 'dtype': float, 'not_null': True}),
        ('accel',
            {'field': 'accel', 'dtype': float, 'not_null': True}),
        ('jerk',
            {'field': 'jerk', 'dtype': float, 'not_null': True}),
        ('nplc',
            {'field': 'nplc', 'dtype': int, 'not_null': True}),
        ('duration',
            {'field': 'duration', 'dtype': float, 'not_null': True}),
        ('nmeasurements',
            {'field': 'nmeasurements', 'dtype': int, 'not_null': True}),
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
