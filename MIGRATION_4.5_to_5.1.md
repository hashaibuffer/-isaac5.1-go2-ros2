# Isaac Sim 4.5 → 5.1 迁移指南

## 项目信息

- **项目路径**: `D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2`
- **Isaac Sim 4.5 路径**: `D:\isaacsim`
- **Isaac Sim 5.1 路径**: `D:\isaac-sim`
- **目标**: 将项目从 Isaac Sim 4.5 完全迁移到 5.1 版本

---

## 第一阶段：环境准备

### 1.1 确认 Python 版本

Isaac Sim 5.1 要求 **Python 3.11**。执行以下命令验证：

```bash
D:\isaac-sim\python.bat --version
```

如果输出不是 `Python 3.11.x`，需要创建新的 conda 环境：

```bash
conda create -n isaaclab_51 python=3.11
conda activate isaaclab_51
```

### 1.2 安装 Isaac Lab (5.1 兼容版本)

```bash
# 进入 Isaac Lab 源码目录
cd D:\isaac-sim\IsaacLab\source\isaaclab

# 安装基础依赖
pip install setuptools wheel

# 安装 PyTorch（需确认支持当前 GPU）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

# 安装 Isaac Lab
pip install -e .
```

### 1.3 修改启动脚本

编辑 `run_go2.bat`，将 Isaac Sim 路径指向 5.1 版本：

```batch
@echo off
set CARB_APP_PATH=D:\isaac-sim\kit
set ISAAC_PATH=D:\isaac-sim
set EXP_PATH=D:\isaac-sim\apps
set PYTHONPATH=D:\isaac-sim\site

set CONDA_ENV=isaaclab_51
set PYTHON_EXE=D:\ProgramData\anaconda3\envs\%CONDA_ENV%\python.exe

cd /d D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
"%PYTHON_EXE%" isaac_go2_ros2.py
pause
```

### 1.4 备份项目

```bash
cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
git checkout -b backup/before-51-migration
git add .
git commit -m "备份：适配 Isaac Sim 5.1 前的代码状态"
git checkout main
git checkout -b feature/adapt-to-5.1
```

---

## 第二阶段：代码迁移（核心）

### 2.1 API 命名空间重构: omni.isaac. → isaacsim.

这是 Isaac Sim 4.5 → 5.1 最根本的变更。需要在所有 `.py` 文件中进行全局替换。

**替换规则：**

| 旧导入方式 (Isaac Sim 4.5) | 新导入方式 (Isaac Sim 5.1) |
|----------------------------|---------------------------|
| `from omni.isaac.core.prims import X` | `from isaacsim.core.prims import X` |
| `from omni.isaac.core.utils import Y` | `from isaacsim.core.utils import Y` |
| `from omni.isaac.kit import SimulationApp` | `from isaacsim import SimulationApp` |
| `import omni.isaac.core` | `import isaacsim.core` |
| `omni.isaac.ros2_bridge` | `isaacsim.ros2.bridge` |

**操作步骤：**

在项目根目录执行全局搜索，查找所有 `omni.isaac` 出现的位置，逐一替换为 `isaacsim`：

```bash
# 查看所有需要替换的文件
grep -r "omni\.isaac" --include="*.py" .

# 批量替换
find . -name "*.py" -exec sed -i 's/omni\.isaac/isaacsim/g' {} \;
```

> **注意**：`omni.isaac.ros2_bridge` 在旧版中使用短横线命名，新版统一为 `isaacsim.ros2.bridge`。

### 2.2 核心类重命名

类命名体系进行了重构：

| 旧类名 (Isaac Sim 4.5) | 新类名 (Isaac Sim 5.1) |
|------------------------|-----------------------|
| `Articulation` | `SingleArticulation` |
| `ArticulationView` | `Articulation` |
| `RigidPrim` | `SingleRigidPrim` |
| `RigidPrimView` | `RigidPrim` |

**操作步骤：**

```bash
# 检查项目中使用的旧类名
grep -rn "ArticulationView\|RigidPrimView\|Articulation[^V]\|RigidPrim[^V]" --include="*.py" .
# 逐一根据上下文替换
```

### 2.3 修改主入口文件 isaac_go2_ros2.py

在文件最顶部（所有 import 之前）添加 Isaac Sim 5.1 路径：

```python
import sys
import os
# 将 Isaac Sim 5.1 的路径加入系统路径
sys.path.append(r"D:\isaac-sim")
sys.path.append(r"D:\isaac-sim\python")
sys.path.append(r"D:\isaac-sim\kit\python\Lib\site-packages")
```

更新所有 import 语句：

```python
# 旧版本
# from omni.isaac.kit import SimulationApp
# from isaaclab.app import AppLauncher  # 也可能需要更新

# 新版本
from isaacsim import SimulationApp
```

### 2.4 更新各模块文件

按以下顺序检查和更新文件：

| 文件 | 需要检查的内容 |
|------|--------------|
| `env/sim_env.py` | 所有 `omni.isaac` / `isaacsim` 导入 |
| `go2/go2_env.py` | 核心类和 API 调用（InteractiveSceneCfg 等） |
| `go2/go2_ctrl.py` | 控制相关的 API（RslRlVecEnvWrapper 等） |
| `go2/go2_sensors.py` | 传感器 API（Camera, replicator 等） |
| `ros2/go2_ros2_bridge.py` | ROS2 桥接 API |
| `ros2/go2_file_bridge_wsl2.py` | 文件桥接（无 Isaac Sim 依赖，通常无需修改） |

---

## 第三阶段：ROS2 桥接与 OmniGraph 迁移

### 3.1 ROS2 OmniGraph 节点变化

在 Isaac Sim 5.1 中，关键 ROS2 发布节点要求从**专用的源节点**接收预处理数据：

- **ROS2 Publish Transform Tree** — 需要 `Isaac Compute Transform Tree` 源节点
- **ROS2 Publish Joint State** — 需要 `Isaac Read Joint State` 源节点
- **ROS2 Publish Clock** — 节点类型名可能从 `isaacsim.ros2.bridge.ROS2PublishClock` 变更

### 3.2 ROS2 Bridge 扩展名确认

```python
# Isaac Sim 4.5
ext_manager.set_extension_enabled_immediate("omni.isaac.ros2_bridge", True)

# Isaac Sim 5.1 — 确认扩展名是否已变更为 isaacsim.ros2.bridge
ext_manager.set_extension_enabled_immediate("isaacsim.ros2.bridge", True)
```

### 3.3 文件桥接方案（推荐保留）

由于项目当前使用文件桥接而非 DDS 直连进行 ROS2 通信，OmniGraph 节点的变化**对文件桥接方案影响较小**。文件桥接的核心逻辑不变：

```
Windows (Isaac Sim) → 共享文件 → WSL2 (ROS2) → 发布话题
```

只需确认以下内容：
1. `go2_ros2_bridge.py` 中 `ext_manager.set_extension_enabled_immediate()` 的扩展名
2. `omni.kit.app.get_app().get_extension_manager()` 的调用方式

---

## 第四阶段：依赖与配置更新

### 4.1 更新 Conda 环境

```bash
conda create -n isaaclab_51 python=3.11
conda activate isaaclab_51
```

### 4.2 pip 依赖

```bash
# 重新安装所有依赖
pip install setuptools wheel

# PyTorch（根据 GPU 选择版本）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

# Isaac Lab 依赖
pip install numpy<2.0 "pillow==11.0.0"
pip install flatdict==4.0.1 --no-build-isolation
pip install hydra-core matplotlib opencv-python<=4.10 scipy

# RL 策略
pip install rsl-rl-lib==2.3.1
```

### 4.3 检查 cfg/sim.yaml

检查配置文件中是否有硬编码的路径或版本号：

```yaml
# 检查 Isaac Sim 相关路径配置
# 确保 asset_root 路径指向正确的 S3 或本地路径
```

### 4.4 PhysX 引擎变更

Isaac Sim 5.1 使用 PhysX 5.6.1（4.5 版本为 PhysX 5.3）。如果代码中有直接调用 PhysX API 或设置 PhysX 参数的部分，需检查 API 兼容性。

---

## 第五阶段：测试与调试

### 5.1 基础启动测试

```bash
cd D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2
.\run_go2.bat
```

预期可能遇到 ModuleNotFoundError 或 API 不兼容报错，根据报错信息逐项修复。

### 5.2 常见错误及解决方案

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `ModuleNotFoundError: No module named 'omni'` | 未使用 Isaac Sim 的 Python | 检查 `run_go2.bat` 是否正确设置 `CARB_APP_PATH` |
| `ModuleNotFoundError: No module named 'isaacsim'` | 路径未正确添加 | 在 `isaac_go2_ros2.py` 顶部添加 `sys.path.append(r"D:\isaac-sim")` |
| `AttributeError: module 'isaacsim' has no attribute 'xxx'` | API 名称变更 | 检查是否所有 `omni.isaac` 都已替换为 `isaacsim` |
| `ImportError: cannot import name 'ArticulationView'` | 类名已变更 | 将 `ArticulationView` 改为 `Articulation` |
| `OmniGraphError: Could not create node...` | ROS2 节点需要源节点 | 按 3.1 节添加 `Isaac Compute Transform Tree` 或 `Isaac Read Joint State` |
| `DLL load failed while importing _rclpy_pybind11` | ROS2 DLL 路径 | 添加 `D:\isaac-sim\exts\isaacsim.ros2.bridge\humble\lib` 到 PATH |
| `CUDA error: no kernel image` | PyTorch 版本不支持当前 GPU | 安装支持当前 CUDA 架构的 PyTorch 版本 |

### 5.3 功能验证清单

基础启动成功后，逐项验证：

- [ ] 仿真环境能否正常加载（obstacle-dense / warehouse）
- [ ] Go2 机器狗模型是否正确显示
- [ ] 键盘控制（WASDZC）正常响应
- [ ] 多机器人切换（1-9 / F1-F9）正常
- [ ] 文件桥接正常写入共享目录
- [ ] WSL2 端 ROS2 话题正常发布
- [ ] RViz2 可视化数据正确
- [ ] `cmd_vel` 速度指令正常接收

### 5.4 回滚方案

如果迁移后出现不可修复的问题，切换回 4.5 版本：

```bash
git checkout feature/adapt-to-5.1
# 或直接恢复 run_go2.bat 中的路径为 4.5
set ISAAC_PATH=D:\isaacsim
```

---

## 附录：文件变更清单

| 文件 | 预期变更 |
|------|---------|
| `run_go2.bat` | 替换 Isaac Sim 路径为 5.1 |
| `isaac_go2_ros2.py` | 添加 sys.path，更新 import |
| `env/sim_env.py` | `omni.isaac` → `isaacsim` 替换 |
| `go2/go2_env.py` | 类名更新 + 命名空间替换 |
| `go2/go2_ctrl.py` | 命名空间替换 |
| `go2/go2_sensors.py` | 命名空间替换 + API 更新 |
| `ros2/go2_ros2_bridge.py` | 扩展名确认 + API 更新 |
| `cfg/sim.yaml` | 路径/版本号检查 |

## 附录：Isaac Sim 4.5 vs 5.1 关键差异

| 项目 | Isaac Sim 4.5 | Isaac Sim 5.1 |
|------|--------------|--------------|
| Python 版本 | 3.10 | 3.11 |
| 命名空间 | `omni.isaac.*` | `isaacsim.*` |
| PhysX 版本 | 5.3 | 5.6.1 |
| ROS2 Bridge | `omni.isaac.ros2_bridge` | `isaacsim.ros2.bridge` |
| Articulation | `Articulation` + `ArticulationView` | `SingleArticulation` + `Articulation` |
| RigidPrim | `RigidPrim` + `RigidPrimView` | `SingleRigidPrim` + `RigidPrim` |
