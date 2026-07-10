"""QML settings page backend for Synthex Agent preferences."""
from .store import load, save, get, set as set_pref, DEFAULTS
__all__ = ["load","save","get","set_pref","DEFAULTS"]
