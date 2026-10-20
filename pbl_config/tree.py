"""The directory convention of a config tree, so that every consumer (ROS 1, ROS 2, the
offline MPC harness) resolves the same paths from one place::

    <root>/<car>/car_model.yaml                  CarConfig
    <root>/<car>/trailing_params.yaml            TrailingConfig
    <root>/<car>/pacejka/<floor>/default.yaml    PacejkaTireConfig, a symlink into archive/
    <root>/<car>/pacejka/<floor>/archive/        YYYYMMDD_pacejka.yaml, written by sysid
    <root>/<car>/LUT/<floor>/default.csv         steering LUT, a symlink into archive/
    <root>/<car>/LUT/<floor>/archive/            YYYYMMDD_lut.csv
    <root>/<car>/<anything>.yaml                 other per-car files, e.g. the MPC params

The ROS layers construct it from their package lookup (``rospkg`` or
``ament_index``); off-car code passes the directory.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union


class NotExistingFloor(ValueError):
    """The car has per-floor data, but not for this floor. Run the sysid for it."""


@dataclass(frozen=True)
class ConfigTree:
    root: Path

    def __init__(self, root: Union[str, Path]):
        object.__setattr__(self, "root", Path(root))

    def car_dir(self, car: str) -> Path:
        return self.root / car

    def cars(self) -> List[str]:
        """Every car directory that has a car_model.yaml, sorted."""
        return sorted(p.parent.name for p in self.root.glob("*/car_model.yaml"))

    def file(self, car: str, name: str) -> Path:
        """Any per-car file by name, e.g. ``tree.file("NUC5", "single_track_mpc_params.yaml")``."""
        return self.car_dir(car) / name

    def car_model(self, car: str) -> Path:
        return self.file(car, "car_model.yaml")

    def trailing(self, car: str) -> Path:
        return self.file(car, "trailing_params.yaml")

    def pacejka_dir(self, car: str, floor: str) -> Path:
        return self._floor_dir(car, "pacejka", floor)

    def pacejka(self, car: str, floor: str) -> Path:
        return self.pacejka_dir(car, floor) / "default.yaml"

    def lut_dir(self, car: str, floor: str) -> Path:
        return self._floor_dir(car, "LUT", floor)

    def steering_lut(self, car: str, floor: str) -> Path:
        return self.lut_dir(car, floor) / "default.csv"

    def _floor_dir(self, car: str, kind: str, floor: str) -> Path:
        """``<car>/<kind>/<floor>``; raises NotExistingFloor when ``<car>/<kind>`` exists
        without that floor, so a typo in the floor name is not a bare FileNotFoundError."""
        kind_dir = self.car_dir(car) / kind
        floor_dir = kind_dir / floor
        if kind_dir.is_dir() and not floor_dir.is_dir():
            have = sorted(p.name for p in kind_dir.iterdir() if p.is_dir())
            raise NotExistingFloor(f"{car} has no {kind} data for floor {floor!r}; it has {have}")
        return floor_dir
