# Trivia Game Server Installation

## Prerequisites
- Python 3.8+
- AWS Account with DynamoDB access
- Git (optional)

## Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS Credentials
```bash
# Option A: AWS CLI
aws configure

# Option B: Environment Variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-west-2
```

### 3. Initialize Database
```bash
python -c "from app_dynamodb import init_dynamodb; init_dynamodb()"
```

### 4. Run Server
```bash
python app_dynamodb.py
```

## Access Points
- **Game Homepage**: http://localhost:5000
- **Admin Login**: http://localhost:5000/admin
- **Admin Credentials**: username=`james`, password=`pango123`

## Production Deployment

### AWS EC2
```bash
# Install Python and dependencies
sudo yum update -y
sudo yum install python3 python3-pip -y
pip3 install -r requirements.txt

# Set environment variables
export AWS_REGION=us-west-2
export FLASK_ENV=production

# Run with Gunicorn
pip3 install gunicorn
gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:5000 app_dynamodb:app
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app_dynamodb.py"]
```

## Troubleshooting
- **DynamoDB Access**: Ensure IAM permissions for DynamoDB operations
- **Port 5000**: Change port in code if needed: `socketio.run(app, port=8080)`
- **CORS Issues**: Modify `cors_allowed_origins` in SocketIO config