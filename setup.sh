#!/bin/bash

# Setup environment and start service
ssh root@159.223.104.254 "cd /opt/network_dev && \
    rm -rf venv && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt && \
    export FLASK_APP=app.py && \
    export FLASK_ENV=production && \
    flask db init && \
    flask db migrate && \
    flask db upgrade && \
    systemctl restart network_dev.service" 