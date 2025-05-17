from flask import Flask, render_template, jsonify
import boto3
from datetime import datetime

app = Flask(__name__)

# AWS Clients
cloudwatch = boto3.client('cloudwatch')
rds = boto3.client('rds')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    # Get metrics from CloudWatch
    response = cloudwatch.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'failover_metric',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'Custom',
                        'MetricName': 'DatabaseFailoverTriggered'
                    },
                    'Period': 3600,
                    'Stat': 'Sum'
                },
                'ReturnData': True
            }
        ],
        StartTime=datetime.utcnow() - timedelta(hours=24),
        EndTime=datetime.utcnow()
    )
    
    # Get RDS cluster status
    clusters = rds.describe_db_clusters()
    cluster_status = []
    
    for cluster in clusters['DBClusters']:
        cluster_status.append({
            'identifier': cluster['DBClusterIdentifier'],
            'status': cluster['Status'],
            'endpoint': cluster['Endpoint'],
            'readerEndpoint': cluster.get('ReaderEndpoint', 'N/A'),
            'multiAZ': cluster['MultiAZ']
        })
    
    return jsonify({
        'metrics': response['MetricDataResults'],
        'clusters': cluster_status,
        'lastUpdated': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True)