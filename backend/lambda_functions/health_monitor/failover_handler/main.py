import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    rds = boto3.client('rds')
    sns = boto3.client('sns')
    
    db_cluster_id = os.environ['DB_CLUSTER_ID']
    
    try:
        # Perform failover
        response = rds.failover_db_cluster(
            DBClusterIdentifier=db_cluster_id,
            TargetDBInstanceIdentifier=os.environ['DB_READER_INSTANCE_ID']
        )
        
        # Update Route53 record if needed
        if 'ROUTE53_ZONE_ID' in os.environ and 'ROUTE53_RECORD' in os.environ:
            route53 = boto3.client('route53')
            new_endpoint = rds.describe_db_clusters(
                DBClusterIdentifier=db_cluster_id
            )['DBClusters'][0]['Endpoint']
            
            route53.change_resource_record_sets(
                HostedZoneId=os.environ['ROUTE53_ZONE_ID'],
                ChangeBatch={
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': os.environ['ROUTE53_RECORD'],
                            'Type': 'CNAME',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': new_endpoint}]
                        }
                    }]
                }
            )
        
        # Send success notification
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Database failover completed successfully at {datetime.now()}",
            Subject="Database Failover Completed"
        )
        
        return {
            'statusCode': 200,
            'body': f"Failover initiated at {datetime.now()}"
        }
    except Exception as e:
        # Send failure notification
        sns.publish(
            TopicArn=os.environ['SNS_TOPIC_ARN'],
            Message=f"Database failover failed at {datetime.now()}: {str(e)}",
            Subject="Database Failover Failed"
        )
        raise e