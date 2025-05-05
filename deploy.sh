#!/bin/bash

# Configuration
REMOTE_HOST="root@159.223.104.254"
REMOTE_DIR="/opt/network_dev"
DEPLOY_DIR="/srv/network_dev"
BACKUP_DIR="/opt/network_dev/backups"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}Error:${NC} $1"
}

# Function to create backup
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/network_dev_${timestamp}.db"
    
    print_status "Creating database backup..."
    ssh $REMOTE_HOST "mkdir -p $BACKUP_DIR && \
        if [ -f $DEPLOY_DIR/network_dev.db ]; then \
            cp $DEPLOY_DIR/network_dev.db $backup_file; \
        fi"
}

# Run all deployment steps
./commit.sh
./pull.sh
./sync.sh

echo "✅ Deployment complete!" 