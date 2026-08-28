import os
import subprocess
import sys

base = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
subprocess.Popen([sys.executable, os.path.join(base, "login_gui.py")], cwd=base)