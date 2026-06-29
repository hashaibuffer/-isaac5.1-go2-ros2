import os
import sys
import types
import hydra
import torch
import time
import math
import argparse

# Set ROS2 environment variables BEFORE any Isaac Sim imports
os.environ["ROS_DISTRO"] = "humble"
os.environ["ROS_DOMAIN_ID"] = "42"
os.environ["ROS_LOCALHOST_ONLY"] = "0"
os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp")
os.environ["ROS_DISCOVERY_SERVER"] = "192.168.50.205:11811"
os.environ["FASTRTPS_DEFAULT_PROFILES_FILE"] = r"D:\isaacsim\data\fastdds_discovery.xml"
_ros2_lib = os.path.join(os.environ.get("ISAAC_PATH", "D:/isaacsim"),
                         "exts/isaacsim.ros2.bridge", "humble", "lib")
if os.path.exists(_ros2_lib):
    os.environ["PATH"] = _ros2_lib + ";" + os.environ.get("PATH", "")
_ros2_dll = os.path.join(os.environ.get("ISAAC_PATH", "D:/isaacsim"),
                          "exts/isaacsim.ros2.bridge", "humble", "rclpy")
if os.path.exists(_ros2_dll):
    os.environ["PATH"] = _ros2_dll + ";" + os.environ.get("PATH", "")

# Workaround: h5py DLL conflicts with Isaac Sim's sensor extensions (omni.sensors.nv.common)
# Create a mock h5py module to satisfy import dependencies without loading native DLLs
# The recording features that need h5py won't be used in this simulation.
_mock_h5py = types.ModuleType('h5py')
_mock_h5py.__version__ = '0.0.0'
_mock_h5py.__file__ = '<mock>'
_mock_h5py.h5 = types.ModuleType('h5py.h5')
_mock_h5py.h5.get_config = lambda: None
_mock_h5py.File = lambda *a, **kw: None
_mock_h5py.h5z = types.ModuleType('h5py.h5z')
_mock_h5py.h5a = types.ModuleType('h5py.h5a')
_mock_h5py.h5d = types.ModuleType('h5py.h5d')
_mock_h5py.h5ds = types.ModuleType('h5py.h5ds')
_mock_h5py.h5f = types.ModuleType('h5py.h5f')
_mock_h5py.h5g = types.ModuleType('h5py.h5g')
_mock_h5py.h5i = types.ModuleType('h5py.h5i')
_mock_h5py.h5l = types.ModuleType('h5py.h5l')
_mock_h5py.h5o = types.ModuleType('h5py.h5o')
_mock_h5py.h5p = types.ModuleType('h5py.h5p')
_mock_h5py.h5pl = types.ModuleType('h5py.h5pl')
_mock_h5py.h5r = types.ModuleType('h5py.h5r')
_mock_h5py.h5s = types.ModuleType('h5py.h5s')
_mock_h5py.h5t = types.ModuleType('h5py.h5t')
_mock_h5py.h5ac = types.ModuleType('h5py.h5ac')
_mock_h5py._errors = types.ModuleType('h5py._errors')
_mock_h5py._objects = types.ModuleType('h5py._objects')
_mock_h5py._conv = types.ModuleType('h5py._conv')
_mock_h5py.utils = types.ModuleType('h5py.utils')
_mock_h5py._proxy = types.ModuleType('h5py._proxy')
_mock_h5py._selector = types.ModuleType('h5py._selector')
_mock_h5py.defs = types.ModuleType('h5py.defs')
_mock_h5py._npystrings = types.ModuleType('h5py._npystrings')
sys.modules['h5py'] = _mock_h5py
sys.modules['h5py.h5'] = _mock_h5py.h5
sys.modules['h5py.h5z'] = _mock_h5py.h5z
sys.modules['h5py.h5a'] = _mock_h5py.h5a
sys.modules['h5py.h5d'] = _mock_h5py.h5d
sys.modules['h5py.h5ds'] = _mock_h5py.h5ds
sys.modules['h5py.h5f'] = _mock_h5py.h5f
sys.modules['h5py.h5g'] = _mock_h5py.h5g
sys.modules['h5py.h5i'] = _mock_h5py.h5i
sys.modules['h5py.h5l'] = _mock_h5py.h5l
sys.modules['h5py.h5o'] = _mock_h5py.h5o
sys.modules['h5py.h5p'] = _mock_h5py.h5p
sys.modules['h5py.h5pl'] = _mock_h5py.h5pl
sys.modules['h5py.h5r'] = _mock_h5py.h5r
sys.modules['h5py.h5s'] = _mock_h5py.h5s
sys.modules['h5py.h5t'] = _mock_h5py.h5t
sys.modules['h5py.h5ac'] = _mock_h5py.h5ac
sys.modules['h5py._errors'] = _mock_h5py._errors
sys.modules['h5py._objects'] = _mock_h5py._objects
sys.modules['h5py._conv'] = _mock_h5py._conv
sys.modules['h5py.utils'] = _mock_h5py.utils
sys.modules['h5py._proxy'] = _mock_h5py._proxy
sys.modules['h5py._selector'] = _mock_h5py._selector
sys.modules['h5py.defs'] = _mock_h5py.defs
sys.modules['h5py._npystrings'] = _mock_h5py._npystrings
print("[INFO] h5py: Using mock module (HDF5 recording disabled)")

# Setup ROS2 environment (must be done before starting SimApp)
ROS2_AVAILABLE = False
try:
    ISAAC_PATH = os.environ.get("ISAAC_PATH", "D:/isaacsim")
    ros2_ext = os.path.join(ISAAC_PATH, "exts/isaacsim.ros2.bridge")
    # Set up PATH for ROS2 native DLLs
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp")
    lib_dir = os.path.join(ros2_ext, "humble", "lib")
    if os.path.exists(lib_dir):
        os.environ["PATH"] = lib_dir + ";" + os.environ.get("PATH", "")
    # Add ROS2 DLLs to PATH (needed for type support)
    lib_dir = os.path.join(ros2_ext, "humble", "lib")
    if os.path.exists(lib_dir):
        os.environ["PATH"] = lib_dir + ";" + os.environ.get("PATH", "")
    rclpy_lib = os.path.join(ros2_ext, "humble", "rclpy")
    if os.path.exists(rclpy_lib):
        os.environ["PATH"] = rclpy_lib + ";" + os.environ.get("PATH", "")
    print("[INFO] ROS2 environment configured")
except Exception as e:
    print(f"[INFO] ROS2 setup skipped: {e}")

from isaaclab.app import AppLauncher

# add argparse arguments
parser = argparse.ArgumentParser(description="Tutorial on running the cartpole RL environment.")

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli = parser.parse_args()

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import torch

from go2.go2_env import Go2RSLEnvCfg, camera_follow
import env.sim_env as sim_env
import go2.go2_sensors as go2_sensors
import omni
import carb
import go2.go2_ctrl as go2_ctrl

# Try to import ROS2 - use Isaac Sim's bundled ROS2 bridge
ROS2_AVAILABLE = False
ros2_bridge_module = None
try:
    # Import ROS2 bridge modules using direct loader
    import sys
    import importlib.util
    ISAAC_PATH = os.environ.get("ISAAC_PATH", "D:/isaacsim")
    ros2_ext = os.path.join(ISAAC_PATH, "exts/isaacsim.ros2.bridge")

    # Set up ROS2 environment (critical: must be done before importing rclpy)
    os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_fastrtps_cpp")
    lib_dir = os.path.join(ros2_ext, "humble", "lib")
    if os.path.exists(lib_dir):
        os.environ["PATH"] = lib_dir + ";" + os.environ.get("PATH", "")
    # Add rclpy directory to sys.path (parent of the actual rclpy package dir)
    rclpy_parent = os.path.join(ros2_ext, "humble", "rclpy")
    if os.path.exists(rclpy_parent) and rclpy_parent not in sys.path:
        sys.path.append(rclpy_parent)

    # Helper to load module from file
    def _load_module(name, path):
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(name, path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            return mod
        return None

    print("[INFO] Isaac Sim ROS2 bridge found")

    import ros2.go2_ros2_bridge as go2_ros2_bridge
    ROS2_AVAILABLE = True
    print("[INFO] ROS2 bridge enabled via native OmniGraph nodes")
    print("[INFO] Run in WSL2: rviz2 -d /path/to/isaac-go2-ros2/rviz/go2.rviz")
except (ImportError, ModuleNotFoundError) as e:
    ROS2_AVAILABLE = False
    print(f"[INFO] ROS2 not available - running without ROS2 bridge")
    print(f"[INFO]   Reason: {e}")
    print("[INFO] To enable ROS2, ensure ROS2 bridge extension is available")

FILE_PATH = os.path.join(os.path.dirname(__file__), "cfg")
@hydra.main(config_path=FILE_PATH, config_name="sim", version_base=None)
def run_simulator(cfg):

    # Go2 Environment setup
    go2_env_cfg = Go2RSLEnvCfg()
    go2_env_cfg.scene.num_envs = cfg.num_envs
    go2_env_cfg.decimation = math.ceil(1./go2_env_cfg.sim.dt/cfg.freq)
    go2_env_cfg.sim.render_interval = go2_env_cfg.decimation
    go2_ctrl.init_base_vel_cmd(cfg.num_envs)
    # env, policy = go2_ctrl.get_rsl_flat_policy(go2_env_cfg)
    env, policy = go2_ctrl.get_rsl_rough_policy(go2_env_cfg)

    # Simulation environment
    if (cfg.env_name == "obstacle-dense"):
        sim_env.create_obstacle_dense_env() # obstacles dense
    elif (cfg.env_name == "obstacle-medium"):
        sim_env.create_obstacle_medium_env() # obstacles medium
    elif (cfg.env_name == "obstacle-sparse"):
        sim_env.create_obstacle_sparse_env() # obstacles sparse
    elif (cfg.env_name == "warehouse"):
        sim_env.create_warehouse_env() # warehouse
    elif (cfg.env_name == "warehouse-forklifts"):
        sim_env.create_warehouse_forklifts_env() # warehouse forklifts
    elif (cfg.env_name == "warehouse-shelves"):
        sim_env.create_warehouse_shelves_env() # warehouse shelves
    elif (cfg.env_name == "full-warehouse"):
        sim_env.create_full_warehouse_env() # full warehouse

    # Sensor setup
    sm = go2_sensors.SensorManager(cfg.num_envs)
    lidar_annotators = sm.add_rtx_lidar()
    cameras = sm.add_camera(cfg.freq)

    # Keyboard control
    system_input = carb.input.acquire_input_interface()
    system_input.subscribe_to_keyboard_events(
        omni.appwindow.get_default_app_window().get_keyboard(), go2_ctrl.sub_keyboard_event)

    # ROS2 Bridge (optional)
    if ROS2_AVAILABLE:
        try:
            dm = go2_ros2_bridge.RobotDataManager(env, lidar_annotators, cameras, cfg)
        except Exception as e:
            print(f"[WARN] ROS2 bridge init failed: {e}")
            dm = None
    else:
        dm = None

    # Print controls
    print(f"[INFO] {cfg.num_envs} Go2 robots spawned")
    print(f"[INFO] Press 1/2/3 or F1/F2/F3 to select robot, WASDZC to control")
    print(f"[INFO]       1-9 or F1-F9 select robots 0-8")
    print(f"[INFO]       W:Fwd A:Left S:Back D:Right Z:LeftTurn C:RightTurn")

    # Run simulation
    sim_step_dt = float(go2_env_cfg.sim.dt * go2_env_cfg.decimation)
    obs, _ = env.reset()
    while simulation_app.is_running():
        start_time = time.time()
        with torch.inference_mode():
            # control joints
            actions = policy(obs)

            # step the environment
            obs, _, _, _ = env.step(actions)

            # ROS2 data (optional)
            if ROS2_AVAILABLE and dm is not None:
                dm.pub_ros2_data()

            # Camera follow
            if (cfg.camera_follow):
                camera_follow(env)

            # limit loop time
            elapsed_time = time.time() - start_time
            if elapsed_time < sim_step_dt:
                sleep_duration = sim_step_dt - elapsed_time
                time.sleep(sleep_duration)
        actual_loop_time = time.time() - start_time
        rtf = min(1.0, sim_step_dt/elapsed_time)
        print(f"\rStep time: {actual_loop_time*1000:.2f}ms, Real Time Factor: {rtf:.2f}", end='', flush=True)

    if ROS2_AVAILABLE and dm is not None:
        dm.destroy_node()
    simulation_app.close()

if __name__ == "__main__":
    run_simulator()
    