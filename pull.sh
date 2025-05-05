#!/bin/bash

# Pull latest code on VM
ssh root@159.223.104.254 "cd /opt/network_dev && \
    if [ ! -d .git ]; then \
        git clone https://github.com/chrscato/network_dev.git .; \
    else \
        git pull origin master; \
    fi" 