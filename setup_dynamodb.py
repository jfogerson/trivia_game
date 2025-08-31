#!/usr/bin/env python3
"""
Setup script for AWS DynamoDB tables
Run this once to create the DynamoDB tables
"""

import boto3
import os

def create_dynamodb_tables():
    """Create DynamoDB tables for trivia game"""
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-west-2'))
    
    tables_to_create = [
        {
            'TableName': 'trivia_admins',
            'KeySchema': [{'AttributeName': 'username', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'username', 'AttributeType': 'S'}],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'trivia_questions',
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'trivia_games',
            'KeySchema': [{'AttributeName': 'id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'id', 'AttributeType': 'S'}],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ]
    
    for table_config in tables_to_create:
        try:
            table = dynamodb.create_table(**table_config)
            print(f"Creating table: {table_config['TableName']}")
            table.wait_until_exists()
            print(f"Table {table_config['TableName']} created successfully!")
        except dynamodb.meta.client.exceptions.ResourceInUseException:
            print(f"Table {table_config['TableName']} already exists")
    
    print("All DynamoDB tables are ready!")

if __name__ == "__main__":
    print("Setting up DynamoDB tables for Trivia Game...")
    create_dynamodb_tables()
    print("\nSetup complete! You can now run the trivia game with:")
    print("python3 app_dynamodb.py")