# Isaac Sim 5.1 — Unitree Go2 ROS2 Simulation

基于 **Isaac Sim 5.1 (Python 3.11)** + **Isaac Lab 2.1.0** 的 Unitree Go2 四足机器人仿真平台，支持多机器人控制、多种仿真环境切换，并通过文件桥接实现 **ROS2 话题可视化**（Windows 仿真 ↔ WSL2 ROS2 + RViz2）。

---

## 目录

- [系统概述](#系统概述)
- [版本迁移说明 (4.5 → 5.1)](#版本迁移说明-45--51)
- [环境配置](#环境配置)
  - [1. 基础环境](#1-基础环境)
  - [2. Isaac Lab 源码配置](#2-isaac-lab-源码配置)
  - [3. ROS2 Humble（WSL2）](#3-ros2-humblewsl2)
- [运行仿真](#运行仿真)
- [键盘控制](#键盘控制)
- [仿真环境](#仿真环境)
- [ROS2 话题与可视化](#ros2-话题与可视化)
- [所有话题列表](#所有话题列表)
- [速度指令控制](#速度指令控制)
- [项目结构](#项目结构)
- [技术架构](#技术架构)
- [常见问题](#常见问题)

---

## 系统概述

| 组件 | 说明 |
|------|------|
| **仿真引擎** | NVIDIA Isaac Sim **5.1** (`D:\isaac-sim`) |
| **Python** | **3.11.13**（Isaac Sim 5.1 内置） |
| **机器人框架** | Isaac Lab 2.1.0（源码安装，`D:\isaacsim\IsaacLab`） |
| **机器人模型** | Unitree Go2（四足机器人） |
| **RL 策略** | PPO 策略，粗糙地形 / 平坦地形 |
| **控制方式** | 键盘操控 + ROS2 cmd_vel |
| **ROS2 集成** | 文件桥接 → WSL2 ROS2 Humble → RViz2 可视化 |
| **GPU 渲染** | NVIDIA RTX 5080（Vulkan） |
| **物理模拟** | CPU（Isaac Sim 5.1 PyTorch 为 CPU 版） |

---

## 版本迁移说明 (4.5 → 5.1)

本项目从 Isaac Sim 4.5 (Python 3.10) 迁移至 **Isaac Sim 5.1 (Python 3.11)**。

### 主要变更

| 变更项 | Isaac Sim 4.5 | Isaac Sim 5.1 |
|--------|---------------|---------------|
| **Python 版本** | 3.10 | 3.11 |
| **安装路径** | `D:\isaacsim` | `D:\isaac-sim` |
| **启动方式** | conda 环境 + python.exe | `python.bat`（Kit 内置） |
| **PyTorch** | 2.12.1+cu130（CUDA） | 2.5.1+cpu（CPU 版） |
| **omni.isaac → isaacsim** | 旧命名空间 | 新命名空间（向下兼容） |
| **ROS2 桥接扩展** | `omni.isaac.ros2_bridge` | `isaacsim.ros2.bridge` |
| **LiDAR 配置** | Hesai_XT32_SD10 | Example_Rotary |
| **LiDAR 注释器** | RtxSensorCpuIsaacCreateRTXLidarScanBuffer | IsaacCreateRTXLidarScanBuffer |
| **GUI 体验文件** | isaaclab.python.kit | **isaaclab.python.sim51.kit**（自定义） |
| **数据目录** | `D:\isaacsim\data\go2_ros2` | `D:\isaac-sim\data\go2_ros2` |

### 迁移详述

#### API 命名空间重构

Isaac Sim 5.1 将 `omni.isaac.*` 迁移到 `isaacsim.*`：

| 旧 (4.5) | 新 (5.1) |
|----------|----------|
| `from omni.isaac.kit import SimulationApp` | `from isaacsim import SimulationApp` |
| `from omni.isaac.core.prims import ...` | `from isaacsim.core.prims import ...` |
| `omni.isaac.ros2_bridge` 扩展 | `isaacsim.ros2.bridge` 扩展 |

#### Kit 体验文件

GUI 模式原使用 `isaaclab.python.kit`，依赖 `omni.physx.stageupdate`（无 cp311 版本）。
创建了 **`isaaclab.python.sim51.kit`**，基于 `isaacsim.exp.base`（Isaac Sim 5.1 原生 Python 体验文件）。

#### PyTorch CUDA 兼容性

Isaac Sim 5.1 内置 PyTorch 2.5.1+cpu。安装 cu118/cu128 版本会导致 Kit 的 CUDA DLL 与 PyTorch 的 CUDA DLL 冲突，进程崩溃。故物理模拟使用 `--device cpu`，渲染使用 GPU (Vulkan)。

#### LiDAR 传感器

原 `Hesai_XT32_SD10` 配置需从 Omniverse 云下载 USD 资源。改用本地可用的 `Example_Rotary` 配置。注释器名从 `RtxSensorCpuIsaacCreateRTXLidarScanBuffer` 改为 `IsaacCreateRTXLidarScanBuffer`，数据格式为极坐标 (distance, azimuth, elevation)，桥接代码自动转换为 XYZ 笛卡尔坐标。

---

## 环境配置

### 1. 基础环境

Isaac Sim 5.1 已安装于 `D:\isaac-sim`，使用其内置 Python 3.11。

```bash
# 验证 Python 版本
D:\isaac-sim\python.bat --version
# 输出: Python 3.11.13

# 验证 Isaac Sim
D:\isaac-sim\python.bat -c "import isaacsim; print('OK')"
```

### 2. Isaac Lab 源码配置

Isaac Lab 2.1.0 位于 `D:\isaacsim\IsaacLab`，通过 `sys.path` 导入（非 pip install）：

```python
# isaac_go2_ros2.py 顶部自动添加
sys.path.insert(0, "D:/isaacsim/IsaacLab/source")
sys.path.insert(0, "D:/isaacsim/IsaacLab/source/isaaclab")
sys.path.insert(0, "D:/isaacsim/IsaacLab/source/isaaclab_rl")
sys.path.insert(0, "D:/isaacsim/IsaacLab/source/isaaclab_assets")
sys.path.insert(0, "D:/isaacsim/IsaacLab/source/isaaclab_tasks")
```

安装 Python 依赖：
```bash
D:\isaac-sim\python.bat -m pip install gymnasium hydra-core
D:\isaac-sim\python.bat -m pip install torch==2.5.1 --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. ROS2 Humble（WSL2）

在 **WSL2 Ubuntu 22.04** 中安装：

```bash
# 安装 ROS2 Humble
sudo apt install -y ros-humble-desktop
sudo apt install -y ros-humble-nav-msgs ros-humble-sensor-msgs
sudo apt install -y ros-humble-tf2-ros ros-humble-cv-bridge
sudo apt install -y ros-humble-sensor-msgs-py ros-humble-point-cloud-msg

# 设置环境变量
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "export ROS_DOMAIN_ID=42" >> ~/.bashrc
source ~/.bashrc
```

#### WSL2 镜像网络配置

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

---

## 运行仿真

### 一键启动（推荐）

双击 `run_go2.bat` 即可启动 GUI 模式。

### 手动启动

```bash
cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
D:\isaac-sim\python.bat isaac_go2_ros2.py --device cpu
```

### 启动参数

| 参数 | 说明 |
|------|------|
| `--device cpu` | 使用 CPU 物理模拟（默认，Isaac Sim 5.1 PyTorch 为 CPU 版） |
| `--headless` | 无头模式（不显示 3D 窗口，用于远程/训练） |

**提示**：LiDAR 和相机传感器仅 GUI 模式可用（需 GPU 渲染管线）。

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

| 按键 | 控制 |
|------|------|
| **1 ~ 9** | 选择机器人 0 ~ 8 |
| **F1 ~ F9** | 选择机器人 0 ~ 8（备用） |
| **W/A/S/D/Z/C** | 控制当前选中的机器人 |

---

## 仿真环境

编辑 `cfg/sim.yaml`：

```yaml
env_name: full-warehouse
num_envs: 1
camera_follow: False    # False = 自由控制视角
sensor:
  enable_lidar: True
  enable_camera: True
```

### 可用环境

| 环境名 | 说明 |
|--------|------|
| `obstacle-sparse` | 稀疏障碍物（100 个） |
| `obstacle-medium` | 中等障碍物（200 个） |
| `obstacle-dense` | 密集障碍物（400 个） |
| `warehouse` | 简单仓库 |
| `warehouse-forklifts` | 仓库 + 叉车 |
| `warehouse-shelves` | 仓库 + 货架 |
| `full-warehouse` | 完整仓库（需下载资产） |

---

## ROS2 话题与可视化

### 文件桥接原理

```
Windows (Isaac Sim 5.1)                 WSL2 (ROS2 Humble)
       │                                      │
       │  写入数据到共享文件                     │  读取数据发布为话题
       │                                      │
       └── D:\isaac-sim\data\go2_ros2/ ──────┘
                │
           +----+----+-----+------+------+
           │    │    │     │      │      │
        data.json  │    .npy  .png  .png
           │   cmd_vel.json
           │
       ┌──┴──┐
       帧号检测增量更新
```

**数据流向：**

1. **go2_ros2_bridge.py**（Windows，仿真内）：每 3 步采集一次机器人状态、传感器数据 → 写入共享目录
2. **go2_file_bridge_wsl2.py**（WSL2）：轮询读取共享文件 → 发布为标准 ROS2 话题
3. **cmd_vel 控制**（双向）：WSL2 订阅 `/unitree_go2/cmd_vel` → 写入 `cmd_vel.json` → Windows 读取并应用

### 启动可视化

**终端 1（Windows）— 启动仿真：**

```bash
cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
.\run_go2.bat
```

**终端 2（WSL2）— 启动桥接（前台运行）：**

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
/usr/bin/python3 /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/ros2/go2_file_bridge_wsl2.py
```

**终端 3（WSL2）— 启动 RViz2：**

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42
rviz2 -d /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/rviz/go2.rviz
```

**一键脚本（WSL2）：**

```bash
cd /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/ros2
chmod +x start_wsl2_bridge.sh
./start_wsl2_bridge.sh --rviz
```

---

## 所有话题列表

| 分类 | 话题 | 类型 | 频率 | 说明 |
|------|------|------|:----:|------|
| **控制** | `/unitree_go2/cmd_vel` | `geometry_msgs/Twist` | 订阅 | 速度指令 (双向) |
| **相机** | `/unitree_go2/front_cam/color_image` | `sensor_msgs/Image` | ~13Hz | RGB 彩色图像 (640×480) |
| | `/unitree_go2/front_cam/depth_image` | `sensor_msgs/Image` | ~13Hz | 深度图像 (灰度模糊) |
| | `/unitree_go2/front_cam/semantic_segmentation_image` | `sensor_msgs/Image` | ~13Hz | 语义分割 (边缘检测) |
| | `/unitree_go2/front_cam/info` | `sensor_msgs/CameraInfo` | ~13Hz | 相机内参 |
| **LiDAR** | `/unitree_go2/lidar/point_cloud` | `sensor_msgs/PointCloud2` | ~13Hz | 激光雷达点云 |
| **里程计** | `/unitree_go2/odom` | `nav_msgs/Odometry` | ~13Hz | 位置/方向/速度 |
| | `/unitree_go2/pose` | `geometry_msgs/PoseStamped` | ~13Hz | 机器人位姿 |
| **TF** | `/tf` | `tf2_msgs/TFMessage` | ~13Hz | odom → base_link |

### RViz2 操作指南

1. **设置 Fixed Frame**：左侧 Displays → Global Options → Fixed Frame 输入 `odom`
2. **恢复图像显示**（如果丢失）：左下角 **Add** → **By topic** → 双击需要的 Image 话题
3. **点云显示设置**：找到 **lidar_point_cloud** → Style 改为 `Points` → Size 改为 2
4. **调整视角**：按住 `Alt` + 鼠标左键拖拽旋转，滚轮缩放

---

## 速度指令控制

```bash
# 单次发送（前进 0.5 m/s）
ros2 topic pub /unitree_go2/cmd_vel geometry_msgs/Twist \
  '{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {z: 0.0}}' --once

# 连续发送（保持速度）
ros2 topic pub -r 10 /unitree_go2/cmd_vel geometry_msgs/Twist \
  '{linear: {x: 0.5}, angular: {z: 0.3}}'

# 停止
ros2 topic pub /unitree_go2/cmd_vel geometry_msgs/Twist \
  '{linear: {x: 0.0}}' --once
```

---

## 项目结构

```
isaac-go2-ros2/
├── cfg/
│   └── sim.yaml                       # 仿真配置（环境/机器人/传感器）
├── env/
│   ├── sim_env.py                     # 仿真环境加载（仓库/障碍物/语义）
│   ├── terrain.py                     # 程序化地形生成
│   └── terrain_cfg.py                 # 地形配置类
├── go2/
│   ├── go2_ctrl.py                    # 键盘控制 + RL 策略加载
│   ├── go2_ctrl_cfg.py               # PPO 策略超参数配置
│   ├── go2_env.py                     # Go2 仿真环境定义（场景/动作/观测）
│   └── go2_sensors.py                 # LiDAR + 相机传感器创建
├── ros2/
│   ├── go2_ros2_bridge.py             # Windows 端桥接（写数据文件）
│   ├── go2_file_bridge_wsl2.py        # WSL2 端桥接（发布 ROS2 话题）
│   └── start_wsl2_bridge.sh           # WSL2 一键启动脚本
├── rviz/
│   └── go2.rviz                       # RViz2 可视化配置文件
├── ckpts/
│   └── unitree_go2/                   # RL 策略模型 checkpoint
├── outputs/                           # Hydra 运行输出
├── isaac_go2_ros2.py                  # 主程序入口
├── run_go2.bat                        # Windows 启动脚本
└── README.md                          # 本文件
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Windows 主机                                 │
│                                                                     │
│  ┌─────────────────┐   ┌──────────────────────────────────────┐    │
│  │ Isaac Sim 5.1   │   │ Python 桥接 (go2_ros2_bridge.py)     │    │
│  │ (Kit + Vulkan)  │   │                                      │    │
│  │                 │   │  - 每 3 帧采集 (robot_state)         │    │
│  │  - 物理仿真 CPU │   │  - Camera RGB → PNG                  │    │
│  │  - RL 策略推理  │──▶│  - Depth → 灰度模糊 PNG              │    │
│  │  - RTX 渲染 GPU │   │  - LiDAR → Polar→XYZ → .npy         │    │
│  │  - LiDAR/相机   │   │  - Odom → JSON                       │    │
│  │  - cmd_vel 控制 │   │  - cmd_vel.json 读取 → 控制机器人    │    │
│  └─────────────────┘   └──────────────┬───────────────────────┘    │
│                                       │ 共享文件                    │
│  ┌────────────────────────────────────┴───────────────────────┐    │
│  │              D:\isaac-sim\data\go2_ros2\                  │    │
│  │  ┌───────────┬──────────┬─────────┬─────────┬──────────┐ │    │
│  │  │data.json  │color_*.png│depth_*.png│semantic*.png│     │ │    │
│  │  │(元数据)   │ (RGB)     │ (深度)   │ (语义)    │.npy  │ │    │
│  │  │           │          │         │         │(点云)  │ │    │
│  │  └───────────┴──────────┴─────────┴─────────┴──────────┘ │    │
│  │  + cmd_vel.json (速度指令, 双向)                          │    │
│  └───────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ WSL2 挂载 /mnt/d/
┌───────────────────────────────v─────────────────────────────────────┐
│                      WSL2 Ubuntu 22.04                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ ROS2 桥接 (go2_file_bridge_wsl2.py)                      │      │
│  │                                                          │      │
│  │  - 读取共享文件 → 发布 Odometry / Image / PointCloud2    │      │
│  │  - 订阅 /unitree_go2/cmd_vel → 写入 cmd_vel.json         │      │
│  │  - 帧号检测确保每次更新发布一次                           │      │
│  └─────────────────────┬────────────────────────────────────┘      │
│                        │                                            │
│               ┌────────v────────┐    ┌────────v────────┐           │
│               │     RViz2       │    │   ros2 CLI      │           │
│               │   可视化调试    │    │  话题列表/回放  │           │
│               └─────────────────┘    └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### 关键实现细节

#### RL 策略加载

使用 rsl_rl 的 `OnPolicyRunner`，支持 CPU 模式加载 CUDA checkpoint（自动 `map_location`）：

```python
def _load_on_policy_runner(ppo_runner, ckpt_path):
    if not torch.cuda.is_available():
        # 自动 map_location="cpu" 加载 CUDA checkpoint
```

#### LiDAR 极坐标 → 笛卡尔坐标转换

`IsaacCreateRTXLidarScanBuffer` 返回 distance/azimuth/elevation 极坐标数据，桥接代码转换为 XYZ：

```python
x = r * cos(elevation) * sin(azimuth)
y = r * cos(elevation) * cos(azimuth)
z = r * sin(elevation)
```

#### cmd_vel 双向通信

WSL2 订阅 ROS2 Twist → 写入 `cmd_vel.json` → Windows 每步读取 → 设置 `base_vel_cmd_input`：

```python
# Windows 侧（go2_ros2_bridge.py）
go2_ctrl.base_vel_cmd_input[selected] = torch.tensor(
    [linear_x, linear_y, angular_z], dtype=torch.float32)
```

### 依赖清单

| 包 | 版本 | 来源 | 用途 |
|----|:----:|------|------|
| torch | 2.5.1+cpu | 清华镜像 | 物理模拟/RL 推理（CPU 版） |
| gymnasium | 1.3.0 | pip | RL 环境接口 |
| hydra-core | 1.3.3 | pip | 配置文件加载 |
| numpy | 2.4.6 | pip | 数据处理 |
| opencv-python-headless | 4.11.0 | pip | 图像处理 |
| pillow | 11.0.0 | pip | 图像编码 |
| scipy | 1.15.3 | pip | 旋转变换 |
| rsl-rl-lib | 2.3.1 | pip | PPO 策略 |

### 已知限制

1. **PyTorch CUDA 不可用** — Isaac Sim 5.1 Kit 的 CUDA DLL 与 PyTorch 冲突，物理模拟使用 CPU
2. **LiDAR 仅 GUI 模式** — RTX LiDAR 需要 GPU 渲染管线，headless 模式不工作
3. **深度/语义为模拟数据** — 深度图由 RGB 灰度模糊生成，语义分割由 Canny 边缘检测模拟
4. **文件桥接延迟** — 约 75-100ms（3 帧采集间隔 + 文件读写）
5. **仓库资产** — 部分 USD 资源需从 Omniverse Nucleus 云下载

---

## 常见问题

### 仿真启动失败（扩展依赖错误）

```
Error: dependency 'omni.physx.stageupdate' can't be satisfied
```

**原因**：`omni.physx.stageupdate` 只有 cp310 版本，Isaac Sim 5.1 为 cp311。
**解决**：使用自定义体验文件 `isaaclab.python.sim51.kit`（已配置，依赖 `isaacsim.exp.base`）。

### RViz2 显示 "Frame [odom] does not exist"

**原因**：桥接进程未运行或数据目录错误。
**检查**：
```bash
# 确认桥接运行
ps aux | grep go2_file_bridge

# 确认数据文件存在
ls -la /mnt/d/isaac-sim/data/go2_ros2/data.json

# 确认话题
ros2 topic list | grep unitree
```

### ROS2 看不到任何话题

```bash
# 重启 daemon
ros2 daemon stop
ros2 topic list

# 确认环境变量
echo $ROS_DOMAIN_ID    # 应为 42

# 运行桥接（保持前台）
/usr/bin/python3 /mnt/d/isaacsim/IsaacLab/_isaac_sim/isaac-go2-ros2/ros2/go2_file_bridge_wsl2.py
```

### 3D 窗口无响应

- 点击 Isaac Sim 窗口使其获得焦点
- 确保 `camera_follow: False`（`cfg/sim.yaml` 中设置）

### 双GPU 警告（Intel Graphics）

```
Skipping unsupported non-NVIDIA GPU: Intel(R) Graphics
```

正常现象。Isaac Sim 自动跳过 Intel 核显，使用 RTX 5080。

### Windows Defender 误报

`python.bat` 或 `kit.exe` 可能被杀毒软件拦截。添加排除项：
```
D:\isaac-sim\
D:\isaacsim\IsaacLab\
```

---

## 文件清单（截至 2026-07-01）

| 文件 | 大小 | 说明 |
|------|:----:|------|
| `run_go2.bat` | 1.4 KB | Windows 启动脚本 |
| `isaac_go2_ros2.py` | 12.7 KB | 主程序 |
| `cfg/sim.yaml` | — | 仿真配置 |
| `go2/go2_env.py` | 7.5 KB | 环境定义 |
| `go2/go2_ctrl.py` | 4.5 KB | 控制逻辑 |
| `go2/go2_ctrl_cfg.py` | 2.4 KB | PPO 配置 |
| `go2/go2_sensors.py` | 2.4 KB | 传感器创建 |
| `env/sim_env.py` | 3.5 KB | 环境加载 |
| `ros2/go2_ros2_bridge.py` | 7.4 KB | Windows 桥接 |
| `ros2/go2_file_bridge_wsl2.py` | 8.5 KB | WSL2 桥接 |
| `ros2/start_wsl2_bridge.sh` | 1.7 KB | WSL2 启动脚本 |
| `rviz/go2.rviz` | — | RViz2 配置 |
