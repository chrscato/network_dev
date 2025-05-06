#!/bin/bash

# Pull latest code on VM
ssh root@159.223.104.254 "cd /opt/network_dev && \
    if [ ! -d .git ]; then \
        rm -rf * && \
        git clone https://github.com/chrscato/network_dev.git .; \
    else \
        git fetch origin && \
        git reset --hard origin/master; \
    fi" 