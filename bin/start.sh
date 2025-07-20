#!/bin/bash

# 设置日志目录
LOG_DIR="/mnt/data/OpenAvatarChat/logs"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/avatarchat.log"

# 查找并停止占用8282端口的进程
echo "检查8282端口占用情况..."
PID=$(lsof -t -i:8282)

if [ ! -z "$PID" ]; then
	    echo "发现进程 $PID 占用8282端口，正在停止..."
	        kill -9 $PID
		    echo "进程已停止"
	    else
		        echo "8282端口未被占用"
fi
sh /mnt/data/OpenAvatarChat/bin/kill_avatar.sh

# 启动服务并将日志输出到指定文件
echo "启动服务...大约需要20s"
nohup uv run /mnt/data/OpenAvatarChat/src/demo.py --config /mnt/data/OpenAvatarChat/config/glut.yaml > $LOG_FILE 2>&1 &

# 验证服务是否启动成功
sleep 20
NEW_PID=$(lsof -t -i:8282)

if [ ! -z "$NEW_PID" ]; then
	    echo "服务已成功启动，PID: $NEW_PID"
	        echo "日志输出到: $LOG_FILE"
	else
		    echo "服务启动失败，请检查日志"
		        tail -n 20 $LOG_FILE
fi
