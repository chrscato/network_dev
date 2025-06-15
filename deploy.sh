#!/bin/bash

# === CONFIGURATION ===
REMOTE_USER="root"
REMOTE_HOST="159.223.104.254"
REMOTE_DIR="/opt/network_dev"
SERVICE_NAME="network_dev"
APP_PORT="5005"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# === STEP 1: Check if we have uncommitted changes ===
print_step "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    print_warning "You have uncommitted changes. Committing them now..."
    
    # Show what's changed
    echo -e "\n${YELLOW}Changed files:${NC}"
    git status --porcelain
    
    # Prompt for commit message
    echo -e "\n📝 Enter your commit message (or press Enter for auto-generated):"
    read -r commit_message
    
    # Use default message if none provided
    if [ -z "$commit_message" ]; then
        commit_message="Auto-deploy: $(TZ='America/New_York' date '+%Y-%m-%d %H:%M:%S %Z')"
    else
        # Add timestamp to custom message
        commit_message="$commit_message - $(TZ='America/New_York' date '+%Y-%m-%d %H:%M:%S %Z')"
    fi
    
    git add .
    git commit -m "$commit_message"
    print_success "Changes committed"
else
    print_success "No uncommitted changes"
fi

# === STEP 2: Push to GitHub ===
print_step "Pushing to GitHub..."
if git push origin master; then
    print_success "Code pushed to GitHub"
else
    print_error "Failed to push to GitHub"
    exit 1
fi

# === STEP 3: Deploy to VM ===
print_step "Deploying to VM ($REMOTE_HOST)..."

# Create a comprehensive deployment script to run on the VM
ssh $REMOTE_USER@$REMOTE_HOST << EOF
    set -e
    
    echo "📁 Switching to project directory..."
    cd $REMOTE_DIR
    
    echo "🔄 Stopping service..."
    systemctl stop $SERVICE_NAME || echo "Service was not running"
    
    echo "📥 Pulling latest code..."
    git fetch origin
    # Reset everything except database and attachments
    git reset --hard origin/master
    git checkout origin/master -- .
    git reset -- database/ attachments/ contracts/
    
    echo "🐍 Updating Python environment..."
    source venv/bin/activate
    pip install -r requirements.txt
    
    echo "🗄️ Updating database..."
    export FLASK_APP=app.py
    export FLASK_ENV=production
    flask db upgrade
    
    echo "🔧 Updating systemd service..."
    cp network_dev.service /etc/systemd/system/
    systemctl daemon-reload
    
    echo "🚀 Starting service..."
    systemctl start $SERVICE_NAME
    systemctl enable $SERVICE_NAME
    
    echo "✅ Deployment complete!"
    
    # Show service status
    echo "📊 Service status:"
    systemctl status $SERVICE_NAME --no-pager -l
EOF

if [ $? -eq 0 ]; then
    print_success "Deployment completed successfully!"
    
    # === STEP 4: Health check ===
    print_step "Performing health check..."
    
    # Wait a moment for the service to start
    sleep 3
    
    # Check if the service is responding
    if curl -s -f http://$REMOTE_HOST:$APP_PORT > /dev/null; then
        print_success "Health check passed - app is responding"
        echo -e "${GREEN}🌐 Your app is live at: http://$REMOTE_HOST:$APP_PORT${NC}"
    else
        print_warning "Health check failed - app may still be starting"
        echo "💡 Check logs with: ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u $SERVICE_NAME -f'"
    fi
    
    # === STEP 5: Show useful commands ===
    echo -e "\n${BLUE}📋 Useful commands:${NC}"
    echo "View logs: ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u $SERVICE_NAME -f'"
    echo "Restart service: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl restart $SERVICE_NAME'"
    echo "Check status: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl status $SERVICE_NAME'"
    echo "SSH to server: ssh $REMOTE_USER@$REMOTE_HOST"
    
else
    print_error "Deployment failed!"
    echo "💡 Check the output above for errors"
    echo "💡 SSH to server to debug: ssh $REMOTE_USER@$REMOTE_HOST"
    exit 1
fi