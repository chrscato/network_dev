#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -y pm2 -g

# Create app directory
mkdir -p /root/net_dev_portal
cd /root/net_dev_portal

# Clone the repository (replace with your actual repository URL)
git clone https://github.com/yourusername/your-repo.git .

# Install dependencies
npm install

# Create environment file
cat > .env << EOL
# Add your environment variables here
PORT=3000
NODE_ENV=production
EOL

# Start the application with PM2
pm2 start npm --name "net_dev_portal" -- start
pm2 save
pm2 startup

echo "Setup completed successfully!" 