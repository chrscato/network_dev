#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== System Information ===${NC}"
# Check disk usage
echo -e "\n${GREEN}Disk Usage:${NC}"
df -h

# Check memory usage
echo -e "\n${GREEN}Memory Usage:${NC}"
free -h

# Check running processes
echo -e "\n${GREEN}Top 10 Memory-Using Processes:${NC}"
ps aux --sort=-%mem | head -n 11

# Check system load
echo -e "\n${GREEN}System Load:${NC}"
uptime

echo -e "\n${YELLOW}=== Cleaning Up ===${NC}"

# Remove old package versions
echo -e "\n${GREEN}Cleaning apt cache...${NC}"
sudo apt-get clean
sudo apt-get autoremove -y

# Remove old logs
echo -e "\n${GREEN}Cleaning old logs...${NC}"
sudo find /var/log -type f -name "*.gz" -delete
sudo find /var/log -type f -name "*.old" -delete
sudo journalctl --vacuum-time=3d

# Clean up temporary files
echo -e "\n${GREEN}Cleaning temporary files...${NC}"
sudo rm -rf /tmp/*
sudo rm -rf /var/tmp/*

# Check for large files
echo -e "\n${GREEN}Top 10 Largest Files:${NC}"
sudo find / -type f -exec du -Sh {} + 2>/dev/null | sort -rh | head -n 10

# Check for old PM2 logs
echo -e "\n${GREEN}Cleaning PM2 logs...${NC}"
pm2 flush
pm2 flush net_dev_portal

# Restart PM2 to ensure clean state
echo -e "\n${GREEN}Restarting PM2...${NC}"
pm2 restart all

echo -e "\n${YELLOW}=== After Cleanup ===${NC}"
# Show updated disk usage
echo -e "\n${GREEN}Updated Disk Usage:${NC}"
df -h

echo -e "\n${GREEN}Cleanup completed!${NC}"
echo "To monitor system resources in real-time, use: htop"
echo "To check application logs: pm2 logs net_dev_portal" 