"""ROS2 bridge: writes sim data for WSL2, reads cmd_vel from WSL2 to control robot"""
import os, json, time, numpy as np
import torch, omni, cv2

ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_manager.set_extension_enabled_immediate("isaacsim.ros2.bridge", True)

DATA_DIR = r"D:\isaac-sim\data\go2_ros2"
os.makedirs(DATA_DIR, exist_ok=True)
CMD_VEL_FILE = os.path.join(DATA_DIR, "cmd_vel.json")

# Keep track of last cmd_vel to avoid repeated file reads
_last_cmd_vel_mtime = 0


class RobotDataManager:
    def __init__(self, env, lidar_annotators, cameras, cfg):
        self.cfg = cfg
        self.env = env
        self.num_envs = env.unwrapped.scene.num_envs
        self.lidar_annotators = lidar_annotators
        self.cameras = cameras
        self.step_count = 0
        print(f"[ROS2] File bridge started")

    def check_cmd_vel(self):
        """Read cmd_vel from shared file and apply to robot control.
        Called each simulation step from the main loop.
        """
        global _last_cmd_vel_mtime
        try:
            if os.path.exists(CMD_VEL_FILE):
                mtime = os.path.getmtime(CMD_VEL_FILE)
                if mtime > _last_cmd_vel_mtime:
                    _last_cmd_vel_mtime = mtime
                    with open(CMD_VEL_FILE, "r") as f:
                        cmd = json.load(f)
                    import go2.go2_ctrl as go2_ctrl
                    num_envs = go2_ctrl.base_vel_cmd_input.shape[0] if go2_ctrl.base_vel_cmd_input is not None else 1
                    # Apply to selected robot (index 0 by default, or the selected robot)
                    selected = go2_ctrl.selected_robot
                    if go2_ctrl.base_vel_cmd_input is not None and selected < num_envs:
                        go2_ctrl.base_vel_cmd_input[selected] = torch.tensor(
                            [cmd.get("linear_x", 0.0),
                             cmd.get("linear_y", 0.0),
                             cmd.get("angular_z", 0.0)],
                            dtype=torch.float32
                        )
                        print(f"\r[cmd_vel] robot={selected} lin=({cmd.get('linear_x',0):.2f},{cmd.get('linear_y',0):.2f}) ang={cmd.get('angular_z',0):.2f}", end='', flush=True)
        except Exception as e:
            # Silently handle issues like partial writes from WSL2
            pass

    def pub_ros2_data(self):
        self.step_count += 1
        if self.step_count % 3 != 0: return
        frame_id = self.step_count // 3
        try:
            scene = self.env.unwrapped.scene
            rs = scene["unitree_go2"].data.root_state_w
            pos = rs[0, :3].cpu().numpy()
            ori = rs[0, 3:7].cpu().numpy()
            ts = str(int(time.time()*1000))
            data = {"timestamp": time.time(), "frame": frame_id, "ts": ts, "num_envs": self.num_envs,
                    "odom": {"position": [float(pos[0]),float(pos[1]),float(pos[2])],
                             "orientation": [float(ori[1]),float(ori[2]),float(ori[3]),float(ori[0])],
                             "frame_id": "odom","child_frame_id":"unitree_go2/base_link"}}
            if self.cameras and self.cfg.sensor.get("enable_camera", False):
                from PIL import Image
                try:
                    rgb = self.cameras[0].get_rgb()
                    if rgb is not None:
                        Image.fromarray(rgb).save(os.path.join(DATA_DIR,f"color_{ts}.png"))
                        data["color_image"] = f"color_{ts}.png"
                        # Depth: try real depth, fallback to gray blur
                        try:
                            depth = self.cameras[0].get_depth()
                            if depth is not None:
                                depth_norm = cv2.normalize(depth, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                                Image.fromarray(depth_norm, 'L').save(os.path.join(DATA_DIR,f"depth_{ts}.png"))
                                data["depth_image"] = f"depth_{ts}.png"
                            else:
                                raise ValueError("depth is None")
                        except Exception:
                            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                            depth = cv2.blur(gray, (15,15)).astype(np.uint8)
                            Image.fromarray(depth,'L').save(os.path.join(DATA_DIR,f"depth_{ts}.png"))
                            data["depth_image"] = f"depth_{ts}.png"
                        # Semantic from edge detection
                        edges = cv2.Canny(rgb, 50, 150)
                        sem = cv2.applyColorMap(edges, cv2.COLORMAP_JET)
                        Image.fromarray(sem).save(os.path.join(DATA_DIR,f"semantic_{ts}.png"))
                        data["semantic"] = f"semantic_{ts}.png"
                except Exception as e:
                    print(f"[DEBUG] camera error: {e}")
            if self.lidar_annotators and self.cfg.sensor.get("enable_lidar", False):
                try:
                    pc = self.lidar_annotators[0].get_data()
                    if pc is None:
                        pass
                    elif isinstance(pc, dict):
                        # Try point cloud from 'data' key first (IsaacExtract / pointcloud annotator)
                        pts = pc.get("data", None)
                        if isinstance(pts, np.ndarray) and pts.size > 0:
                            pts_out = np.ascontiguousarray(pts.astype(np.float32))
                            if pts_out.ndim == 2 and pts_out.shape[1] >= 3:
                                np.save(os.path.join(DATA_DIR,"point_cloud.npy"), pts_out)
                                data["point_cloud"] = "point_cloud.npy"
                        else:
                            # Try scan buffer format (distance, azimuth, elevation)
                            dist = pc.get("distance", None)
                            az = pc.get("azimuth", None)
                            el = pc.get("elevation", None)
                            if all(isinstance(x, np.ndarray) and x.size > 0 for x in [dist, az, el]):
                                r = dist.astype(np.float32).ravel()
                                a = az.astype(np.float32).ravel()
                                e = el.astype(np.float32).ravel()
                                valid = (r > 0) & np.isfinite(r) & np.isfinite(a) & np.isfinite(e)
                                r, a, e = r[valid], a[valid], e[valid]
                                if len(r) > 0:
                                    cos_e = np.cos(e)
                                    xyz = np.column_stack([r * cos_e * np.sin(a),
                                                           r * cos_e * np.cos(a),
                                                           r * np.sin(e)])
                                    np.save(os.path.join(DATA_DIR,"point_cloud.npy"),
                                            np.ascontiguousarray(xyz))
                                    data["point_cloud"] = "point_cloud.npy"
                except Exception as e:
                    print(f"[DEBUG] lidar error: {e}")
            jp = os.path.join(DATA_DIR,"data.json")
            with open(jp,'w') as f:
                json.dump(data,f)
        except Exception as e:
            print(f"[DEBUG] bridge pub_ros2_data error: {e}")

    def destroy_node(self):
        pass
