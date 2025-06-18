#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
REMOTE_USER="root"
REMOTE_HOST="159.223.104.254"
REMOTE_PATH="/root/net_dev_portal"

# Function to check if the last command was successful
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

echo "Starting initial setup..."

# Copy setup script to VM
scp setup_vm.sh $REMOTE_USER@$REMOTE_HOST:/root/
check_status "Copied setup script to VM"

# Create remote directory if it doesn't exist
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH"
check_status "Created remote directory"

# Copy all project files to VM
echo "Copying project files..."
scp -r app.py requirements.txt static templates $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
check_status "Copied project files to VM"

# Copy .env file if it exists
if [ -f .env ]; then
    echo "Copying .env file..."
    scp .env $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
    check_status "Copied .env file"
else
    echo "Warning: No .env file found locally"
fi

# SSH into VM and run setup
echo "Running setup on VM..."
ssh $REMOTE_USER@$REMOTE_HOST "chmod +x /root/setup_vm.sh && /root/setup_vm.sh"
check_status "Setup completed on VM"

echo -e "${GREEN}Initial setup completed successfully!${NC}"
echo "The application should now be running at http://159.223.104.254:8765" 