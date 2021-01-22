"""Provides methods to access various resource files for the application."""

__credits__     = [
#     ('alpha_b.svg', 'Alpha B Icon (from https://materialdesignicons.com/)'),
    ]


import os.path as _path

_BASE_PATH = _path.dirname(__file__)


def find(relpath):
    """Look up the resource file based on the relative path to this module.

    Args:
        relpath (str)

    Returns:
        str
    """
    return _path.join(_BASE_PATH, relpath)
