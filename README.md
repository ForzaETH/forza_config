# pbl_config

Pydantic schemas and path-based loaders for the ForzaETH car configs. No ROS.

| File | Schema | Load | Save |
|---|---|---|---|
| `car_model.yaml` | `CarConfig` | `load_car_config(path)` | hand-maintained |
| `pacejka/<floor>/default.yaml` | `PacejkaTireConfig` | `load_pacejka_tire_config(path)` | `save_pacejka_tire_config(cfg, folder)` |
| `LUT/<floor>/default.csv` | numpy array | `load_steering_lut(path)` | `save_steering_lut(table, folder)` |
| `trailing_params.yaml` | `TrailingConfig` | `load_trailing_config(path)` | hand-maintained |

Every schema is `extra='forbid'`: a missing or an extra key stops the load. A repeated
key in a yaml is an error too (`strict_safe_load`), not last-wins. `load_model(Model,
path)` is the generic loader the four above are built on; other packages use it for
their own schemas (forzaeth_mpc does for the MPC params).

## Values live with the stack

This package carries no yaml. The values are in the stack's `stack_master/config/<car>/`
and the package only knows that layout, through `ConfigTree`:

```python
from pbl_config import ConfigTree, load_car_config, load_pacejka_tire_config

tree = ConfigTree("/path/to/stack_master/config")
car = load_car_config(tree.car_model("NUC5"))
tire = load_pacejka_tire_config(tree.pacejka("NUC5", "dubi"))   # NotExistingFloor on a wrong floor
mpc_yaml = tree.file("NUC5", "single_track_mpc_params.yaml")    # any other per-car file
```

```
<root>/<car>/car_model.yaml
<root>/<car>/trailing_params.yaml
<root>/<car>/pacejka/<floor>/default.yaml  -> archive/YYYYMMDD_pacejka.yaml
<root>/<car>/LUT/<floor>/default.csv       -> archive/YYYYMMDD_lut.csv
```

The savers write a dated file into `archive/` and flip the `default.*` symlink to it,
so every identification stays on disk.

## ROS layers

A ROS package adds the package lookup and nothing else:

```python
# ROS 1
tree = ConfigTree(rospkg.RosPack().get_path("stack_master") + "/config")
# ROS 2 (the config folder is not mirrored into the install space, hence the source tree)
tree = ConfigTree(Path(get_package_share_directory("stack_master")).parents[3]
                  / "src/race_stack/stack_master/config")

def load_car_config_ros(car): return load_car_config(tree.car_model(car))
```

Anything that needs `rclpy`/`rospy` (parameter services, dynamic reconfigure) belongs
in that layer, not here.

## Errors

- `FileNotFoundError`: the file is not there.
- `NotExistingFloor` (a `ValueError`): the car has `pacejka/` or `LUT/` data but not for
  that floor. The message lists the floors it has.
- `yaml.YAMLError`: malformed yaml or a duplicate key.
- `pydantic.ValidationError`: schema mismatch. The title names the file, so a missing
  key reads `1 validation error for CarConfig (/.../NUC5/car_model.yaml)`.

## Install and test

```bash
pip install -e .
pytest                                                    # on a tree built in tmp_path
PBL_CONFIG_TREE=<stack_master>/config pytest -k real_tree # every car of a real tree
```

Python >= 3.8, pydantic 2, pyyaml, numpy.
