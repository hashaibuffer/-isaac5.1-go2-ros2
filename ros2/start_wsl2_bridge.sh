#!/bin/bash
# Start the WSL2-side ROS2 bridge
# Run this AFTER starting isaac_go2_ros2 on Windows
#
# Usage:
#   ./start_wsl2_bridge.sh              # Start bridge only
#   ./start_wsl2_bridge.sh --rviz       # Start bridge + rviz2
#   ./start_wsl2_bridge.sh --rviz-only  # Start rviz2 only (bridge already running)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RVIZ_CONFIG="$PROJECT_DIR/rviz/go2.rviz"

# ROS2 environment
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=42

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Go2 ROS2 Bridge - WSL2 Side${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

case "${1:-}" in
    --rviz)
        echo -e "${YELLOW}Starting bridge in background...${NC}"
        /usr/bin/python3 "$SCRIPT_DIR/go2_file_bridge_wsl2.py" &
        BRIDGE_PID=$!
        sleep 2
        echo -e "${YELLOW}Starting rviz2...${NC}"
        rviz2 -d "$RVIZ_CONFIG"
        echo -e "${YELLOW}Stopping bridge (PID=$BRIDGE_PID)...${NC}"
        kill $BRIDGE_PID 2>/dev/null
        ;;
    --rviz-only)
        echo -e "${YELLOW}Starting rviz2 only (bridge should already be running)...${NC}"
        rviz2 -d "$RVIZ_CONFIG"
        ;;
    *)
        echo -e "${YELLOW}Starting bridge (foreground)...${NC}"
        echo -e "${YELLOW}Open a second terminal and run:${NC}"
        echo "  cd ${PROJECT_DIR}/ros2"
        echo "  source /opt/ros/humble/setup.bash"
        echo "  export ROS_DOMAIN_ID=42"
        echo "  rviz2 -d ${RVIZ_CONFIG}"
        echo ""
        /usr/bin/python3 "$SCRIPT_DIR/go2_file_bridge_wsl2.py"
        ;;
esac
