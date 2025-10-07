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
        ('What does AI stand for?', 'Artificial Intelligence', 'Artifical Intelligence', 'Artificiial Intelligence','Artificial Intellligence', 'a'),
        ('Which neural network type is best for sequence data?', 'CNN', 'RNN', 'GAN', 'SVM', 'b'),
        ('What does AI enable machines to do?' 'Play games', 'Send emails', 'Store data', 'Solve problems', 'd'),
        ('Who introduced the concept of AI?', 'Alan Turing', 'Marvin Minsky', 'John McCarthy', 'Geoffrey Hinton', 'a'),
        ('What year did IBM’s Deep Blue beat Kasparov?', '1987', '1990', '1997', '2000', 'c'),
        ('What is the main focus of AI?', 'Automation', 'Human-like tasks', 'Networking' 'Security', 'b'),
        ('What does ML stand for?', 'Managed Logic', 'Machine Learning', 'Modern Language', 'Matrix Lab', 'b'),
        ('What do deep learning models use?', 'Neural Networks', 'SQL Databases', 'Static Rules', 'Flat Files', 'a'),
        ('Which field uses NLP?', 'Voice Control', 'Image Editing', 'Data Mining', 'File Transfer', 'a'),
        ('Which AWS service supports ML?', 'SageMaker', 'Textract', 'Bedrock', 'CloudTrail', 'a'),
        ('What does Amazon Textract do?', 'Analyze Audio', 'Extract Text', 'Generate Images', 'Host Servers', 'b'),
        ('What is generative AI known for?', 'Data Storage', 'New Content', 'Network Security', 'User Login', 'b'),
        ('What is the foundation of AI architecture?', 'Models', 'Data', 'Applications', 'Security', 'b'),
        ('What is the third layer of AI architecture?', 'Data', 'Model', 'Application', 'Security', 'c'),
        ('Which model won ImageNet in 2012?', 'VGGNet', 'ResNet', 'AlexNet', 'BERT', 'c'),
        ('Which AWS chip powers deep learning?', 'Inferentia', 'Trainium', 'Graviton', 'Nitro', 'b'),
        ('What does Responsible AI ensure?', 'Fairness', 'Speed', 'Profit', 'Marketing', 'a'),
        ('What does AI aim to imitate?', 'Machines', 'Humans', 'Animals', 'Objects', 'b'),
        ('What type of data does deep learning handle best?', 'Unstructured', 'Numeric', 'Categorical', 'Binary', 'a'),
        ('Who is the CEO of Amazon?', 'Elon Musk', 'Andy Jassy', 'Jeff Bezos', 'Satya Nadella', 'b'),
        ('What framework guides AI adoption on AWS?', 'Well-Architected', 'CAF-AI', 'Control Tower', 'SageMaker', 'b'),
        ('What is CAF-AI built upon?', 'ML Models', 'Cloud Adoption Framework', 'AI Hardware', 'Data Lakes', 'b'),
        ('What is the main goal of CAF-AI?', 'Replace CAF', 'Guide AI Journey', 'Build Models', 'Train Data', 'b'),
        ('What does CAF-AI help organizations assess?', 'Data Size', 'AI Maturity', 'Costs', 'Storage', 'b'),
        ('What does the AWS Well-Architected Framework evaluate?', 'Code Quality', 'Architectural Best Practices','UI Design', 'Data Volume', 'b'),
        ('How many pillars are in the Well-Architected Framework?', 'Four', 'Five', 'Six', 'Seven', 'c'),
        ('Which AWS tool helps review workloads?', 'AI Builder', 'Well-Architected Tool', 'SageMaker', 'Textract', 'b'),
        ('What is the focus of the ML Lens?', 'Model Creation', 'ML Architecture', 'AI Ethics', 'Cost Saving', 'b'),
        ('What is a foundational element of CAF-AI?', 'Capabilities', 'Products', 'Scripts', 'Instances', 'a'),
        ('What does CAF-AI aim to accelerate?', 'AI Adoption', 'Cloud Costs', 'User Access', 'Data Storage', 'a'),
        ('A company wants to record API calls that are made to Amazon Bedrock in log files. For compliance purposes, the company wants these logs to include the API call, the user who made the call, and the time that the call was made.  Which AWS service will meet these requirements?',        'Inspector', 'CloudWatch', 'Trusted Advisor', 'CloudTrail ', 'd'),
        ('Which AWS service can the company use to secure access to Amazon Bedrock?', 'Amazon Macie', 'Rekognition','Identity and Access Management (IAM)', 'Config', 'c'),
        ('Which AWS service can detect text and handwriting from invoices that are stored in PNG format?', 'Polly','Textract', 'Kendra', 'Comprehend', 'b'),
        ('A data scientist notices that a model has high accuracy on training data, but has low accuracy on testing data. What is causing these results?','Not enough training time', 'Underfitting', 'Too much training data', 'Overfitting', 'd'),
        ('A company wants to use an open source foundation model (FM) to evaluate if contracts adhere to compliance rules.','Which AWS service will meet these requirements?', 'SageMaker JumpStart', 'Textract', 'Kendra', 'Q Business','a'),
        ('What is a foundation model (FM) in the context of generative AI?','A task-specific model that is trained on a narrow domain, such as finance or medicine, to serve as a foundation in that area.','A large, general-purpose model that is pre-trained on diverse datasets that can be fine-tuned for downstream tasks.','A theoretical framework to understand how different types of models learn representations.','A basic architecture that serves as a starting point to design more complex neural networks.', 'b'),
        ('A travel company wants to use a pre-trained generative AI model to generate background images for marketing materials. The company does not have ML expertise. Additionally, the company does not want to customize and host the ML model.  Which AWS service will meet these requirements?',      'Bedrock', 'Comprehend', 'Rekognition', 'Personalize', 'a'),
        ('A company wants to use generative AI to create product descriptions on its website.  What is a limitation of generative AI that the company should be aware of?','Generative AI models might produce biased or inappropriate content that requires human review and editing.','Generative AI cannot handle the large volumes of data that is required for product descriptions.','Generative AI cannot generate text in the multiple languages that is required for an ecommerce website.','Generative AI models lack the ability to understand and incorporate product specifications and details.', 'a'),
        ('A company wants to increase the consistency and quality of large language model (LLM) responses by providing the model with access to external sources of knowledge. Which technique will meet the requirement with the LEAST development effort?','Report Content Errors', 'Fine-tuning', 'Retrieval augmented generation (RAG)', 'In-context learning', 'Continued pre-training', 'a'),
        ('A company uses Amazon SageMaker AI for its ML models. The company wants to implement a solution for model owners to create a record of model information. The model information should include intended uses, risk ratings, training details, and evaluation results.',        'Which SageMaker AI feature will meet these requirements?', 'SageMaker Role Manager', 'SageMaker Model Cards','SageMaker Model Dashboard', 'SageMaker Model Monitor', 'c'),
        ('What is a valid data format for instruction-based fine-tuning?', 'Images that are labeled with categories','Playlists that are curated with recommended music', 'Prompt-response text pairs','Audio files with transcriptions', 'c'),
        ('A marketing company wants to generate personalized product descriptions for an ecommerce client website.The product descriptions must align with the unique style and tone of the existing website.Which prompt engineering technique will meet these requirements with the LEAST operational effort?','Few-shot prompting with examples of well-written product descriptions','Zero-shot prompting without any examples','Fine-tuning to optimize the descriptions based on customer engagement metrics','Continued pre-training on a different domain','a'),
        ('A company wants to gain insights from diverse data sources to improve business operations. The data sources include audio from call centers.', 'Which solution will improve transcription accuracy for domain-specific speech?', 'Use a custom bot in Amazon Lex.', 'Use a custom language model in Amazon Translate.', 'Use batch language identification in Amazon Transcribe.', 'Use a custom language model in Amazon Transcribe.', 'd'),
        ('A company wants to assess the performance of a foundation model (FM) for text generation. Which technique or metric will meet these requirements?','Reinforcement learning', 'F1 score', 'Recall-Oriented Understudy for Gisting Evaluation (ROUGE)','Fine-tuning', 'c'),
        ('A company has a containerized frontend application for its AI application. The company must implement a solution to assess its AWS environment security posture.The solution must identify potential security vulnerabilities across Amazon EC2 instances and Amazon Elastic Container Registry (Amazon ECR) repositories for the application.The solution should provide recommendations for remediation.Which AWS service will meet these requirements?','AWS CloudTrail','AWS Config','Amazon Inspector','AWS Artifact','c')
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