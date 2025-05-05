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
ssh $REMOTE_HOST << 'EOF'
    # Create directory if it doesn't exist
    mkdir -p /opt/network_dev

    # Pull latest changes
    cd /opt/network_dev
    if [ -d .git ]; then
        git pull origin master
    else
        # Use SSH URL instead of HTTPS
        git clone git@github.com:chrscato/network_dev.git .
    fi

    # Install system dependencies
    apt-get update
    apt-get install -y python3-venv python3-pip

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install flask flask-sqlalchemy flask-migrate python-dotenv

    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        cat > .env << 'EOL'
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=sqlite:///network_dev.db
SECRET_KEY=your-secret-key-here
EOL
    fi

    # Run database migrations if flask-migrate is installed
    if command -v flask &> /dev/null; then
        export FLASK_APP=app.py
        flask db upgrade
    fi

    # Create systemd service if it doesn't exist
    if [ ! -f /etc/systemd/system/network_dev.service ]; then
        cat > /etc/systemd/system/network_dev.service << 'EOL'
[Unit]
Description=Network Development Portal
After=network.target

[Service]
User=root
WorkingDirectory=/opt/network_dev
Environment="PATH=/opt/network_dev/venv/bin"
ExecStart=/opt/network_dev/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL
        systemctl daemon-reload
        systemctl enable network_dev
    fi

    # Restart the application service
    systemctl restart network_dev
EOF

# Check if the deployment was successful
if [ $? -eq 0 ]; then
    print_status "✅ Deployment complete!"
    print_status "Application is running at: http://159.223.104.254:5000"
else
    print_error "Deployment failed!"
    exit 1
fi 