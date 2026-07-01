@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo  Isaac Sim 5.1 - Unitree Go2 Simulation
echo ========================================
echo.

:: Set Isaac Sim 5.1 environment variables
set CARB_APP_PATH=D:\isaac-sim\kit
set ISAAC_PATH=D:\isaac-sim
set EXP_PATH=D:\isaac-sim\apps
set PYTHONPATH=D:\isaac-sim\site

:: Use Isaac Sim 5.1's built-in Python (Python 3.11)
set PYTHON_EXE=D:\isaac-sim\python.bat

:: Check python exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at: %PYTHON_EXE%
    pause
    exit /b 1
)

cd /d D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2

echo [INFO] Starting Go2 simulation with Isaac Sim 5.1...
echo [INFO] Controls: 1-9 select robot, WASDZC to control
echo [INFO] Robot 0 selected by default
echo.
echo [INFO] GPU mode (RTX 5080) - 3D rendering ^& LiDAR/camera sensors
echo [INFO] Physics on CPU (Isaac Sim 5.1 torch is CPU-only)
echo.
echo [INFO] Tips:
echo   run_go2.bat              - GUI mode (recommended, full sensors)
echo   run_go2.bat --headless   - Headless mode (no window, no sensors)

:: --device cpu: Isaac Sim 5.1's bundled PyTorch (2.5.1+cpu) has no CUDA support
:: 3D rendering still uses RTX 5080 GPU via Vulkan
call "%PYTHON_EXE%" isaac_go2_ros2.py --device cpu %*

echo.
if errorlevel 1 (
    echo [ERROR] Simulation exited with code %errorlevel%
) else (
    echo [INFO] Simulation completed successfully.
)
echo.
pause
