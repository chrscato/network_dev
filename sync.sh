#!/bin/bash

# Sync files from /opt/network_dev to /srv/network_dev
ssh root@159.223.104.254 "mkdir -p /srv/network_dev && \
    cp -r /opt/network_dev/* /srv/network_dev/" 