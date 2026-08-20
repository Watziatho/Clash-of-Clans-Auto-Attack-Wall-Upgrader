import sys

# Suppress all background console window creation on Windows (adb.exe, minitouch, etc.)
if sys.platform == "win32":
    import subprocess
    _orig_popen = subprocess.Popen
    def _silent_popen(*args, **kwargs):
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        else:
            kwargs["creationflags"] |= 0x08000000
        return _orig_popen(*args, **kwargs)
    subprocess.Popen = _silent_popen

from multiprocessing import freeze_support
from launch import launch

if __name__ == "__main__":
    freeze_support()
    launch()
