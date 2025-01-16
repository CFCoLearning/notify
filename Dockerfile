FROM python:3.12-slim

RUN useradd --no-log-init -d /app napcat
WORKDIR /app

COPY NapCat.Shell.zip entrypoint.sh snapshoot.py server.py /app/

RUN apt update && \
    apt install -y \
        pandoc \
        wget \
        curl \
        unzip \
        cron \
        xvfb \
        gosu \
        && apt clean && \
    pip install --no-cache-dir requests selenium flask

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -O /tmp/chrome.deb \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb

RUN arch=$(arch | sed s/aarch64/arm64/ | sed s/x86_64/amd64/) && \
    curl -o linuxqq.deb https://dldir1.qq.com/qqfile/qq/QQNT/63c751e8/linuxqq_3.2.15-30899_${arch}.deb && \
    dpkg -i --force-depends linuxqq.deb && rm linuxqq.deb && \
    chmod +x entrypoint.sh && \
    echo "(async () => {await import('file:///app/napcat/napcat.mjs');})();" > /opt/QQ/resources/app/loadNapCat.js && \
    sed -i 's|"main": "[^"]*"|"main": "./loadNapCat.js"|' /opt/QQ/resources/app/package.json

RUN mkdir -p /app/napcat/config && \
    mkdir -p /tmp/table && \
    chown -R root:root /app && \
    chown -R root:root /tmp/table

VOLUME /app/napcat/config
VOLUME /app/.config/QQ
VOLUME /tmp/table

# 确保 entrypoint.sh 可执行
RUN chmod +x /app/entrypoint.sh /app/snapshoot.py /app/server.py

# 运行入口脚本
ENTRYPOINT ["bash", "/app/entrypoint.sh"]
