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
            ('Which EC2 option reduces long-term cost?' 'On-Demand' 'Capacity Reservation' 'Reserved Instance' 'Dedicated' 'c'),
            ('Which S3 storage class is cheapest?' 'Standard' 'IA' 'One Zone' 'Glacier' 'd'),
            ('Which S3 feature prevents deletion?' 'Lifecycle' 'Versioning' 'Replication' 'Events' 'b'),
            ('Which service manages VPCs?' 'CloudFront' 'VPC' 'IAM' 'EKS' 'b'),
            ('Which AWS service is a NAT instance replacement?' 'VPC Peering' 'NAT Gateway' 'Transit Gateway' 'Direct Connect' 'b'),
            ('Which service connects to on-premise resources?' 'VPN' 'Direct Connect' 'CloudFront' 'IAM' 'b'),
            ('Which service shares VPC subnets?' 'Transit Gateway' 'VPC Peering' 'NAT Gateway' 'CloudFront' 'a'),
            ('Which service enforces microsegmentation?' 'ACL' 'Security Group' 'Firewall Manager' 'WAF' 'c'),
            ('Which EC2 option provides GPUs?' 'C5' 'G4' 'M5' 'T3' 'b'),
            ('Which database is multi-master?' 'Aurora' 'RDS' 'Neptune' 'DynamoDB' 'd'),
            ('Which Aurora feature improves scaling?' 'Read Replicas' 'Multi-AZ' 'Global Database' 'Sharding' 'c'),
            ('Which service supports serverless SQL?' 'Athena' 'Redshift' 'RDS' 'Glue' 'a'),
            ('Which service automates ML labeling?' 'SageMaker' 'Ground Truth' 'Comprehend' 'Rekognition' 'b'),
            ('Which AI service translates text?' 'Comprehend' 'Lex' 'Translate' 'Polly' 'c'),
            ('Which AI service generates speech?' 'Lex' 'Comprehend' 'Transcribe' 'Polly' 'd'),
            ('Which AI service detects entities?' 'Lex' 'Comprehend' 'Rekognition' 'Polly' 'b'),
            ('Which service is managed Kafka?' 'Kinesis' 'MSK' 'SNS' 'SQS' 'b'),
            ('Which service is managed RabbitMQ?' 'MSK' 'MQ' 'Kinesis' 'SNS' 'b'),
            ('Which Kinesis type replays data?' 'Streams' 'Firehose' 'Analytics' 'Video' 'a'),
            ('Which service indexes logs?' 'CloudWatch' 'Elasticsearch' 'S3' 'Glue' 'b'),
            ('Which service provides log insights?' 'CloudTrail' 'Athena' 'CloudWatch Logs' 'Inspector' 'c'),
            ('Which service encrypts at scale?' 'IAM' 'Shield' 'KMS' 'Inspector' 'c'),
            ('Which service manages SSL certs?' 'WAF' 'ACM' 'Shield' 'CloudFront' 'b'),
            ('Which service provides DDoS protection?' 'WAF' 'GuardDuty' 'Shield' 'CloudTrail' 'c'),
            ('Which service runs Lambda inside VPC?' 'Lambda' 'VPC' 'EKS' 'Fargate' 'a'),
            ('Which service offers parallel clusters?' 'ECS' 'Batch' 'Glue' 'Step Functions' 'b'),
            ('Which orchestration manages workflows?' 'ECS' 'Step Functions' 'Lambda' 'Athena' 'b'),
            ('Which service queries petabytes fast?' 'Redshift' 'Athena' 'EMR' 'Glue' 'a'),
            ('Which service prepares ML data?' 'Glue' 'S3' 'EMR' 'EKS' 'a'),
            ('Which tool provides cost explorer?' 'Trusted Advisor' 'Budgets' 'Cost Explorer' 'Inspector' 'c'),
            ('Which tool gives savings plans?' 'Budgets' 'Pricing Calculator' 'Cost Explorer' 'Marketplace' 'b'),
            ('Which monitoring adds custom metrics?' 'CloudTrail' 'CloudWatch' 'Inspector' 'X-Ray' 'b'),
            ('Which service traces requests?' 'CloudWatch' 'X-Ray' 'Inspector' 'CloudTrail' 'b'),
            ('Which service supports chaos testing?' 'FIS' 'Inspector' 'X-Ray' 'Shield' 'a'),
            ('Which service manages blue/green?' 'Elastic Beanstalk' 'CodeDeploy' 'ECS' 'Lambda' 'b'),
            ('Which service is serverless CI/CD?' 'CodePipeline' 'CodeBuild' 'Amplify' 'CodeCommit' 'c'),
            ('Which service is Git repo?' 'CodeBuild' 'CodePipeline' 'CodeCommit' 'CodeStar' 'c'),
            ('Which service allows mobile backend?' 'Amplify' 'S3' 'Lambda' 'Glue' 'a'),
            ('Which service allows AR VR scenes?' 'Sumerian' 'Braket' 'Lex' 'Polly' 'a'),
            ('Which service supports quantum?' 'EKS' 'EC2' 'Braket' 'ECS' 'c'),
            ('Which service uses satellite links?' 'Outposts' 'Snowball' 'Ground Station' 'Direct Connect' 'c'),
            ('Which service runs containers at edge?' 'Lambda' 'Fargate' 'EKS Anywhere' 'Greengrass' 'd'),
            ('Which service builds digital twins?' 'IoT TwinMaker' 'Outposts' 'S3' 'Glue' 'a'),
            ('Which service secures accounts?' 'Inspector' 'Macie' 'Organizations' 'Shield' 'c'),
            ('Which service detects PII?' 'Macie' 'GuardDuty' 'Inspector' 'Shield' 'a'),
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