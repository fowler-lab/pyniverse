import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

if "MPLCONFIGDIR" not in os.environ:
    _MPL_CONFIG_DIR = Path(__file__).resolve().parent / ".mplconfig"
    _MPL_CONFIG_DIR.mkdir(exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(_MPL_CONFIG_DIR)
