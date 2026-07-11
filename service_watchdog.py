import subprocess, time, sys, os

def start_watchdog():
    proc = subprocess.Popen([sys.executable, "employee.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    proc.wait()

if __name__ == "__main__":
    start_watchdog()