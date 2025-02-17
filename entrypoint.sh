#!/bin/bash

# 启动 server.py 服务
if [ -f /app/server.py ]; then
    echo "Starting server.py to handle snapshoot requests..."
    python /app/server.py > /var/log/server.log 2>&1 &
else
    echo "Error: /app/server.py not found!"
    exit 1
fi

# 安装 napcat
if [ ! -f "napcat/napcat.mjs" ]; then
    unzip -q NapCat.Shell.zip -d ./NapCat.Shell
    cp -rf NapCat.Shell/* napcat/
    rm -rf ./NapCat.Shell
fi
if [ ! -f "napcat/config/napcat.json" ]; then
    unzip -q NapCat.Shell.zip -d ./NapCat.Shell
    cp -rf NapCat.Shell/config/* napcat/config/
    rm -rf ./NapCat.Shell
fi

# 配置 WebUI Token
CONFIG_PATH=/app/napcat/config/webui.json

if [ ! -f "${CONFIG_PATH}" ] && [ -n "${WEBUI_TOKEN}" ]; then
    echo "正在配置 WebUI Token..."
    cat > "${CONFIG_PATH}" << EOF
{
    "host": "0.0.0.0",
    "prefix": "${WEBUI_PREFIX}",
    "port": 6099,
    "token": "${WEBUI_TOKEN}",
    "loginRate": 3
}
EOF
fi

rm -rf "/tmp/.X1-lock"

: ${NAPCAT_GID:=0}
: ${NAPCAT_UID:=0}
usermod -o -u ${NAPCAT_UID} napcat
groupmod -o -g ${NAPCAT_GID} napcat
usermod -g ${NAPCAT_GID} napcat
chown -R ${NAPCAT_UID}:${NAPCAT_GID} /app

# 启动 Xvfb 服务
gosu napcat Xvfb :1 -screen 0 1080x760x16 +extension GLX +render > /dev/null 2>&1 &
sleep 2

# 环境变量
export FFMPEG_PATH=/usr/bin/ffmpeg
export DISPLAY=:1

# 启动 cron 服务
service cron start

# 启动 NapCat 和 QQ 服务
cd /app/napcat
ACCOUNT=$(ls /app/napcat/config/ | grep -oE '[1-9][0-9]{4,12}' | head -n 1)
gosu napcat /opt/QQ/qq --no-sandbox -q $ACCOUNT