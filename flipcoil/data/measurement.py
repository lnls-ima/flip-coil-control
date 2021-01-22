"""Flip Coil measurement data module"""

import numpy as _np
import collections as _collections
import imautils.db.database as _database
# measurement data
    # flux forward
    # flux backward
    # flux mean
    # I forward
    # I backward
    # I mean
    # I std
    # Motor positions
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
        ('I_mean', 
            {'field': 'I_mean', 'dtype': float, 'not_null': True}),
        ('I_std', 
            {'field': 'I_std', 'dtype': float, 'not_null': True}),
        ('flux_frw', 
            {'field': 'flux_frw', 'dtype': _np.ndarray, 'not_null': True}),
        ('flux_bck', 
            {'field': 'flux_bck', 'dtype': _np.ndarray, 'not_null': True}),
        ('coil_width', 
            {'field': 'coil_width', 'dtype': float, 'not_null': True}),
        ('n_turns',
            {'field': 'n_turns', 'dtype': float, 'not_null': True}),
        ('inetegration_interval',
            {'field': 'integration_interval', 'dtype': float, 'not_null': True}),
        ('pos7_frw',
            {'field': 'pos7_frw', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos8_frw',
            {'field': 'pos8_frw', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos7_bck',
            {'field': 'pos7_bck', 'dtype': _np.ndarray, 'not_null': True}),
        ('pos8_bck', 
            {'field': 'pos8_bck', 'dtype': _np.ndarray, 'not_null': True}),
        #cfgs_ids!
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
