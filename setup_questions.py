#!/usr/bin/env python3
"""
Script to create a new DynamoDB table with trivia questions
and copy them to the game's question table
"""

import boto3
import json
import os

def load_questions_from_file(filename='questions.json'):
    """Load questions from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please create the questions file.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing {filename}: {e}")
        return []

def create_questions_source_table():
    """Create source table with trivia questions from file"""
    region = os.getenv('AWS_REGION', 'us-west-2')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    # Create source questions table
    try:
        source_table = dynamodb.create_table(
            TableName='trivia_questions_source',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        source_table.wait_until_exists()
        print("Created trivia_questions_source table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        source_table = dynamodb.Table('trivia_questions_source')
        print("trivia_questions_source table already exists")
    
    # Load questions from file
    questions = load_questions_from_file()
    if not questions:
        print("No questions loaded. Exiting.")
        return
    
    print(f"Loaded {len(questions)} questions from file")
    
    # Insert questions into source table
    for i, question in enumerate(questions):
        try:
            # Add ID to question
            question['id'] = str(i + 1)
            source_table.put_item(
                Item=question,
                ConditionExpression='attribute_not_exists(id)'
            )
        except Exception as e:
            print(f"Error inserting question {i+1}: {e}")
    
    print(f"Inserted {len(questions)} questions into source table")
    
    # Copy to game table
    try:
        game_table = dynamodb.create_table(
            TableName='trivia_questions',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        game_table.wait_until_exists()
        print("Created trivia_questions table")
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        game_table = dynamodb.Table('trivia_questions')
        print("trivia_questions table already exists")
    
    # Copy questions to game table
    for i, question in enumerate(questions):
        try:
            # Ensure ID is set
            question['id'] = str(i + 1)
            game_table.put_item(
                Item=question,
                ConditionExpression='attribute_not_exists(id)'
            )
        except Exception as e:
            print(f"Error copying question {i+1} to game table: {e}")
    
    print(f"Copied {len(questions)} questions to game table")

if __name__ == '__main__':
    create_questions_source_table()