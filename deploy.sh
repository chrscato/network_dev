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
    # Create necessary directories
    mkdir -p /opt/network_dev
    mkdir -p /srv/network_dev
    mkdir -p /opt/network_dev/backups

    # Clean and update code in /opt/network_dev
    cd /opt/network_dev
    if [ -d .git ]; then
        git fetch origin
        git reset --hard origin/master
        git clean -fd
    else
        rm -rf /opt/network_dev/*
        git clone git@github.com:chrscato/network_dev.git .
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi

    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install flask flask-sqlalchemy flask-migrate python-dotenv

    # Clean and prepare deployment directory
    rm -rf /srv/network_dev/*
    mkdir -p /srv/network_dev

    # Sync code to deployment directory, excluding sensitive files
    rsync -av --delete \
        --exclude '.env' \
        --exclude '*.db' \
        --exclude 'venv' \
        --exclude 'backups' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        /opt/network_dev/ /srv/network_dev/

    # Copy .env if it exists in /opt/network_dev
    if [ -f /opt/network_dev/.env ]; then
        cp /opt/network_dev/.env /srv/network_dev/.env
    fi

    # Create .env if it doesn't exist
    if [ ! -f /srv/network_dev/.env ]; then
        cat > /srv/network_dev/.env << 'EOL'
FLASK_APP=app.py
FLASK_ENV=production
DATABASE_URL=sqlite:///network_dev.db
SECRET_KEY=your-secret-key-here
EOL
    fi

    # Create virtual environment in deployment directory
    cd /srv/network_dev
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install flask flask-sqlalchemy flask-migrate python-dotenv

    # Initialize Flask-Migrate if not already done
    if [ ! -d "migrations" ]; then
        export FLASK_APP=app.py
        flask db init
    fi

    # Run database migrations
    export FLASK_APP=app.py
    flask db upgrade

    # Create systemd service
    cat > /etc/systemd/system/network_dev.service << 'EOL'
[Unit]
Description=Network Development Portal
After=network.target

[Service]
User=root
WorkingDirectory=/srv/network_dev
Environment="PATH=/srv/network_dev/venv/bin"
Environment="FLASK_APP=app.py"
Environment="FLASK_ENV=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/srv/network_dev/venv/bin/python -m flask run --host=0.0.0.0
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd and restart service
    systemctl daemon-reload
    systemctl enable network_dev
    systemctl stop network_dev
    sleep 2
    systemctl start network_dev
    sleep 2
    systemctl status network_dev
EOF

# Check if the deployment was successful
if [ $? -eq 0 ]; then
    print_status "✅ Deployment complete!"
    print_status "Application is running at: http://159.223.104.254:5000"
else
    print_error "Deployment failed!"
    exit 1
fi

# Run all deployment steps
./commit.sh
./pull.sh
./sync.sh

echo "✅ Deployment complete!" 