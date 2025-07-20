#!/bin/bash

# 设置日志目录
BASE_DIR="/mnt/data/open-avatar-chat/opt/OpenAvatarChat"
LOG_DIR="$BASE_DIR/logs"

mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/avatarchat.log"

# 查找并停止占用8283端口的进程
echo "检查8283端口占用情况..."
PID=$(lsof -t -i:8283)

if [ ! -z "$PID" ]; then
	    echo "发现进程 $PID 占用8282端口，正在停止..."
	        kill -9 $PID
		    echo "进程已停止 "
	    else
		        echo "8283端口未被占用"
fi

#sh /mnt/data/open-avatar-chat/opt/OpenAvatarChat/bin/kill_avatar.sh
sleep 2
# 启动服务并将日志输出到指定文件
echo "启动服务...大约需要20s"
echo "启动命令 uv run $BASE_DIR/src/demo.py --config $BASE_DIR/config/glut_tts_llm.yaml > $LOG_FILE 2>&1 &"
echo "日志命令 tail -100f $LOG_FILE"
nohup uv run $BASE_DIR/src/demo.py --config $BASE_DIR/config/glut_tts_llm.yaml > $LOG_FILE 2>&1 &

# 验证服务是否启动成功
sleep 20
NEW_PID=$(lsof -t -i:8283)

if [ ! -z "$NEW_PID" ]; then
	    echo "服务已成功启动，PID: $NEW_PID"
	        echo "日志输出到: $LOG_FILE"
	        tail -100f $LOG_FILE
	else
		    echo "服务启动失败，请检查日志"
		        tail -n 20 $LOG_FILE
fi
