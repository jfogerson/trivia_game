#!/usr/bin/env python3
"""
Setup script for AWS RDS PostgreSQL database
Run this once to create the RDS instance and configure it
"""

import boto3
import os
import time

def create_rds_instance():
    """Create RDS PostgreSQL instance"""
    rds = boto3.client('rds')
    
    try:
        response = rds.create_db_instance(
            DBInstanceIdentifier='trivia-game-db',
            DBInstanceClass='db.t3.micro',
            Engine='postgres',
            MasterUsername='trivia_admin',
            MasterUserPassword='TriviaGame123!',
            AllocatedStorage=20,
            VpcSecurityGroupIds=[
                # Add your security group ID here
            ],
            DBName='trivia',
            BackupRetentionPeriod=7,
            MultiAZ=False,
            PubliclyAccessible=True,
            StorageType='gp2',
            StorageEncrypted=True
        )
        
        print(f"Creating RDS instance: {response['DBInstance']['DBInstanceIdentifier']}")
        print("This may take 10-15 minutes...")
        
        # Wait for instance to be available
        waiter = rds.get_waiter('db_instance_available')
        waiter.wait(DBInstanceIdentifier='trivia-game-db')
        
        # Get endpoint
        response = rds.describe_db_instances(DBInstanceIdentifier='trivia-game-db')
        endpoint = response['DBInstances'][0]['Endpoint']['Address']
        
        print(f"RDS instance created successfully!")
        print(f"Endpoint: {endpoint}")
        print(f"Database: trivia")
        print(f"Username: trivia_admin")
        print(f"Password: TriviaGame123!")
        
        return endpoint
        
    except Exception as e:
        print(f"Error creating RDS instance: {e}")
        return None

def setup_environment_variables(endpoint):
    """Setup environment variables for database connection"""
    env_vars = f"""
# Add these environment variables to your system or .env file:
export RDS_HOST="{endpoint}"
export RDS_DB="trivia"
export RDS_USER="trivia_admin"
export RDS_PASSWORD="TriviaGame123!"
export RDS_PORT="5432"
"""
    
    with open('.env', 'w') as f:
        f.write(f"""RDS_HOST={endpoint}
RDS_DB=trivia
RDS_USER=trivia_admin
RDS_PASSWORD=TriviaGame123!
RDS_PORT=5432
""")
    
    print(env_vars)
    print("Environment variables saved to .env file")

if __name__ == "__main__":
    print("Setting up AWS RDS for Trivia Game...")
    endpoint = create_rds_instance()
    if endpoint:
        setup_environment_variables(endpoint)
        print("\nSetup complete! You can now run the trivia game with:")
        print("python3 app.py")