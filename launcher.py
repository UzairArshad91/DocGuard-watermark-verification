import subprocess, sys, os, time

base = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))

subprocess.Popen([sys.executable, os.path.join(base, "main.py")])
time.sleep(2)
subprocess.Popen([sys.executable, os.path.join(base, "service_watchdog.py")])
subprocess.Popen([sys.executable, os.path.join(base, "file_watcher.py")])
subprocess.Popen([sys.executable, os.path.join(base, "login_gui.py")])