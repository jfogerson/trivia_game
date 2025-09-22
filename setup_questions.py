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
        ('What is widely considered to be the first horror movie made?', 'Nosferatu', 'Frankenstein',
         'The House of the Devil', 'Dr. Jekyll and Mr. Hyde', 'c')
        ('What is the name of Neve Campbell’s character in Scream?', 'Gale Weathers', 'Sidney Prescott', 'Tatum Riley',
         'Casey Becker', 'b')
        ('In Jeepers Creepers, the Creeper rises every how many years to feed?', '13 years', '30 years', '23 years',
         '50 years', 'c')
        ('What is the name of the summer camp where Friday the 13th takes place?', 'Camp Crystal Lake', 'Camp Redwood',
         'Camp Blood', 'Camp Silver Lake', 'a')
        ('What kind of allergy does Charlie have in Hereditary?', 'Shellfish allergy', 'Nut allergy', 'Gluten allergy',
         'Dairy allergy', 'b')
        ('What is the name of the possessed young girl in The Exorcist?', 'Linda', 'Emily', 'Regan', 'Sarah', 'c')
        ('In which state does The Blair Witch Project take place?', 'Virginia', 'Maryland', 'Pennsylvania', 'Ohio', 'b')
        ('Who plays Pennywise in 2017’s It?', 'Alexander Skarsgård', 'Bill Skarsgård', 'Gustaf Skarsgård',
         'Stellan Skarsgård', 'b')
        ('In The Ring, how long do people have to live after watching the video tape?', '3 days', '5 days', '7 days',
         '10 days', 'c')
        ('Who plays Chucky’s love interest, Tiffany, in Bride of Chucky?', 'Jennifer Tilly', 'Sarah Michelle Gellar',
         'Neve Campbell', 'Courteney Cox', 'a')
        ('Who directed acclaimed horror movies Get Out and Us?', 'Jordan Peele', 'James Wan', 'John Carpenter',
         'Ari Aster', 'a')
        ('What year was the first Saw movie released?', '2002', '2003', '2004', '2005', 'c')
        ('What is the name of the man Dr. Caligari controls in The Cabinet of Dr. Caligari?', 'Cesare', 'Hans', 'Karl',
         'Otto', 'a')
        ('Which horror movie stars Jennifer Love Hewitt, Freddie Prinze Jr., Sarah Michelle Gellar and Ryan Phillippe?',
         'Scream', 'I Know What You Did Last Summer', 'Urban Legend', 'Final Destination', 'b')
        ('In which city does Rosemary’s Baby take place?', 'Los Angeles', 'Chicago', 'New York City', 'Boston', 'c')
        ('There are two serial killers at the center of Silence of the Lambs. What are their names?',
         'Hannibal Lecter and Buffalo Bill', 'Hannibal Lecter and Norman Bates', 'Buffalo Bill and Michael Myers',
         'Norman Bates and Freddy Krueger', 'a')
        ('In Halloween, Michael Myers, as a child, kills his teenage sister. What was her name?', 'Laurie', 'Judith',
         'Annie', 'Linda', 'b')
        ('Which author of scary books holds the record for the most book-to-movie adaptations in the horror genre?',
         'Dean Koontz', 'Stephen King', 'Clive Barker', 'Anne Rice', 'b')
        ('What title is Dani crowned in Midsommar?', 'Sun Queen', 'Flower Maiden', 'May Queen', 'Harvest Queen', 'c')
        ('Passengers must survive what kind of outbreak in Train to Busan?', 'Vampire outbreak', 'Zombie outbreak',
         'Plague outbreak', 'Alien outbreak', 'b')
        ('What is the name of the hotel Jack Torrance is hired to care for in The Shining?', 'The Overlook Hotel',
         'The Stanley Hotel', 'The Timberline Hotel', 'The Grand Hotel', 'a')
        ('Who plays Freddy Krueger in A Nightmare on Elm Street?', 'Robert Englund', 'Jackie Earle Haley',
         'Doug Bradley', 'Tony Todd', 'a')
        ('What is the real name of “The Black Bride” in Insidious: Chapter 2?', 'Parker Crane', 'Elise Rainier',
         'Josh Lambert', 'Carl', 'a')
        ('What year was the original The Texas Chainsaw Massacre released?', '1972', '1973', '1974', '1975', 'c')
        ('Who plays Norman Bates in 1960’s Psycho?', 'Anthony Perkins', 'Vincent Price', 'Peter Cushing',
         'Christopher Lee', 'a')
        ('1922’s Nosferatu is an unofficial adaptation of which vampire book?', 'Dracula', 'Carmilla', 'The Vampyre',
         'Salems Lot', 'a')
        ('Which city were Alex and his classmates flying to when he had a disturbing premonition on the plane in Final Destination?',
         'London', 'Rome', 'Paris', 'Berlin', 'c')
        ('Who directed 1963’s The Birds?', 'Alfred Hitchcock', 'Stanley Kubrick', 'George Romero', 'John Carpenter',
         'a')
        ('The Witch takes place in what year?', '1620', '1630', '1640', '1650', 'b')
        ('What is the name of the killer in the Saw franchise?', 'Jigsaw', 'Puzzleman', 'The Engineer', 'The Architect',
         'a')
        ('Which horror movie isn’t based on a book?', 'Frankenstein', 'Bird Box', 'Interview with the Vampire',
         'A Quiet Place', 'd')
        ('What is the name of the spacecraft the crew is aboard in Alien?', 'The Nostromo', 'The Prometheus',
         'The Covenant', 'The Sulaco', 'a')
        ('In which city does 1992’s Candyman take place?', 'Detroit', 'Chicago', 'New Orleans', 'Baltimore', 'b')
        ('Which actor appears in The Purge, Sinister and The Black Phone?', 'Ethan Hawke', 'Patrick Wilson',
         'James McAvoy', 'Cillian Murphy', 'a')
        ('How many killers are there in The Strangers?', 'Two', 'Three', 'Four', 'Five', 'b')
        ('Who played Carrie in 1976’s Carrie?', 'Sissy Spacek', 'Jamie Lee Curtis', 'Linda Blair', 'Piper Laurie', 'a')
        ('Where does Noa meet Steve in Fresh?', 'The grocery store', 'A bar', 'A coffee shop', 'A dating app', 'a')
        ('What is the name of the pop-up book in The Babadook?', 'Mister Babadook', 'The Dark Book', 'The Shadow Man',
         'The Creeper', 'a')
        ('What year was Let the Right One In released?', '2006', '2007', '2008', '2009', 'c')
        ('Which actor and actress play Ed and Lorraine Warren in The Conjuring universe?',
         'Patrick Wilson and Vera Farmiga', 'Ethan Hawke and Toni Collette', 'James McAvoy and Jessica Chastain',
         'Ryan Gosling and Emily Blunt', 'a')
        ('The Losers Club reunites after how many years in It Chapter Two?', '17 years', '27 years', '37 years',
         '47 years', 'b')
        ('What is used to suppress the evil leprechaun’s powers in Leprechaun?', 'Silver', 'Garlic', 'Four-leaf clover',
         'Holy water', 'c')
        ('Which two slashers faced off in a 2003 movie?', 'Michael Myers and Jason Voorhees',
         'Freddy Krueger and Jason Voorhees', 'Freddy Krueger and Leatherface', 'Chucky and Freddy Krueger', 'b')
        ('In Insidious, what ability do Josh and Dalton share?', 'Telepathy', 'Time travel', 'Astral projection',
         'Mind control', 'c')
        ('What is the name of the child in The Omen?', 'Damien', 'David', 'Daniel', 'Derek', 'a')
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