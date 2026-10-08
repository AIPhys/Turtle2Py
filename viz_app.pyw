"""Double-click launcher for the Turtle2Py Viz GUI (pythonw, no console)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from turtle2py.viz.app import main

main()
