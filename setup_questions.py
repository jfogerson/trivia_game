#!/usr/bin/env python3
"""
Script to create a new DynamoDB table with trivia questions
and copy them to the game's question table
"""

import boto3
import os

def create_questions_source_table():
    """Create source table with comprehensive trivia questions"""
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
    
    # Comprehensive question set
    questions = [
        ("What is the capital of France?", "London", "Berlin", "Paris", "Madrid", "c"),
        ("Which planet is closest to the Sun?", "Venus", "Mercury", "Earth", "Mars", "b"),
        ("What is 2 + 2?", "3", "4", "5", "6", "b"),
        ("Who painted the Mona Lisa?", "Van Gogh", "Picasso", "Da Vinci", "Monet", "c"),
        ("What is the largest ocean?", "Atlantic", "Indian", "Arctic", "Pacific", "d"),
        ("What year did World War II end?", "1944", "1945", "1946", "1947", "b"),
        ("What is the chemical symbol for gold?", "Go", "Gd", "Au", "Ag", "c"),
        ("Which country invented pizza?", "Greece", "Italy", "Spain", "France", "b"),
        ("What is the smallest country in the world?", "Monaco", "Vatican City", "San Marino", "Liechtenstein", "b"),
        ("Who wrote Romeo and Juliet?", "Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain", "b"),
        ("What is the hardest natural substance?", "Gold", "Iron", "Diamond", "Platinum", "c"),
        ("Which gas makes up most of Earth's atmosphere?", "Oxygen", "Nitrogen", "Carbon Dioxide", "Hydrogen", "b"),
        ("What is the largest mammal?", "Elephant", "Blue Whale", "Giraffe", "Hippopotamus", "b"),
        ("In which year did the Titanic sink?", "1910", "1911", "1912", "1913", "c"),
        ("What is the currency of Japan?", "Yuan", "Won", "Yen", "Rupee", "c"),
        ("Which continent is the Sahara Desert located in?", "Asia", "Africa", "Australia", "South America", "b"),
        ("What is the square root of 64?", "6", "7", "8", "9", "c"),
        ("Who developed the theory of relativity?", "Newton", "Einstein", "Galileo", "Darwin", "b"),
        ("What is the longest river in the world?", "Amazon", "Nile", "Mississippi", "Yangtze", "b"),
        ("Which element has the atomic number 1?", "Helium", "Hydrogen", "Lithium", "Carbon", "b"),
        ("What is the capital of Australia?", "Sydney", "Melbourne", "Canberra", "Perth", "c"),
        ("Who painted The Starry Night?", "Picasso", "Van Gogh", "Monet", "Da Vinci", "b"),
        ("What is the largest planet in our solar system?", "Saturn", "Jupiter", "Neptune", "Uranus", "b"),
        ("Which ocean is the deepest?", "Atlantic", "Indian", "Arctic", "Pacific", "d"),
        ("What is the most abundant element in the universe?", "Oxygen", "Hydrogen", "Carbon", "Nitrogen", "b"),
        ("Who wrote '1984'?", "Aldous Huxley", "George Orwell", "Ray Bradbury", "H.G. Wells", "b"),
        ("What is the speed of light?", "300,000 km/s", "150,000 km/s", "450,000 km/s", "600,000 km/s", "a"),
        ("Which country has the most time zones?", "Russia", "USA", "China", "Canada", "a"),
        ("What is the smallest bone in the human body?", "Stapes", "Malleus", "Incus", "Radius", "a"),
        ("Who composed The Four Seasons?", "Bach", "Mozart", "Vivaldi", "Beethoven", "c"),
        ("What is the chemical formula for water?", "H2O", "CO2", "NaCl", "CH4", "a"),
        ("Which mountain range contains Mount Everest?", "Andes", "Himalayas", "Rockies", "Alps", "b"),
        ("What is the largest desert in the world?", "Sahara", "Gobi", "Antarctica", "Arabian", "c"),
        ("Who invented the telephone?", "Edison", "Bell", "Tesla", "Marconi", "b"),
        ("What is the capital of Canada?", "Toronto", "Vancouver", "Ottawa", "Montreal", "c"),
        ("Which planet is known as the Red Planet?", "Venus", "Mars", "Jupiter", "Saturn", "b"),
        ("What is the longest bone in the human body?", "Tibia", "Femur", "Humerus", "Radius", "b"),
        ("Who wrote Pride and Prejudice?", "Charlotte Bronte", "Jane Austen", "Emily Dickinson", "Virginia Woolf", "b"),
        ("What is the freezing point of water in Celsius?", "-1", "0", "1", "32", "b"),
        ("Which country gifted the Statue of Liberty to the USA?", "Britain", "France", "Spain", "Italy", "b"),
        ("What is the largest island in the world?", "Australia", "Greenland", "Madagascar", "Borneo", "b"),
        ("Who painted the ceiling of the Sistine Chapel?", "Leonardo", "Michelangelo", "Raphael", "Donatello", "b"),
        ("What is the most spoken language in the world?", "English", "Mandarin", "Spanish", "Hindi", "b"),
        ("Which organ produces insulin?", "Liver", "Pancreas", "Kidney", "Heart", "b"),
        ("What is the smallest prime number?", "0", "1", "2", "3", "c"),
        ("Who discovered penicillin?", "Pasteur", "Fleming", "Curie", "Darwin", "b")
    ]
    
    # Insert questions into source table
    for i, q in enumerate(questions):
        try:
            source_table.put_item(
                Item={
                    'id': str(i+1),
                    'question': q[0],
                    'option_a': q[1],
                    'option_b': q[2],
                    'option_c': q[3],
                    'option_d': q[4],
                    'correct_answer': q[5]
                },
                ConditionExpression='attribute_not_exists(id)'
            )
        except:
            pass  # Question already exists
    
    print(f"Inserted {len(questions)} questions into source table")
    return source_table

def copy_questions_to_game_table():
    """Copy questions from source table to game table"""
    region = os.getenv('AWS_REGION', 'us-west-2')
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    source_table = dynamodb.Table('trivia_questions_source')
    game_table = dynamodb.Table('trivia_questions')
    
    # Scan all questions from source
    response = source_table.scan()
    questions = response['Items']
    
    print(f"Found {len(questions)} questions in source table")
    
    # Clear existing questions in game table
    game_response = game_table.scan()
    for item in game_response['Items']:
        game_table.delete_item(Key={'id': item['id']})
    
    print("Cleared existing questions from game table")
    
    # Copy questions to game table
    for question in questions:
        game_table.put_item(Item=question)
    
    print(f"Copied {len(questions)} questions to game table")

if __name__ == "__main__":
    print("Setting up trivia questions...")
    
    # Create source table with questions
    create_questions_source_table()
    
    # Copy to game table
    copy_questions_to_game_table()
    
    print("Question setup complete!")
    print("The trivia game now has access to all questions from the source table.")