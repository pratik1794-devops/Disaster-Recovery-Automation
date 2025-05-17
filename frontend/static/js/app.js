document.addEventListener('DOMContentLoaded', function() {
    const statusElement = document.getElementById('cluster-status');
    const manualFailoverBtn = document.getElementById('manualFailover');
    const testRecoveryBtn = document.getElementById('testRecovery');
    let failoverChart;
    
    // Initialize chart
    function initChart() {
        const ctx = document.getElementById('failoverChart').getContext('2d');
        failoverChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Failover Events',
                    data: [],
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    // Fetch and update status
    function updateStatus() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                // Update cluster status
                statusElement.innerHTML = data.clusters.map(cluster => `
                    <div class="status-card ${cluster.status === 'available' ? 'healthy' : 'unhealthy'}">
                        <h3>${cluster.identifier}</h3>
                        <p>Status: <strong>${cluster.status}</strong></p>
                        <p>Endpoint: ${cluster.endpoint}</p>
                        <p>Reader Endpoint: ${cluster.readerEndpoint}</p>
                        <p>Multi-AZ: ${cluster.multiAZ ? 'Yes' : 'No'}</p>
                    </div>
                `).join('');
                
                // Update chart
                if (data.metrics && data.metrics.length > 0) {
                    const metricData = data.metrics[0];
                    failoverChart.data.labels = metricData.Timestamps.map(t => new Date(t).toLocaleTimeString());
                    failoverChart.data.datasets[0].data = metricData.Values;
                    failoverChart.update();
                }
            })
            .catch(error => console.error('Error fetching status:', error));
    }
    
    // Manual failover
    manualFailoverBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to initiate a manual failover?')) {
            fetch('/api/failover', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'Failover initiated');
                    updateStatus();
                })
                .catch(error => alert('Error initiating failover: ' + error));
        }
    });
    
    // Test recovery
    testRecoveryBtn.addEventListener('click', function() {
        fetch('/api/test-recovery', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                alert(data.message || 'Recovery test initiated');
            })
            .catch(error => alert('Error testing recovery: ' + error));
    });
    
    // Initialize and start polling
    initChart();
    updateStatus();
    setInterval(updateStatus, 30000); // Update every 30 seconds
});