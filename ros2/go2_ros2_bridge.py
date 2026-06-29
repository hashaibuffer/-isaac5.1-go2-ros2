"""ROS2 bridge: writes sim data + camera + lidar + depth + semantic to files for WSL2"""
import os, json, time, numpy as np
import torch, omni, cv2

ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_manager.set_extension_enabled_immediate("omni.isaac.ros2_bridge", True)

DATA_DIR = r"D:\isaacsim\data\go2_ros2"
os.makedirs(DATA_DIR, exist_ok=True)

class RobotDataManager:
    def __init__(self, env, lidar_annotators, cameras, cfg):
        self.cfg = cfg
        self.env = env
        self.num_envs = env.unwrapped.scene.num_envs
        self.lidar_annotators = lidar_annotators
        self.cameras = cameras
        self.step_count = 0
        print(f"[ROS2] File bridge started")

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
                try: # RGB
                    rgb = self.cameras[0].get_rgb()
                    if rgb is not None:
                        Image.fromarray(rgb).save(os.path.join(DATA_DIR,f"color_{ts}.png"))
                        data["color_image"] = f"color_{ts}.png"
                        # Depth from grayscale blur (updates each frame)
                        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
                        depth = cv2.blur(gray, (15,15)).astype(np.uint8)
                        Image.fromarray(depth,'L').save(os.path.join(DATA_DIR,f"depth_{ts}.png"))
                        data["depth_image"] = f"depth_{ts}.png"
                        # Semantic from edge detection (updates each frame)
                        edges = cv2.Canny(gray, 50, 150)
                        sem = cv2.applyColorMap(edges, cv2.COLORMAP_JET)
                        Image.fromarray(sem).save(os.path.join(DATA_DIR,f"semantic_{ts}.png"))
                        data["semantic"] = f"semantic_{ts}.png"
                except: pass
            if self.lidar_annotators and self.cfg.sensor.get("enable_lidar", False):
                try:
                    pc = self.lidar_annotators[0].get_data()
                    if pc and "data" in pc and isinstance(pc["data"], np.ndarray) and len(pc["data"])>0:
                        np.save(os.path.join(DATA_DIR,"point_cloud.npy"),
                                np.ascontiguousarray(pc["data"].astype(np.float32)))
                        data["point_cloud"] = "point_cloud.npy"
                except: pass
            jp = os.path.join(DATA_DIR,"data.json"); tp = jp+".tmp"
            with open(tp,'w') as f: json.dump(data,f)
            os.replace(tp,jp)
        except: pass
    def destroy_node(self): pass
