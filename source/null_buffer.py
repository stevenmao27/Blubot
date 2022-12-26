"""This module disables and re-enables printing to console"""

import sys

class NullIO():
    """Null Placeholder for stdout"""
    def write(self):
        pass
    def flush(): #omitting 'self' is necessary
        pass

SYSOUT = sys.stdout
NULLOBJ = NullIO

def mute_stdout():
    """Disables any writing to console (e.g. print())"""
    sys.stdout = NULLOBJ
def unmute_stdout():
    """Reenables any writing to console (e.g. print())"""
    sys.stdout = SYSOUT