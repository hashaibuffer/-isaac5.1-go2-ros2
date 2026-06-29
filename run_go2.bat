@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo  Isaac Sim - Unitree Go2 Simulation
echo ========================================

:: Set Isaac Sim environment variables
set CARB_APP_PATH=D:\isaacsim\kit
set ISAAC_PATH=D:\isaacsim
set EXP_PATH=D:\isaacsim\apps
set PYTHONPATH=D:\isaacsim\site

:: Use conda environment
set CONDA_ENV=isaaclab_env_2
set PYTHON_EXE=D:\ProgramData\anaconda3\envs\%CONDA_ENV%\python.exe

:: Check python exists
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python not found at: %PYTHON_EXE%
    pause
    exit /b 1
)

cd /d D:\isaacsim\IsaacLab\_isaac_sim\isaac-go2-ros2

echo [INFO] Starting Go2 simulation...
echo [INFO] Controls: 1-9 select robot, WASDZC to control
echo.

"%PYTHON_EXE%" isaac_go2_ros2.py

echo.
echo [INFO] Simulation ended.
pause
