#!/bin/bash

# Sync non-git files to VM
rsync -av \
    --exclude '.git' \
    --exclude '.env' \
    --exclude '*.db' \
    --exclude 'venv' \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    ./ root@159.223.104.254:/opt/network_dev/ 