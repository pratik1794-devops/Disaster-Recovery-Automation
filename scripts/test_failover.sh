#!/bin/bash

# Simulate database failure
aws rds stop-db-instance --db-instance-identifier your-primary-db-instance

# Monitor CloudWatch for failover trigger
echo "Monitoring for failover..."
while true; do
    status=$(aws rds describe-db-instances --db-instance-identifier your-primary-db-instance --query 'DBInstances[0].DBInstanceStatus' --output text)
    if [ "$status" == "stopped" ]; then
        echo "Primary database stopped. Waiting for failover..."
        sleep 10
    else
        echo "Failover detected! New status: $status"
        break
    fi
done

# Verify new primary
new_primary=$(aws rds describe-db-clusters --db-cluster-identifier your-db-cluster --query 'DBClusters[0].Endpoint' --output text)
echo "New primary endpoint: $new_primary"