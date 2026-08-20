import sys

# Suppress all background console window creation on Windows (adb.exe, minitouch, etc.)
if sys.platform == "win32":
    import subprocess
    _orig_popen_init = subprocess.Popen.__init__
    def _silent_popen_init(self, *args, **kwargs):
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        else:
            kwargs["creationflags"] |= 0x08000000
        _orig_popen_init(self, *args, **kwargs)
    subprocess.Popen.__init__ = _silent_popen_init

from multiprocessing import freeze_support
from launch import launch

if __name__ == "__main__":
    freeze_support()
    launch()
