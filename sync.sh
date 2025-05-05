#!/bin/bash

# Sync non-git files to VM using scp
scp -r app.py root@159.223.104.254:/opt/network_dev/
scp -r templates root@159.223.104.254:/opt/network_dev/
scp -r static root@159.223.104.254:/opt/network_dev/
scp -r migrations root@159.223.104.254:/opt/network_dev/
scp requirements.txt root@159.223.104.254:/opt/network_dev/ 