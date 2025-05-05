#!/bin/bash

# Configuration
REMOTE_HOST="root@159.223.104.254"
REMOTE_DIR="/opt/network_dev"
LOCAL_DIR="$(pwd)"

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

# Check if we have uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_status "You have uncommitted changes. Please commit or stash them before deploying."
    exit 1
fi

# Push local changes
print_status "Pushing changes to GitHub..."
git add .
git commit -m "Deploy: $(date)"
git push origin master

# Deploy to server
print_status "Deploying to server..."
ssh $REMOTE_HOST << EOF
    # Create directory if it doesn't exist
    mkdir -p $REMOTE_DIR

    # Pull latest changes
    cd $REMOTE_DIR
    if [ -d .git ]; then
        git pull origin master
    else
        git clone https://github.com/your-username/network_dev.git .
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install -r requirements.txt

    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
    fi

    # Run database migrations
    flask db upgrade

    # Restart the application service if it exists
    if systemctl is-active --quiet network_dev; then
        systemctl restart network_dev
    fi
EOF

# Check if the deployment was successful
if [ $? -eq 0 ]; then
    print_status "✅ Deployment complete!"
else
    print_error "Deployment failed!"
    exit 1
fi 