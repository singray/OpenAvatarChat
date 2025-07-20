#!/bin/bash
PIDS=$(ps -ef | grep -i '[O]penAvatarChat' | awk '{print $2}')

# 检查是否找到进程

if [ -z "$PIDS" ]; then
    echo "No penAvatarChat processes found."
else
    echo "Found penAvatarChat processes with PIDs: $PIDS"
    echo "Killing these processes..."
    
    # 终止进程
    kill -9 $PIDS 2>/dev/null || true
    sleep 2
    echo "All penAvatarChat processes have been terminated."
fi
