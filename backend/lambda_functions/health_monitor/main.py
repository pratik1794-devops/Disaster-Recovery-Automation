import boto3
import psycopg2
import os
from datetime import datetime

def lambda_handler(event, context):
    db_endpoint = os.environ['DB_ENDPOINT']
    db_reader_endpoint = os.environ['DB_READER_ENDPOINT']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    
    cloudwatch = boto3.client('cloudwatch')
    sns = boto3.client('sns')
    
    try:
        # Check primary database
        conn = psycopg2.connect(
            host=db_endpoint,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        primary_status = "healthy"
        conn.close()
    except Exception as e:
        primary_status = "unhealthy"
        # Publish custom metric to trigger failover
        cloudwatch.put_metric_data(
            Namespace='Custom',
            MetricData=[{
                'MetricName': 'DatabaseFailoverTriggered',
                'Value': 1,
                'Unit': 'Count'
            }]
        )
        # Send notification
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Primary database failure detected at {datetime.now()}. Failover initiated.",
            Subject="Database Failover Triggered"
        )
    
    # Check reader database
    try:
        conn = psycopg2.connect(
            host=db_reader_endpoint,
            database=db_name,
            user=db_user,
            password=db_password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        reader_status = "healthy"
        conn.close()
    except Exception as e:
        reader_status = "unhealthy"
    
    return {
        'statusCode': 200,
        'body': {
            'primary_status': primary_status,
            'reader_status': reader_status,
            'timestamp': str(datetime.now())
        }
    }