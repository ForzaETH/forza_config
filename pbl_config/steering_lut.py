from pathlib import Path

import numpy as np

from .archive import write_archived
from .yaml_io import PathLike


def load_steering_lut(path: PathLike) -> np.ndarray:
    """``LUT/<floor>/default.csv`` at ``path``; see ``ConfigTree.steering_lut``.

    Row 0 holds the velocities, column 0 the steering angles, the cells the steady-state
    lateral acceleration (NaN where there is none).
    """
    return np.loadtxt(Path(path), delimiter=",")


def save_steering_lut(table: np.ndarray, folder: PathLike, update_latest: bool = True) -> Path:
    """Write ``folder/archive/<YYYYMMDD>_lut.csv`` and, with ``update_latest``, point
    ``folder/default.csv`` at it. ``folder`` is ``ConfigTree.lut_dir``."""
    return write_archived(folder, "lut.csv", lambda path: np.savetxt(path, table, delimiter=","),
                          update_latest)
