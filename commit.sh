#!/bin/bash

# Force add and commit all changes
git add .
git commit -m "Auto-deploy: $(date)" || true  # || true ensures script continues even if no changes
git push origin master 