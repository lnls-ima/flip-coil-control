"""Flip Coil measurement data module"""

import numpy as _np
import collections as _collections
import imautils.db.database as _database


class MeasurementData(_database.DatabaseAndFileDocument):
    """Read, write and store measurement results data."""

    label = 'Measurement'
    collection_name = 'measurements'
    db_dict = _collections.OrderedDict([
        ('idn', {'field': 'id', 'dtype': int, 'not_null': True}),
        ('date', {'field': 'date', 'dtype': str, 'not_null': True}),
        ('hour', {'field': 'hour', 'dtype': str, 'not_null': True}),
        ('software_version',
            {'field': 'software_version', 'dtype': str, 'not_null': False}),
        ('name',
            {'field': 'name', 'dtype': str, 'not_null': True}),
        ('comments',
            {'field': 'comments', 'dtype': str, 'not_null': True}),
        ('I_mean',
            {'field': 'I_mean', 'dtype': float, 'not_null': True}),
        ('I_std',
            {'field': 'I_std', 'dtype': float, 'not_null': True}),
        ('data_frw',
            {'field': 'data_frw', 'dtype': _np.ndarray, 'not_null': True}),
        ('data_bck',
            {'field': 'data_bck', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos7f',
            {'field': 'pos7f', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos8f',
            {'field': 'pos8f', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos7b',
            {'field': 'pos7b', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos8b',
            {'field': 'pos8b', 'dtype': _np.ndarray, 'not_null': True}),
        ('cfg_id',
            {'field': 'cfg_id', 'dtype': int, 'not_null': True}),
        ('Iamb',
            {'field': 'Iamb', 'dtype': int, 'not_null': True}),
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
