"""ForzaETH car configs: pydantic schemas and path-based loaders, no ROS.

The values live with the stack (``stack_master/config/<car>/``), this package only
knows their shape and the directory convention (``ConfigTree``). A ROS layer adds the
package lookup on top::

    tree = ConfigTree(<stack_master>/config)        # rospkg or ament_index finds it
    load_car_config(tree.car_model("NUC5"))
    load_pacejka_tire_config(tree.pacejka("NUC5", "dubi"))
"""
from .archive import write_archived
from .car import CarConfig, load_car_config
from .steering_lut import load_steering_lut, save_steering_lut
from .tire import PacejkaTireConfig, load_pacejka_tire_config, save_pacejka_tire_config
from .trailing import TrailingConfig, load_trailing_config
from .tree import ConfigTree, NotExistingFloor
from .yaml_io import StrictLoader, load_model, strict_safe_load

__all__ = [
    "CarConfig", "load_car_config",
    "PacejkaTireConfig", "load_pacejka_tire_config", "save_pacejka_tire_config",
    "TrailingConfig", "load_trailing_config",
    "load_steering_lut", "save_steering_lut",
    "ConfigTree", "NotExistingFloor",
    "StrictLoader", "strict_safe_load", "load_model", "write_archived",
]
