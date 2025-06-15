#!/bin/bash

# === CONFIGURATION ===
REMOTE_USER="root"
REMOTE_HOST="159.223.104.254"
REMOTE_DIR="/opt/network_dev"

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
        commit_message="Update: $(TZ='America/New_York' date '+%Y-%m-%d %H:%M:%S %Z')"
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

# === STEP 3: Update VM ===
print_step "Updating VM ($REMOTE_HOST)..."

# Create a script to run on the VM that preserves important files
ssh $REMOTE_USER@$REMOTE_HOST << EOF
    set -e
    
    echo "📁 Switching to project directory..."
    cd $REMOTE_DIR
    
    echo "💾 Backing up important files..."
    cp -r database/ database_backup/
    cp -r attachments/ attachments_backup/
    cp -r contracts/ contracts_backup/
    
    echo "📥 Pulling latest code..."
    git fetch origin
    git reset --hard origin/master
    
    echo "📦 Restoring important files..."
    rm -rf database/ attachments/ contracts/
    mv database_backup/ database/
    mv attachments_backup/ attachments/
    mv contracts_backup/ contracts/
    
    echo "✅ Update complete!"
EOF

if [ $? -eq 0 ]; then
    print_success "VM updated successfully!"
else
    print_error "VM update failed!"
    echo "💡 Check the output above for errors"
    echo "💡 SSH to server to debug: ssh $REMOTE_USER@$REMOTE_HOST"
    exit 1
fi 