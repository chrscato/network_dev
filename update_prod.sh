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
    # Create backup directories if they don't exist
    mkdir -p database_backup attachments_backup contracts_backup
    
    # Only copy if directories exist
    [ -d "database" ] && cp -r database/* database_backup/ 2>/dev/null || true
    [ -d "attachments" ] && cp -r attachments/* attachments_backup/ 2>/dev/null || true
    [ -d "contracts" ] && cp -r contracts/* contracts_backup/ 2>/dev/null || true
    
    echo "📥 Pulling latest code..."
    git fetch origin
    git reset --hard origin/master
    
    echo "📦 Restoring important files..."
    # Create directories if they don't exist
    mkdir -p database attachments contracts
    
    # Only restore if backup directories have content
    [ "$(ls -A database_backup)" ] && cp -r database_backup/* database/ 2>/dev/null || true
    [ "$(ls -A attachments_backup)" ] && cp -r attachments_backup/* attachments/ 2>/dev/null || true
    [ "$(ls -A contracts_backup)" ] && cp -r contracts_backup/* contracts/ 2>/dev/null || true
    
    # Clean up backup directories
    rm -rf database_backup attachments_backup contracts_backup
    
    echo "🔒 Setting proper permissions..."
    # Set ownership to www-data (the user running the Flask app)
    chown -R www-data:www-data database attachments contracts
    
    # Set directory permissions to 755 (drwxr-xr-x)
    find database attachments contracts -type d -exec chmod 755 {} \;
    
    # Set file permissions to 644 (rw-r--r--)
    find database attachments contracts -type f -exec chmod 644 {} \;
    
    # Make sure the database file itself is writable
    chmod 664 database/network_dev.db
    
    echo "🔄 Restarting service..."
    systemctl restart network_dev
    
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