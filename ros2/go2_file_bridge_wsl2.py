#!/usr/bin/env python3
"""
WSL2-side ROS2 publisher: reads sim data from shared files, publishes as ROS2 topics.
Run: /usr/bin/python3 go2_file_bridge_wsl2.py
"""
import json, time, os, sys, struct
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped, TransformStamped
from sensor_msgs.msg import Image, PointCloud2, PointField, CameraInfo
from sensor_msgs_py import point_cloud2
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import cv2
import numpy as np

DATA_DIR = "/mnt/d/isaacsim/data/go2_ros2"

class Go2Bridge(Node):
    def __init__(self):
        super().__init__("go2_file_bridge")
        self.odom_pub = self.create_publisher(Odometry, "/unitree_go2/odom", 10)
        self.pose_pub = self.create_publisher(PoseStamped, "/unitree_go2/pose", 10)
        self.img_pub = self.create_publisher(Image, "/unitree_go2/front_cam/color_image", 10)
        self.depth_pub = self.create_publisher(Image, "/unitree_go2/front_cam/depth_image", 10)
        self.semseg_pub = self.create_publisher(Image, "/unitree_go2/front_cam/semantic_segmentation_image", 10)
        self.lidar_pub = self.create_publisher(PointCloud2, "/unitree_go2/lidar/point_cloud", 10)
        self.cam_info_pub = self.create_publisher(CameraInfo, "/unitree_go2/front_cam/info", 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.bridge = CvBridge()
        self.last_frame = -1
        self.get_logger().info("Go2 Bridge started (camera + depth + semantic + lidar)")

    def publish_data(self):
        json_path = os.path.join(DATA_DIR, "data.json")
        if not os.path.exists(json_path):
            return

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
        except Exception:
            return

        frame = data.get("frame", 0)
        if frame == self.last_frame:
            return
        self.last_frame = frame

        now = self.get_clock().now().to_msg()
        odom_data = data.get("odom", {})
        pos = odom_data.get("position", [0,0,0])
        ori = odom_data.get("orientation", [0,0,0,1])

        # --- Odometry ---
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = "odom"
        odom.child_frame_id = "unitree_go2/base_link"
        odom.pose.pose.position.x = pos[0]
        odom.pose.pose.position.y = pos[1]
        odom.pose.pose.position.z = pos[2]
        odom.pose.pose.orientation.x = ori[0]
        odom.pose.pose.orientation.y = ori[1]
        odom.pose.pose.orientation.z = ori[2]
        odom.pose.pose.orientation.w = ori[3]
        self.odom_pub.publish(odom)

        # --- TF ---
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = "odom"
        t.child_frame_id = "unitree_go2/base_link"
        t.transform.translation.x = pos[0]
        t.transform.translation.y = pos[1]
        t.transform.translation.z = pos[2]
        t.transform.rotation.x = ori[0]
        t.transform.rotation.y = ori[1]
        t.transform.rotation.z = ori[2]
        t.transform.rotation.w = ori[3]
        self.tf_broadcaster.sendTransform(t)

        # --- Pose ---
        pose = PoseStamped()
        pose.header = odom.header
        pose.pose = odom.pose.pose
        self.pose_pub.publish(pose)

        # --- Camera Image ---
        img_name = data.get("color_image")
        if img_name:
            img_path = os.path.join(DATA_DIR, img_name)
            if os.path.exists(img_path):
                try:
                    cv_img = cv2.imread(img_path)
                    if cv_img is not None:
                        ros_img = self.bridge.cv2_to_imgmsg(cv_img, "bgr8")
                        ros_img.header.stamp = now
                        ros_img.header.frame_id = "unitree_go2/front_cam"
                        self.img_pub.publish(ros_img)

                        # Camera info
                        h, w = cv_img.shape[:2]
                        if h > 0 and w > 0:
                            cam_info = CameraInfo()
                            cam_info.header = ros_img.header
                            cam_info.height = h
                            cam_info.width = w
                            cam_info.distortion_model = "plumb_bob"
                            f = float(w)
                            cx = float(w) / 2.0
                            cy = float(h) / 2.0
                            cam_info.k = (f, 0.0, cx, 0.0, f, cy, 0.0, 0.0, 1.0)
                            self.cam_info_pub.publish(cam_info)
                except Exception as e:
                    self.get_logger().warn(f"Camera error: {e}")

        # --- Depth Image ---
        depth_name = data.get("depth_image")
        if depth_name:
            depth_path = os.path.join(DATA_DIR, depth_name)
            if os.path.exists(depth_path):
                try:
                    depth_cv = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
                    if depth_cv is not None:
                        ros_depth = self.bridge.cv2_to_imgmsg(depth_cv, "mono8")
                        ros_depth.header.stamp = now
                        ros_depth.header.frame_id = "unitree_go2/front_cam"
                        self.depth_pub.publish(ros_depth)
                except Exception as e:
                    self.get_logger().warn(f"Depth error: {e}")

        # --- Semantic Segmentation ---
        sem_name = data.get("semantic")
        if sem_name:
            sem_path = os.path.join(DATA_DIR, sem_name)
            if os.path.exists(sem_path):
                try:
                    sem_cv = cv2.imread(sem_path)
                    if sem_cv is not None:
                        ros_sem = self.bridge.cv2_to_imgmsg(sem_cv, "bgr8")
                        ros_sem.header.stamp = now
                        ros_sem.header.frame_id = "unitree_go2/front_cam"
                        self.semseg_pub.publish(ros_sem)
                except Exception as e:
                    self.get_logger().warn(f"Semantic error: {e}")

        # --- LiDAR Point Cloud ---
        pc_name = data.get("point_cloud")
        if pc_name:
            pc_path = os.path.join(DATA_DIR, pc_name)
            if os.path.exists(pc_path):
                try:
                    pts = np.load(pc_path)
                    if len(pts) > 0:
                        fields = [
                            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
                            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
                            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
                        ]
                        pc2 = point_cloud2.create_cloud(odom.header, fields, pts[:, :3])
                        self.lidar_pub.publish(pc2)
                except Exception as e:
                    self.get_logger().warn(f"Lidar error: {e}")

def main():
    rclpy.init()
    node = Go2Bridge()
    while rclpy.ok():
        node.publish_data()
        rclpy.spin_once(node, timeout_sec=0.05)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
