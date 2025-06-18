#!/bin/bash

# Remote VM Cleanup Script
# Run this from your local machine to clean up the VM at 159.223.104.254

VM_IP="159.223.104.254"
VM_USER="root"  # Change this to your VM username if different

echo "=== REMOTE VM CLEANUP SCRIPT ==="
echo "Target VM: $VM_IP"
echo "Date: $(date)"
echo "================================="

# Function to run commands on remote VM
run_remote() {
    local command="$1"
    echo "Running on VM: $command"
    ssh $VM_USER@$VM_IP "$command"
}

# Function to run interactive commands on remote VM
run_remote_interactive() {
    local command="$1"
    ssh -t $VM_USER@$VM_IP "$command"
}

echo -e "\n=== STEP 1: TEST CONNECTION ==="
echo "==============================="
echo "Testing SSH connection to VM..."
if ssh -o ConnectTimeout=5 $VM_USER@$VM_IP "echo 'Connection successful!'" 2>/dev/null; then
    echo "✓ SSH connection working"
else
    echo "✗ SSH connection failed!"
    echo "Please check:"
    echo "1. VM is running"
    echo "2. SSH key is set up"
    echo "3. VM_USER is correct (current: $VM_USER)"
    exit 1
fi

echo -e "\n=== STEP 2: AUDIT VM WEB APPLICATIONS ==="
echo "========================================"

echo -e "\n2.1 Running web servers:"
run_remote "ps aux | grep -E '(apache2|httpd|nginx)' | grep -v grep || echo 'No web servers found'"

echo -e "\n2.2 Python/Flask applications:"
run_remote "ps aux | grep python | grep -v grep || echo 'No Python processes found'"

echo -e "\n2.3 Node.js applications:"
run_remote "ps aux | grep node | grep -v grep || echo 'No Node.js processes found'"

echo -e "\n2.4 Application servers:"
run_remote "ps aux | grep -E '(gunicorn|uwsgi|pm2|celery)' | grep -v grep || echo 'No app servers found'"

echo -e "\n2.5 Listening ports:"
run_remote "netstat -tulpn | grep -E ':(80|443|8000|8080|5000|3000|9000|8888)' || echo 'No common web ports in use'"

echo -e "\n2.6 Systemd services:"
run_remote "systemctl list-units --type=service --state=active | grep -E '(apache|nginx|httpd|gunicorn|uwsgi|flask|django)' || echo 'No web-related services found'"

echo -e "\n=== STEP 3: INTERACTIVE CLEANUP MENU ==="
echo "======================================="

while true; do
    echo -e "\nRemote VM Cleanup Options:"
    echo "1) Stop all Python/Flask processes"
    echo "2) Stop Apache2 service"
    echo "3) Stop Nginx service"
    echo "4) Stop Gunicorn processes"
    echo "5) Stop all Node.js processes"
    echo "6) Show Flask project directories"
    echo "7) Clean up large log files"
    echo "8) Show current VM status"
    echo "9) Open interactive SSH session"
    echo "10) Upload and run comprehensive cleanup script"
    echo "0) Exit"
    
    read -p "Enter your choice (0-10): " choice
    
    case $choice in
        1)
            echo "Stopping Python/Flask processes on VM..."
            run_remote "pkill -f python; pkill -f flask"
            echo "Python/Flask processes stopped"
            ;;
        2)
            echo "Stopping Apache2 on VM..."
            run_remote "systemctl stop apache2; systemctl disable apache2"
            ;;
        3)
            echo "Stopping Nginx on VM..."
            run_remote "systemctl stop nginx; systemctl disable nginx"
            ;;
        4)
            echo "Stopping Gunicorn on VM..."
            run_remote "pkill -f gunicorn"
            ;;
        5)
            echo "Stopping Node.js on VM..."
            run_remote "pkill -f node"
            ;;
        6)
            echo "Flask project directories on VM:"
            run_remote "find /home -name 'app.py' -o -name '*.py' | grep -E '(flask|app)' 2>/dev/null | head -10"
            run_remote "find /var/www -name 'app.py' -o -name '*.py' 2>/dev/null | head -5"
            ;;
        7)
            echo "Large log files on VM:"
            run_remote "find /var/log -name '*.log' -type f -size +100M -exec ls -lh {} \; 2>/dev/null"
            read -p "Truncate large log files? (y/n): " confirm
            if [[ $confirm == "y" ]]; then
                run_remote "find /var/log -name '*.log' -type f -size +100M -exec truncate -s 0 {} \;"
                echo "Large log files truncated"
            fi
            ;;
        8)
            echo "Current VM status:"
            run_remote "ps aux | grep -E '(python|node|apache|nginx|gunicorn)' | grep -v grep || echo 'No web processes running'"
            run_remote "netstat -tulpn | grep -E ':(80|443|8000|8080|5000|3000)' || echo 'No web ports in use'"
            ;;
        9)
            echo "Opening interactive SSH session to VM..."
            echo "Type 'exit' to return to this script"
            run_remote_interactive "bash"
            ;;
        10)
            echo "Uploading comprehensive cleanup script..."
            # Create the comprehensive script
            cat > /tmp/vm_comprehensive_cleanup.sh << 'EOF'
#!/bin/bash
echo "=== COMPREHENSIVE VM CLEANUP ==="
echo "Date: $(date)"
echo "================================"

# Stop all web-related services
echo "Stopping web services..."
for service in apache2 nginx httpd; do
    if systemctl is-active --quiet $service; then
        systemctl stop $service
        systemctl disable $service
        echo "✓ Stopped $service"
    fi
done

# Kill web application processes
echo "Stopping web application processes..."
pkill -f "python.*flask" 2>/dev/null && echo "✓ Stopped Flask processes"
pkill -f "gunicorn" 2>/dev/null && echo "✓ Stopped Gunicorn processes"
pkill -f "uwsgi" 2>/dev/null && echo "✓ Stopped uWSGI processes"
pkill -f "node" 2>/dev/null && echo "✓ Stopped Node.js processes"

# Clean up logs
echo "Cleaning up large log files..."
find /var/log -name "*.log" -type f -size +100M -exec truncate -s 0 {} \; 2>/dev/null
echo "✓ Log files cleaned"

# Show final status
echo "=== FINAL STATUS ==="
echo "Running web processes:"
ps aux | grep -E "(python|node|apache|nginx|gunicorn)" | grep -v grep || echo "None"
echo "Listening web ports:"
netstat -tulpn | grep -E ":(80|443|8000|8080|5000|3000)" || echo "None"
echo "Cleanup complete!"
EOF
            
            # Upload and run the script
            scp /tmp/vm_comprehensive_cleanup.sh $VM_USER@$VM_IP:/tmp/
            run_remote "chmod +x /tmp/vm_comprehensive_cleanup.sh && /tmp/vm_comprehensive_cleanup.sh"
            run_remote "rm /tmp/vm_comprehensive_cleanup.sh"
            rm /tmp/vm_comprehensive_cleanup.sh
            ;;
        0)
            echo "Remote cleanup complete!"
            break
            ;;
        *)
            echo "Invalid choice. Please try again."
            ;;
    esac
    
    echo -e "\nPress Enter to continue..."
    read
done

echo -e "\n=== CLEANUP SUMMARY ==="
echo "======================"
echo "VM cleanup operations completed from local machine"
run_remote "echo 'Final VM status:' && ps aux | grep -E '(python|node|apache|nginx)' | grep -v grep || echo 'No web processes running'"