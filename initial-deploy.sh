#!/bin/bash

# === CONFIGURATION ===
REMOTE_USER="root"
REMOTE_HOST="159.223.104.254"
REMOTE_DIR="/opt/network_dev"
LOCAL_PROJECT_DIR="."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting initial deployment to VM...${NC}"

# === STEP 1: Create remote directory ===
echo -e "${YELLOW}📁 Creating remote directory...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

# === STEP 2: Copy project files ===
echo -e "${YELLOW}📤 Copying project files to VM...${NC}"

# Use rsync for better file transfer (excludes common files we don't want)
rsync -avz --progress \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.db' \
  --exclude='venv' \
  --exclude='node_modules' \
  --exclude='.DS_Store' \
  --exclude='logs/' \
  --exclude='contracts/' \
  --include='.env' \
  $LOCAL_PROJECT_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# === STEP 3: Set up Git repository on remote ===
echo -e "${YELLOW}🔧 Setting up Git repository on VM...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << EOF
  cd $REMOTE_DIR
  
  # Initialize git if not already done
  if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git remote add origin https://github.com/chrscato/network_dev.git
  fi
  
  # Set up git config (adjust with your details)
  git config user.name "VM Deploy"
  git config user.email "deploy@clarity-dx.com"
  
  echo "✅ Git repository set up"
EOF

# === STEP 4: Set up Python environment ===
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << EOF
  cd $REMOTE_DIR
  
  # Install Python 3 and pip if not installed
  apt update
  apt install -y python3 python3-pip python3-venv git
  
  # Create virtual environment
  echo "🔨 Creating virtual environment..."
  python3 -m venv venv
  
  # Activate and install requirements
  echo "📦 Installing Python packages..."
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  
  echo "✅ Python environment ready"
EOF

# === STEP 5: Set up database ===
echo -e "${YELLOW}🗄️ Setting up database...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << EOF
  cd $REMOTE_DIR
  source venv/bin/activate
  
  # Set up Flask environment
  export FLASK_APP=app.py
  export FLASK_ENV=production
  
  # Initialize database
  echo "🏗️ Initializing database..."
  flask db init || echo "Database already initialized"
  flask db migrate -m "Initial migration" || echo "Migration files exist"
  flask db upgrade
  
  echo "✅ Database ready"
EOF

# === STEP 6: Set up systemd service ===
echo -e "${YELLOW}⚙️ Setting up systemd service...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << EOF
  # Copy the service file to systemd
  cp $REMOTE_DIR/network_dev.service /etc/systemd/system/
  
  # Reload systemd and enable the service
  systemctl daemon-reload
  systemctl enable network_dev.service
  systemctl start network_dev.service
  
  echo "✅ Service configured and started"
EOF

echo -e "${GREEN}🎉 Initial deployment complete!${NC}"
echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Check service status: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl status network_dev.service'"
echo "2. View logs: ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u network_dev.service -f'"
echo "3. Test the app: curl http://$REMOTE_HOST:5005"
echo "4. Use the deploy.sh script for future updates"