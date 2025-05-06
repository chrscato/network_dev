#!/bin/bash

# Pull latest changes from git repository and sync to both directories
ssh root@159.223.104.254 "cd /opt/network_dev && git pull && \
    mkdir -p /srv/network_dev && \
    cp -r /opt/network_dev/* /srv/network_dev/" 