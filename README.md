# Isaac Sim Unitree Go2 ROS2 Simulation

基于 **Isaac Sim 4.5** + **Isaac Lab 2.1.0** 的 Unitree Go2 四足机器人仿真平台，支持多机器人控制、多种仿真环境切换，并通过文件桥接实现 **ROS2 话题可视化**（Windows 仿真 ↔ WSL2 ROS2 + RViz2）。

---

## 目录

- [系统概述](#系统概述)
- [环境配置](#环境配置)
  - [1. Conda 环境](#1-conda-环境)
  - [2. Isaac Lab 安装](#2-isaac-lab-安装)
  - [3. ROS2 Humble（WSL2）](#3-ros2-humblewsl2)
  - [4. WSL2 镜像网络配置](#4-wsl2-镜像网络配置)
- [运行仿真](#运行仿真)
- [键盘控制](#键盘控制)
  - [单机器人](#单机器人)
  - [多机器人切换](#多机器人切换)
- [仿真环境](#仿真环境)
  - [可用环境列表](#可用环境列表)
  - [配置方法](#配置方法)
- [ROS2 话题与可视化](#ros2-话题与可视化)
  - [文件桥接原理](#文件桥接原理)
  - [启动可视化](#启动可视化)
  - [可用话题列表](#可用话题列表)
  - [RViz2 配置](#rviz2-配置)
- [常见问题](#常见问题)

---

## 系统概述

| 组件 | 说明 |
|------|------|
| **仿真引擎** | NVIDIA Isaac Sim 4.5 |
| **机器人框架** | Isaac Lab 2.1.0 |
| **机器人模型** | Unitree Go2（四足机器人） |
| **控制方式** | 键盘实时操控 |
| **ROS2 集成** | 文件桥接 → WSL2 ROS2 Humble → RViz2 可视化 |
| **GPU** | NVIDIA RTX 5080（CUDA 13.0） |

---

## 环境配置

### 1. Conda 环境

```bash
# 创建 Python 3.10 环境
conda create -n isaaclab_env_2 python=3.10
conda activate isaaclab_env_2

# 安装基础依赖
pip install setuptools wheel
```

### 2. Isaac Lab 安装

```bash
# 安装 PyTorch（RTX 5080 需 CUDA 13.0 版本）
pip install torch==2.12.1+cu130 torchvision==0.27.1+cu130 ^
  --index-url https://download.pytorch.org/whl/cu130

# 安装其他依赖
pip install "numpy<2" "pillow==11.0.0"
pip install flatdict==4.0.1 --no-build-isolation
pip install rsl-rl-lib==2.3.1
pip install hydra-core matplotlib opencv-python<=4.10 scipy

# 从源码安装 Isaac Lab
cd D:\isaacsim\IsaacLab\source\isaaclab
pip install -e .
```

### 3. ROS2 Humble（WSL2）

在 **WSL2 Ubuntu 22.04** 中安装：

```bash
# 更换 apt 源为清华镜像（可选）
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak
sudo sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
sudo sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list
sudo apt update

# 安装 ROS2 Humble
sudo apt install -y ros-humble-desktop
sudo apt install -y ros-humble-nav-msgs ros-humble-sensor-msgs
sudo apt install -y ros-humble-tf2-ros ros-humble-cv-bridge
sudo apt install -y ros-humble-sensor-msgs-py

# 设置环境变量
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 4. WSL2 镜像网络配置

创建 `%USERPROFILE%\.wslconfig`：

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=false
autoProxy=true
```

重启 WSL2：

```cmd
wsl --shutdown
wsl
```

验证：

```bash
hostname -I
# 应显示与 Windows 主机相同的 IP 地址
```

---

## 运行仿真

### 一键启动（推荐）

双击 `run_go2.bat` 即可启动。

### 手动启动

```bash
conda activate isaaclab_env_2

set CARB_APP_PATH=D:\isaacsim\kit
set ISAAC_PATH=D:\isaacsim
set EXP_PATH=D:\isaacsim\apps
set PYTHONPATH=D:\isaacsim\site

cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
python isaac_go2_ros2.py
```

加载约 10-20 秒后出现 Isaac Sim 窗口和 Go2 机器人。

---

## 键盘控制

### 单机器人

| 按键 | 动作 |
|------|------|
| **W** | 前进 |
| **S** | 后退 |
| **A** | 左移 |
| **D** | 右移 |
| **Z** | 左旋转 |
| **C** | 右旋转 |

### 多机器人切换

`cfg/sim.yaml` 中设置 `num_envs: N`（N ≥ 2）后：

| 按键 | 功能 |
|------|------|
| **1 ~ 9** | 选择 Robot 0 ~ 8 |
| **F1 ~ F9** | 选择 Robot 0 ~ 8（备用） |
| **W/A/S/D/Z/C** | 控制当前选中的机器人 |

---

## 仿真环境

### 可用环境

| 环境名 | 说明 | 性能 |
|--------|------|------|
| `obstacle-sparse` | 稀疏障碍物（100 个） | ✅ RTF ~0.5 |
| `obstacle-medium` | 中等障碍物（200 个） | ✅ RTF ~0.5 |
| `obstacle-dense` | 密集障碍物（400 个） | ✅ RTF ~0.5 |
| `warehouse` | 简单仓库 | ✅ RTF ~0.3 |
| `warehouse-forklifts` | 仓库 + 叉车 | ✅ RTF ~0.3 |
| `warehouse-shelves` | 仓库 + 货架 | ✅ RTF ~0.3 |
| `full-warehouse` | 完整仓库 | ⚠️ 需 Nucleus 服务器 |

### 配置方法

编辑 `cfg/sim.yaml`：

```yaml
env_name: obstacle-dense   # 环境名称
num_envs: 1                 # 机器人数量
sensor:
  enable_lidar: True
  enable_camera: True
```

---

## ROS2 话题与可视化

### 文件桥接原理

```
Windows (Isaac Sim)                WSL2 (ROS2)
       │                                │
  写入数据到                      读取数据并发布
  共享文件目录                    为 ROS2 话题
       │                                │
       └── D:\isaacsim\data\go2_ros2 ───┘
```

### 启动可视化

**终端 1（Windows）**：

```bash
conda activate isaaclab_env_2
cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
python isaac_go2_ros2.py
```

**终端 2（WSL2）**：

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42

# 启动文件桥接（必须用系统 Python 3.10）
/usr/bin/python3 /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/ros2/go2_file_bridge_wsl2.py &

# 启动 RViz2
rviz2 -d /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/rviz/go2.rviz
```

### 可用话题列表

| 分类 | 话题 | 类型 | 说明 |
|------|------|------|------|
| 命令与控制 | `/unitree_go2/cmd_vel` | `geometry_msgs/Twist` | 发送速度指令控制机器人运动 |
| 前视摄像头 | `/unitree_go2/front_cam/color_image` | `sensor_msgs/Image` | RGB 彩色图像 (640x480, bgr8) |
| | `/unitree_go2/front_cam/depth_image` | `sensor_msgs/Image` | 深度图像 (伪深度, mono8) |
| | `/unitree_go2/front_cam/semantic_segmentation_image` | `sensor_msgs/Image` | 语义分割图像 (伪语义, bgr8) |
| | `/unitree_go2/front_cam/info` | `sensor_msgs/CameraInfo` | 相机内参信息 |
| 激光雷达 | `/unitree_go2/lidar/point_cloud` | `sensor_msgs/PointCloud2` | 激光雷达点云 (50000+ points) |
| 里程计与定位 | `/unitree_go2/odom` | `nav_msgs/Odometry` | 里程计数据 (位置/方向/速度) |
| | `/unitree_go2/pose` | `geometry_msgs/PoseStamped` | 机器人当前位姿 |

### RViz2 配置

**1. 设置 Fixed Frame**

左侧面板 → **Global Options** → **Fixed Frame** 改为 `odom`

**2. 添加可视化元素**

点击左下角 **Add** 按钮，按以下列表添加：

| 显示类型 | 话题/设置 | 用途 |
|---------|----------|------|
| **Grid** | 默认 | 地面网格 |
| **TF** | 自动 | 显示机器人坐标系树 |
| **Odometry** | `/unitree_go2/odom` | 里程计位置箭头 |
| **Pose** | `/unitree_go2/pose` | 机器人位姿 (Axes) |
| **PointCloud2** | `/unitree_go2/lidar/point_cloud` | 激光雷达点云 |
| **Image** × 3 | `/unitree_go2/front_cam/color_image` | RGB 彩色图像 |
| | `/unitree_go2/front_cam/depth_image` | 深度图像 |
| | `/unitree_go2/front_cam/semantic_segmentation_image` | 语义分割图像 |

**3. 发送速度指令**

```bash
# 在 WSL2 中发布速度指令
ros2 topic pub /unitree_go2/cmd_vel geometry_msgs/Twift   "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}" --once
```

**4. 保存配置**

File → Save Config As → 保存为 `go2.rviz`

---

## 常见问题

### 仿真启动报 `No module named 'isaacsim'`

设置环境变量：

```cmd
set PYTHONPATH=D:\isaacsim\site
```

### 键盘无反应

点击 Isaac Sim 窗口使其获得焦点。

### RViz2 看不到话题

```bash
ros2 topic list                    # 检查话题
ps aux | grep go2_file_bridge      # 确认桥接运行
echo $ROS_DOMAIN_ID                # 确认 = 42
```



## 项目结构

```
isaac-go2-ros2/
├── cfg/sim.yaml                   # 仿真配置
├── env/sim_env.py                 # 环境加载
├── go2/
│   ├── go2_ctrl.py                # 键盘控制
│   ├── go2_env.py                 # Go2 环境
│   └── go2_sensors.py             # 传感器
├── ros2/
│   ├── go2_ros2_bridge.py         # Windows 端桥接
│   └── go2_file_bridge_wsl2.py    # WSL2 端发布
├── rviz/go2.rviz                  # RViz2 配置
├── ckpts/unitree_go2/             # RL 策略模型
├── isaac_go2_ros2.py              # 主程序
└── run_go2.bat                    # 启动脚本
```


---

## 技术实现

### 1. 架构概述

```
+-----------------------------------------------------------------+
|                      Windows 主机                                |
|                                                                  |
|  +-------------+   +--------------------------------------+     |
|  | Isaac Sim   |   | Python 桥接 (go2_ros2_bridge.py)     |     |
|  | 4.5         |-->|                                      |     |
|  |             |   |  - 每 3 帧采集一次数据               |     |
|  |  - 物理仿真 |   |  - RGB -> PIL PNG                    |     |
|  |  - RL 策略  |   |  - 深度 -> cv2.blur (灰度模糊)       |     |
|  |  - 传感器   |   |  - 语义 -> cv2.Canny + COLORMAP     |     |
|  +-------------+   |  - 点云 -> numpy .npy                |     |
|                    |  - 里程计 -> JSON                     |     |
|                    +----------+---------------------------+     |
|                               | 共享文件                        |
|                    +----------v---------------------------+     |
|                    |  D:\isaacsim\data\go2_ros2\         |     |
|                    |  +-- data.json (元数据)               |     |
|                    |  +-- color_*.png (RGB)               |     |
|                    |  +-- depth_*.png (深度)              |     |
|                    |  +-- semantic_*.png (语义)           |     |
|                    |  +-- point_cloud.npy (点云)          |     |
|                    |  +-- cmd_vel.json (速度指令)          |     |
|                    +--------------------------------------+     |
+-----------------------------------------------------------------+
                               | WSL2 挂载 /mnt/d/
+------------------------------v----------------------------------+
|                      WSL2 Ubuntu 22.04                          |
|                                                                  |
|  +----------------------------------------------+               |
|  | ROS2 桥接 (go2_file_bridge_wsl2.py)          |               |
|  |                                              |               |
|  |  - 读取共享文件 -> 发布 ROS2 话题            |               |
|  |  - 订阅 cmd_vel -> 写入 cmd_vel.json         |               |
|  |  - 帧号检测更新（非 mtime）                  |               |
|  +--------------------+-------------------------+               |
|                       |                                         |
|              +--------v--------+        +--------v--------+     |
|              |  RViz2          |        |  ros2 CLI       |     |
|              |  可视化         |        |  调试/录制      |     |
|              +-----------------+        +-----------------+     |
+-----------------------------------------------------------------+
```

### 2. 关键代码改动

#### 2.1 多机器人选择控制 (go2/go2_ctrl.py)

**改动内容：** 将原固定键位映射改为数字键选择 + WASDZC 控制的通用模式。

**核心代码：**

```python
select_map = {'1':0,'2':1,'3':2,'F1':0,'F2':1,'F3':2,'KEY_1':0,...}
if key_name in select_map:
    selected_robot = select_map[key_name]
    base_vel_cmd_input.zero_()
# WASDZC 控制当前选中的机器人
base_vel_cmd_input[selected_robot] = ...
```

**解决的问题：** 原代码 Robot1 使用 IJKL 键，无法扩展至 Robot2+。

#### 2.2 h5py 模拟模块

**原因：** Isaac Sim 的 omni.sensors.nv.common 扩展的 HDF5 DLL 与 pip h5py 冲突。

**方案：** 创建 mock h5py 模块插入 sys.modules：

```python
_mock_h5py = types.ModuleType('h5py')
_mock_h5py.File = lambda *a,**kw: None
sys.modules['h5py'] = _mock_h5py
```

#### 2.3 PyTorch CUDA (RTX 5080)

**问题：** RTX 5080 (sm_120) 需要 PyTorch >= 2.7。

**解决：** 安装 PyTorch 2.12.1+cu130。
```bash
pip install torch==2.12.1+cu130 --index-url https://download.pytorch.org/whl/cu130
```

#### 2.4 地形颜色方案

**问题：** color_meshes_by_height 默认 colormap "turbo" 不存在。

**修复：** 改为 "viridis"。
```python
color_map = kwargs.pop("color_map", "viridis")
```

#### 2.5 仓库 USD 加载

**方案：** flatten + 本地缓存。
1. 下载基础 Props 到本地
2. 生成自包含扁平化 USD
3. 优先加载扁平化版本

#### 2.6 文件桥接

Windows -> 共享文件 -> WSL2 -> ROS2 topics

每帧使用递增 frame 号检测更新，替代 mtime 检测。

### 3. 依赖配置

| 包 | 版本 | 原因 |
|------|------|------|
| torch | 2.12.1+cu130 | RTX 5080 兼容 |
| numpy | <2.0 | Isaac Lab 要求 |
| opencv-python | <=4.10 | 深度/语义生成 |
| pillow | 11.0.0 | 图片编码 |
| rsl-rl-lib | 2.3.1 | RL 策略 |
| setuptools | <71 | flatdict 构建需要 pkg_resources |

### 4. 实现思路

- **多机器人控制**: 选中模式 + 统一 WASDZC
- **环境加载**: 程序化地形(完美) + USD flatten(仓库)
- **ROS2通信**: 文件桥接绕过 DDS 跨平台限制
- **深度/语义**: 从 RGB 实时生成，非真实传感器数据
- **帧同步**: frame 号检测确保每帧更新

### 5. 已知限制

1. 仓库环境需 Nucleus 服务器才能完整显示道具
2. 深度/语义为 RGB 生成数据，非真实传感器
3. 文件桥接约 100ms 延迟
