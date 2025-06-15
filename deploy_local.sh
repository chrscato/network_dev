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

# Commit changes if there are any
git add .
if git diff --staged --quiet; then
    echo "No changes to commit"
else
    read -p "Enter commit message: " commit_message
    git commit -m "$commit_message"
    check_status "Changes committed"
fi

# Push changes to remote repository
git push origin master
check_status "Changes pushed to repository"

# SSH into the VM and run the update script
ssh $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && ./update.sh"
check_status "Remote deployment completed"

echo -e "${GREEN}Deployment completed successfully!${NC}" 