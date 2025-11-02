#!/usr/bin/env python3
"""
Trivia Game Server Setup Script
Automates installation and configuration
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_aws_region():
    """Set default AWS region if not configured"""
    if not os.getenv('AWS_REGION'):
        os.environ['AWS_REGION'] = 'us-west-2'
        print("Set AWS_REGION to us-west-2")

def initialize_database():
    """Initialize DynamoDB tables"""
    print("Initializing DynamoDB tables...")
    try:
        from app_dynamodb import init_dynamodb
        init_dynamodb()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        print("Please configure AWS credentials and try again")

def main():
    """Run complete setup"""
    print("=== Trivia Game Server Setup ===")
    
    try:
        install_dependencies()
        setup_aws_region()
        initialize_database()
        
        print("\n✅ Setup complete!")
        print("Run: python app_dynamodb.py")
        print("Access: http://localhost:5000")
        print("Admin: username=james, password=pango123")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()