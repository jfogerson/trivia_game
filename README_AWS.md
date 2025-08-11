# AWS Database Setup for Trivia Game

The trivia game now supports both AWS RDS (PostgreSQL) and DynamoDB backends.

## Option 1: AWS RDS (PostgreSQL)

### Setup:
1. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

2. **Create RDS instance**:
   ```bash
   python3 setup_rds.py
   ```

3. **Set environment variables**:
   ```bash
   export RDS_HOST="your-rds-endpoint"
   export RDS_DB="trivia"
   export RDS_USER="trivia_admin"
   export RDS_PASSWORD="TriviaGame123!"
   export RDS_PORT="5432"
   ```

4. **Run the application**:
   ```bash
   python3 app.py
   ```

### RDS Benefits:
- SQL queries and relationships
- ACID compliance
- Familiar PostgreSQL syntax
- Better for complex queries

## Option 2: AWS DynamoDB

### Setup:
1. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

2. **Create DynamoDB tables**:
   ```bash
   python3 setup_dynamodb.py
   ```

3. **Set AWS region** (optional):
   ```bash
   export AWS_REGION="us-east-1"
   ```

4. **Run the DynamoDB version**:
   ```bash
   python3 app_dynamodb.py
   ```

### DynamoDB Benefits:
- Serverless and fully managed
- Auto-scaling
- Pay-per-request pricing
- Better for high-traffic scenarios

## AWS Permissions Required

### For RDS:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "rds:CreateDBInstance",
                "rds:DescribeDBInstances",
                "rds:ModifyDBInstance"
            ],
            "Resource": "*"
        }
    ]
}
```

### For DynamoDB:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:CreateTable",
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Scan",
                "dynamodb:Query",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem"
            ],
            "Resource": "*"
        }
    ]
}
```

## Cost Considerations

### RDS (db.t3.micro):
- ~$13/month for the instance
- Additional storage costs
- Good for development/testing

### DynamoDB:
- Pay-per-request pricing
- ~$1.25 per million requests
- Free tier: 25GB storage, 25 RCU/WCU
- More cost-effective for variable workloads

## Production Deployment

### RDS Production:
- Use larger instance types (db.t3.small+)
- Enable Multi-AZ for high availability
- Set up automated backups
- Use VPC security groups

### DynamoDB Production:
- Consider provisioned capacity for predictable workloads
- Enable point-in-time recovery
- Use DynamoDB Accelerator (DAX) for caching
- Set up CloudWatch monitoring

## Security Best Practices

1. **Use IAM roles** instead of access keys when possible
2. **Enable encryption** at rest and in transit
3. **Use VPC** for RDS instances
4. **Implement least privilege** access policies
5. **Rotate credentials** regularly
6. **Enable CloudTrail** for audit logging

## Monitoring

- **CloudWatch** for metrics and alarms
- **RDS Performance Insights** for database performance
- **DynamoDB Insights** for table performance
- **Application Load Balancer** for distributing traffic