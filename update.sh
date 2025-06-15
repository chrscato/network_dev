#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check if the last command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

# Pull latest changes
git pull origin main
check_status "Pulled latest changes"

# Install dependencies
npm install
check_status "Dependencies installed"

# Restart the application using PM2
pm2 restart net_dev_portal
check_status "Application restarted"

echo -e "${GREEN}Update completed successfully!${NC}" 