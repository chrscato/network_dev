#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Create app directory
mkdir -p /root/net_dev_portal
cd /root/net_dev_portal

# Clone the repository
git clone https://github.com/chrscato/network_dev.git .
git checkout master

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cat > .env << EOL
# Add your environment variables here
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=0
EOL

# Install and configure Gunicorn
pip install gunicorn

# Start the application with PM2
pm2 start gunicorn --name "net_dev_portal" -- --bind 0.0.0.0:5000 app:app
pm2 save
pm2 startup

echo "Setup completed successfully!" 