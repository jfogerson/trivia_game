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
        ("Which Azure service helps orchestrate workflows visually between services?", "Azure Logic Apps","Azure Functions", "Azure Automation", "Azure DevOps", "a"),
        ("Which Azure service is designed for identity and access management?", "Azure Active Directory","Azure Security Center", "Azure Monitor", "Azure Policy", "a"),
        ("Which Azure service balances network traffic between applications?", "Azure Load Balancer","Azure Application Gateway", "Azure Front Door", "Azure ExpressRoute", "a"),
        ("Which Azure service allows you to back up and restore workloads?", "Azure Backup", "Azure Site Recovery","Azure Storage Explorer", "Azure Key Vault", "a"),
        ("Which Azure service provides governance and compliance recommendations?", "Azure Advisor", "Azure Policy","Azure Monitor", "Azure Automation", "a"),
        ("Which Azure service provides cost management and budgeting tools?", "Azure Cost Management + Billing","Azure Advisor", "Azure Monitor", "Azure Policy", "a"),
        ("Which Azure service enables real-time event streaming and processing?", "Azure Event Hubs","Azure Logic Apps", "Azure Service Bus", "Azure Functions", "a"),
        ("Which Azure service provides centralized management for multiple subscriptions?", "Azure Management Groups","Azure Resource Manager", "Azure Policy", "Azure Monitor", "a"),
        ("Which Azure service provides scalable, distributed NoSQL database capabilities?", "Azure Cosmos DB","Azure SQL Database", "Azure Synapse Analytics", "Azure Blob Storage", "a"),
        ("Which Azure service lets you run Windows 10/11 desktops in the cloud?", "Azure Virtual Desktop","Azure Kubernetes Service", "Azure App Service", "Azure Virtual Machines", "a"),
        ("Which Azure service delivers content globally with low latency?", "Azure Content Delivery Network","Azure Front Door", "Azure Traffic Manager", "Azure Load Balancer", "a"),
        ("Which Azure service is used to host and scale containerized applications?", "Azure App Service","Azure Kubernetes Service", "Azure Virtual Machines", "Azure Logic Apps", "b"),
        ("Which Azure service provides analytics for security and threat detection?", "Azure Policy","Microsoft Sentinel", "Azure Advisor", "Azure Defender", "b"),
        ("Which Azure service provides a scalable, managed Apache Spark platform?", "Azure Functions","Azure Databricks", "Azure DevOps", "Azure Logic Apps", "b"),
        ("Which Azure service allows integration and automation between cloud and on-prem systems?", "Azure Event Grid","Azure Logic Apps", "Azure Service Bus", "Azure Functions", "b"),
        ("Which Azure service helps secure cloud resources with policies and compliance rules?", "Azure Automation","Azure Policy", "Azure Firewall", "Azure Load Balancer", "b"),
        ("Which Azure service provides prebuilt AI models for vision, speech, and language?", "Azure OpenAI Service","Azure Cognitive Services", "Azure Bot Service", "Azure HDInsight", "b"),
        ("Which Azure service provides centralized key and secret management?", "Azure App Service", "Azure Key Vault","Azure Databricks", "Azure Monitor", "b"),
        ("Which Azure service enables disaster recovery for virtual machines?", "Azure Backup", "Azure Site Recovery","Azure Sentinel", "Azure Automation", "b"),
        ("Which Azure service helps monitor applications and infrastructure in real time?", "Azure Log Analytics","Azure Monitor", "Azure Defender", "Azure Policy", "b"),
        ("Which Azure service allows you to move data between on-prem and cloud efficiently?", "Azure ExpressRoute","Azure Data Box", "Azure HDInsight", "Azure Event Hubs", "b"),
        ("Which Azure service provides hybrid cloud management for on-prem resources?", "Azure Policy", "Azure Arc","Azure Lighthouse", "Azure Bastion", "b"),
        ("Which Azure service allows you to deploy infrastructure using templates?", "Azure Key Vault","Azure Firewall", "Azure Resource Manager", "Azure Synapse Analytics", "c"),
        ("Which Azure service provides cloud-based version control and CI/CD pipelines?", "Azure Automation","Azure Key Vault", "Azure DevOps", "Azure Policy", "c"),
        ("Which Azure service provides serverless compute for event-driven code?", "Azure Automation","Azure Kubernetes Service", "Azure Logic Apps", "Azure Functions", "c"),
        ("Which Azure service provides a platform for big data analytics and data warehousing?", "Azure Data Factory","Azure Databricks", "Azure Synapse Analytics", "Azure App Service", "c"),
        ("Which Azure service enables conversational bots using AI?", "Azure Cognitive Services", "Azure HDInsight","Azure Bot Service", "Azure Databricks", "c"),
        ("Which Azure service provides message queuing for distributed applications?", "Azure App Service","Azure Blob Storage", "Azure Service Bus", "Azure Policy", "c"),
        ("Which Azure service allows you to store unstructured data such as images and documents?", "Azure Cosmos DB","Azure Data Factory", "Azure Blob Storage", "Azure Policy", "c"),
        ("Which Azure service offers hybrid identity synchronization?", "Azure Arc", "Azure AD B2C", "Azure AD Connect","Azure Policy", "c"),
        ("Which Azure service provides AI and ML model training capabilities?", "Azure App Configuration","Azure Cognitive Services", "Azure Machine Learning", "Azure Bot Service", "c"),
        ("Which Azure service provides distributed caching to improve performance?", "Azure SQL Database","Azure Blob Storage", "Azure Cache for Redis", "Azure Functions", "c"),
        ("Which Azure service hosts and manages relational databases?", "Azure Databricks", "Azure Blob Storage","Azure SQL Database", "Azure Cosmos DB", "c"),
        ("Which Azure service enables private connections between on-prem and Azure?", "Azure Bastion","Azure Private Link", "Azure ExpressRoute", "Azure VPN Gateway", "d"),
        ("Which Azure service helps centralize configuration for distributed applications?", "Azure Automation","Azure Key Vault", "Azure DevOps", "Azure App Configuration", "d"),
        ("Which Azure service provides AI-powered search across datasets?", "Azure Data Factory", "Azure HDInsight","Azure Machine Learning", "Azure Cognitive Search", "d"),
        ("Which Azure service helps you manage secrets in CI/CD pipelines?", "Azure Logic Apps", "Azure DevOps Repos","Azure Policy", "Azure Key Vault", "d"),
        ("Which Azure service allows external partners to manage your resources securely?", "Azure Arc", "Azure Policy","Azure Automation", "Azure Lighthouse", "d"),
        ("Which Azure service provides automated remediation and compliance enforcement?", "Azure Policy","Azure Monitor", "Azure Advisor", "Azure Automation", "d"),
        ("Which Azure service allows running virtual machines in the cloud?", "Azure Functions", "Azure Logic Apps","Azure Kubernetes Service", "Azure Virtual Machines", "d"),
        ("Which Azure service manages APIs and provides analytics and security?", "Azure Load Balancer","Azure Application Gateway", "Azure Front Door", "Azure API Management", "d"),
        ("Which Azure service delivers real-time user behavior insights?", "Azure Log Analytics", "Azure Policy","Azure App Service", "Azure Application Insights", "d"),
        ("Which Azure service enables users to create and manage virtual networks?", "Azure Policy", "Azure Firewall","Azure Load Balancer", "Azure Virtual Network", "d"),
        ("Which Azure service provides pre-deployment recommendations for performance and cost?", "Azure Firewall","Azure Policy", "Azure Automation", "Azure Advisor", "d"),
        ("Which Azure service delivers high-performance, low-latency private connectivity?", "Azure Firewall","Azure Policy", "Azure Bastion", "Azure ExpressRoute", "d")		]
    
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