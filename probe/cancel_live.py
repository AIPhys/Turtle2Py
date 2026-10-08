"""Live-Popen cancel test: kill a running Turtle child mid-flight and abort the pipeline."""

import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from turtle2py.viz import fork  # noqa: E402

work = ROOT / "probe" / "_cancel_live"
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)
inp = work / "cancel_demo.dat"
shutil.copy(ROOT / "demo_channel.dat", inp)

# instrument _kill_tree to capture the taskkill result
kill_info = {}
_orig_kill = fork._kill_tree


def spy_kill(p):
    if sys.platform == "win32":
        r = subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(p.pid)],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        kill_info["pid"] = p.pid
        kill_info["rc"] = r.returncode
        kill_info["out"] = r.stdout.decode("cp1251", "replace").strip()
    else:
        p.terminate()


fork._kill_tree = spy_kill

result = {}


def worker():
    try:
        fork.fork(inp, rays=20000, engine="py", log=lambda m: print(f"  [fork] {m}"))
        result["ok"] = True
    except SystemExit as e:
        result["ok"] = False
        result["exc"] = f"SystemExit: {e}"
    except BaseException as e:
        result["ok"] = False
        result["exc"] = f"{type(e).__name__}: {e}"


th = threading.Thread(target=worker, daemon=True)
th.start()

# wait until a live child process is in flight
proc = None
t0 = time.time()
while time.time() - t0 < 60:
    p = fork._PROC
    if p is not None and p.poll() is None:
        proc = p
        break
    time.sleep(0.1)
if proc is None:
    print("FAIL: no live Popen observed within 60 s")
    sys.exit(1)
print(f"live Popen pid={proc.pid} running for {time.time() - t0:.1f} s -> cancel()")

t0 = time.time()
killed = fork.cancel()
th.join(timeout=120)
dt = time.time() - t0

# child must be dead
child_rc = proc.poll()
# any surviving python -m turtle2py for this deck?
ps = subprocess.run(
    [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -like '*cancel_demo*' -or $_.CommandLine -like '*turtle2py*' } | "
        "Select-Object -ExpandProperty CommandLine",
    ],
    capture_output=True,
)
leftover = [
    ln for ln in ps.stdout.decode("utf-8", "replace").splitlines() if ln.strip()
]

print(f"cancel() returned: {killed}")
print(f"taskkill: rc={kill_info.get('rc')} out={kill_info.get('out')!r}")
print(f"thread ended in {dt:.1f} s, result={result}")
print(f"child poll() after cancel: {child_rc}")
print(f"leftover turtle2py python processes: {leftover}")

ok = (
    killed is True
    and result.get("exc") == "SystemExit: cancelled"
    and child_rc is not None
    and kill_info.get("rc") == 0
    and not leftover
)
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
