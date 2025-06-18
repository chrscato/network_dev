#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Node.js and npm (required for PM2)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -y pm2 -g

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install and configure firewall
sudo apt-get install -y ufw
sudo ufw allow 8765/tcp
sudo ufw allow ssh
sudo ufw --force enable

# Create app directory
mkdir -p /root/net_dev_portal
cd /root/net_dev_portal

# Copy all files from local machine (run this from your local machine)
# scp -r ./* root@159.223.104.254:/root/net_dev_portal/

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn

# Create environment file
cat > .env << EOL
# Add your environment variables here
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=0
PORT=8765
EOL

# Create a startup script
cat > start.sh << EOL
#!/bin/bash
cd /root/net_dev_portal
source venv/bin/activate
gunicorn --bind 0.0.0.0:8765 --workers 4 --timeout 120 app:app
EOL

chmod +x start.sh

# Stop any existing PM2 processes
pm2 delete net_dev_portal 2>/dev/null || true

# Start the application with PM2
pm2 start start.sh --name "net_dev_portal"
pm2 save
pm2 startup

# Check if the application is running
sleep 5
if curl -s http://localhost:8765 > /dev/null; then
    echo "Application is running successfully!"
else
    echo "Warning: Application might not be running properly. Check logs with: pm2 logs net_dev_portal"
fi

echo "Setup completed!"
echo "The application should be running on http://159.223.104.254:8765"
echo "To check logs: pm2 logs net_dev_portal"
echo "To check status: pm2 status" 