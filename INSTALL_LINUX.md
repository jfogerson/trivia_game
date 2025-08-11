# Linux Installation Guide

## File Location on Windows
All files are currently located at:
```
c:\Users\jamfog02\OneDrive - Robert Half\PythonFiles\trivia_game\
```

## Step-by-Step Linux Installation

### 1. Transfer Files to Linux
```bash
# On Linux server, create directory
mkdir ~/trivia_game
cd ~/trivia_game

# Transfer these files from Windows:
# - app_dynamodb.py (recommended)
# - requirements.txt  
# - setup_dynamodb.py
# - admin_game.html
# - templates/ (entire folder)
# - README.md
# - README_AWS.md
```

### 2. Install System Requirements
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv awscli

# CentOS/RHEL
sudo yum install python3 python3-pip awscli
```

### 3. Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure AWS
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter your default region (e.g., us-east-1)
# Enter output format: json
```

### 5. Create DynamoDB Tables
```bash
python3 setup_dynamodb.py
```

### 6. Run the Game
```bash
# Development
python3 app_dynamodb.py

# Production
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 app_dynamodb:app --bind 0.0.0.0:5000
```

### 7. Access the Game
- Game: http://your-server-ip:5000
- Admin: http://your-server-ip:5000/admin
- Default admin: username=`admin`, password=`admin123`

## Firewall Configuration
```bash
# Allow port 5000
sudo ufw allow 5000
# OR for iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

## Systemd Service (Optional)
Create `/etc/systemd/system/trivia.service`:
```ini
[Unit]
Description=Trivia Game
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trivia_game
Environment=PATH=/home/ubuntu/trivia_game/venv/bin
ExecStart=/home/ubuntu/trivia_game/venv/bin/gunicorn --worker-class eventlet -w 1 app_dynamodb:app --bind 0.0.0.0:5000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable trivia
sudo systemctl start trivia
```

## Troubleshooting
- Check logs: `journalctl -u trivia -f`
- Verify AWS credentials: `aws sts get-caller-identity`
- Test DynamoDB access: `aws dynamodb list-tables`