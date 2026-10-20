"""Round trips on a config tree built in tmp_path, plus the real tree when
PBL_CONFIG_TREE points at a <stack_master>/config directory."""
import os
from pathlib import Path

import numpy as np
import pytest
import yaml
from pydantic import ValidationError

from pbl_config import (CarConfig, ConfigTree, NotExistingFloor, PacejkaTireConfig,
                        load_car_config, load_pacejka_tire_config, load_steering_lut,
                        load_trailing_config, save_pacejka_tire_config, save_steering_lut,
                        strict_safe_load)

CAR = dict(m=3.695, Iz=0.05797, lf=0.170, lr=0.151, wheelbase=0.321, width_m=0.29, h_cg=0.014,
           a_max=3, a_min=-3, v_max=15.0, v_min=-5.0, C_0d=0.48, C_d=-1.1, C_acc=8.29, C_dec=5.77,
           C_R=2.03, C_0v=100, C_v=20, tau_steer=0.15779476, max_steering_angle=0.4189,
           min_radius_curv_m=0.75, max_steering_velocity=3.2, racecar_version="NUC5")
TIRE = dict(Bf=4.142, Br=4.8721, Cf=0.4375, Cr=2.1651, Df=2.6476, Dr=1.057, Ef=0.2332, Er=1.692,
            floor="dubi", friction_coeff=1.0)
TRAILING = dict(allow_accel_trailing=False, trailing_mode=True, prioritize_dyn=True, trailing_gap=2.0,
                trailing_p_gain=1.0, trailing_i_gain=0.0, trailing_d_gain=0.2, blind_trailing_speed=1.5)


@pytest.fixture
def tree(tmp_path):
    car = tmp_path / "NUC5"
    (car / "pacejka" / "dubi").mkdir(parents=True)
    (car / "car_model.yaml").write_text(yaml.dump(CAR))
    (car / "trailing_params.yaml").write_text(yaml.dump(TRAILING))
    (car / "pacejka" / "dubi" / "default.yaml").write_text(yaml.dump(TIRE))
    return ConfigTree(tmp_path)


def test_duplicate_key_is_an_error():
    with pytest.raises(yaml.YAMLError, match="duplicate key"):
        strict_safe_load("a: 1\nb: 2\na: 3\n")
    assert strict_safe_load("a: 1\nnested:\n  c: 3\n") == {"a": 1, "nested": {"c": 3}}


def test_car_round_trip_and_tree(tree):
    cfg = load_car_config(tree.car_model("NUC5"))
    assert cfg.tau_steer == pytest.approx(0.15779476)
    assert cfg.model_dump() == CAR
    assert tree.cars() == ["NUC5"]
    assert load_trailing_config(tree.trailing("NUC5")).trailing_gap == 2.0


def test_schema_errors_name_the_file(tree):
    path = tree.car_model("NUC5")
    path.write_text(yaml.dump({**CAR, "typo_key": 1}))
    with pytest.raises(ValidationError) as exc:
        load_car_config(path)
    assert str(path) in str(exc.value) and "typo_key" in str(exc.value)
    bad = dict(CAR)
    del bad["Iz"]
    path.write_text(yaml.dump(bad))
    with pytest.raises(ValidationError, match="Iz"):
        load_car_config(path)
    path.write_text(yaml.dump({**CAR, "tau_steer": 0.0}))
    with pytest.raises(ValidationError, match="tau_steer"):
        load_car_config(path)
    path.write_text("- just\n- a list\n")
    with pytest.raises(ValueError, match="mapping"):
        load_car_config(path)


def test_pacejka_floors_and_archive(tree):
    assert load_pacejka_tire_config(tree.pacejka("NUC5", "dubi")).Df == 2.6476
    with pytest.raises(NotExistingFloor, match="dubi"):
        tree.pacejka("NUC5", "winti")
    # a car without any pacejka data is a plain missing file, not a floor problem
    (tree.root / "NUC9").mkdir()
    assert not tree.pacejka("NUC9", "dubi").exists()

    new = PacejkaTireConfig(**{**TIRE, "Df": 3.0})
    written = save_pacejka_tire_config(new, tree.pacejka_dir("NUC5", "dubi"))
    assert written.parent.name == "archive" and written.name.endswith("_pacejka.yaml")
    default = tree.pacejka("NUC5", "dubi")
    assert default.is_symlink() and os.readlink(default) == f"archive/{written.name}"
    assert load_pacejka_tire_config(default).Df == 3.0


def test_steering_lut_round_trip(tree):
    table = np.array([[np.nan, 1.0, 2.0], [0.1, 0.5, 1.1], [0.2, 0.9, np.nan]])
    folder = tree.lut_dir("NUC5", "dubi")
    save_steering_lut(table, folder)
    back = load_steering_lut(tree.steering_lut("NUC5", "dubi"))
    np.testing.assert_array_equal(np.isnan(back), np.isnan(table))
    np.testing.assert_allclose(np.nan_to_num(back), np.nan_to_num(table))


@pytest.mark.skipif("PBL_CONFIG_TREE" not in os.environ, reason="set PBL_CONFIG_TREE=<stack_master>/config")
def test_real_tree_loads():
    tree = ConfigTree(os.environ["PBL_CONFIG_TREE"])
    cars = tree.cars()
    assert cars, f"no car_model.yaml under {tree.root}"
    for car in cars:
        assert isinstance(load_car_config(tree.car_model(car)), CarConfig)
        if tree.trailing(car).exists():
            load_trailing_config(tree.trailing(car))
        pacejka = tree.car_dir(car) / "pacejka"
        for floor in (p.name for p in pacejka.iterdir() if p.is_dir()) if pacejka.is_dir() else ():
            load_pacejka_tire_config(tree.pacejka(car, floor))
