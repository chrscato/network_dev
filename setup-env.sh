#!/bin/bash

# === CONFIGURATION ===
REMOTE_USER="root"
REMOTE_HOST="159.223.104.254"
REMOTE_DIR="/opt/network_dev"

echo "🔧 Setting up environment variables on VM..."

# Check if local .env exists
if [ ! -f ".env" ]; then
    echo "❌ No .env file found locally. Please create one first."
    echo "💡 Copy from .env.example: cp .env.example .env"
    exit 1
fi

echo "📤 Copying .env file to VM..."
scp .env $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/.env

echo "🔒 Setting proper permissions on .env file..."
ssh $REMOTE_USER@$REMOTE_HOST "chmod 600 $REMOTE_DIR/.env"

echo "✅ Environment variables configured on VM"

# Optionally, restart the service to pick up new environment variables
read -p "🔄 Restart the service to apply new environment variables? (y/N): " restart_service
if [[ $restart_service =~ ^[Yy]$ ]]; then
    ssh $REMOTE_USER@$REMOTE_HOST "systemctl restart network_dev"
    echo "✅ Service restarted"
fi