# Deployment and Maintenance Guide

## Overview

This guide covers deployment strategies, infrastructure requirements, monitoring, and maintenance procedures for the Deep Research MCP system in production environments.

## Table of Contents

- [Infrastructure Requirements](#infrastructure-requirements)
- [Deployment Methods](#deployment-methods)
- [Production Configuration](#production-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Maintenance Procedures](#maintenance-procedures)
- [Scaling Strategies](#scaling-strategies)
- [Security Considerations](#security-considerations)

## Infrastructure Requirements

### Minimum System Requirements

#### Single Instance Deployment
- **CPU**: 2 cores minimum, 4 cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, 100GB recommended
- **Network**: Stable internet connection with 10Mbps+ bandwidth
- **OS**: Linux (Ubuntu 20.04+), macOS 11+, Windows 10+

#### Production Deployment
- **CPU**: 8 cores minimum, 16 cores recommended
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 500GB SSD minimum, 1TB NVMe recommended
- **Network**: High-speed internet with redundant connections
- **Load Balancer**: For multi-instance deployments

### Software Dependencies

#### Core Dependencies
```bash
# Python 3.11+
python3.11 -m pip install --upgrade pip

# System packages (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    git \
    curl \
    wget \
    build-essential

# Document generation (optional)
sudo apt-get install -y \
    pandoc \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-latex-extra
```

#### Container Requirements (Docker)
```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    pandoc \
    texlive-latex-base \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .

EXPOSE 8080
CMD ["python", "mcp_server.py"]
```

## Deployment Methods

### Method 1: Direct Deployment

#### Step 1: Environment Setup
```bash
# Clone repository
git clone https://github.com/your-org/deep-research-mcp.git
cd deep-research-mcp

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 2: Configuration
```bash
# Create production environment file
cp .env.example .env.production

# Edit configuration
nano .env.production
```

#### Step 3: Service Setup
```bash
# Create systemd service
sudo tee /etc/systemd/system/deep-research-mcp.service << EOF
[Unit]
Description=Deep Research MCP Server
After=network.target

[Service]
Type=simple
User=research
Group=research
WorkingDirectory=/opt/deep-research-mcp
Environment=PATH=/opt/deep-research-mcp/venv/bin
EnvironmentFile=/opt/deep-research-mcp/.env.production
ExecStart=/opt/deep-research-mcp/venv/bin/python mcp_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable deep-research-mcp
sudo systemctl start deep-research-mcp
```

### Method 2: Docker Deployment

#### Single Container
```bash
# Build image
docker build -t deep-research-mcp:latest .

# Run container
docker run -d \
  --name deep-research-mcp \
  --restart unless-stopped \
  -p 8080:8080 \
  -v $(pwd)/.env.production:/app/.env:ro \
  -v $(pwd)/data:/app/data \
  deep-research-mcp:latest
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  deep-research-mcp:
    build: .
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - ENV=production
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: research_mcp
      POSTGRES_USER: research
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - deep-research-mcp

volumes:
  redis_data:
  postgres_data:
```

### Method 3: Kubernetes Deployment

#### Namespace and ConfigMap
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: deep-research-mcp

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: deep-research-config
  namespace: deep-research-mcp
data:
  MAX_CONCURRENT_SECTIONS: "5"
  ENABLE_CACHING: "true"
  CACHE_TTL: "3600"
```

#### Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deep-research-mcp
  namespace: deep-research-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deep-research-mcp
  template:
    metadata:
      labels:
        app: deep-research-mcp
    spec:
      containers:
      - name: deep-research-mcp
        image: deep-research-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        envFrom:
        - configMapRef:
            name: deep-research-config
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
```

#### Service and Ingress
```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: deep-research-mcp-service
  namespace: deep-research-mcp
spec:
  selector:
    app: deep-research-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: deep-research-mcp-ingress
  namespace: deep-research-mcp
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - research.yourdomain.com
    secretName: deep-research-tls
  rules:
  - host: research.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: deep-research-mcp-service
            port:
              number: 80
```

### Method 4: Cloud Platform Deployment

#### AWS ECS
```json
{
  "family": "deep-research-mcp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "deep-research-mcp",
      "image": "your-account.dkr.ecr.region.amazonaws.com/deep-research-mcp:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/deep-research-mcp",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Run
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: deep-research-mcp
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containerConcurrency: 10
      containers:
      - image: gcr.io/your-project/deep-research-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-key
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
```

## Production Configuration

### Environment Variables
```bash
# .env.production
# Environment
ENV=production
DEBUG_MODE=false
LOG_LEVEL=INFO

# LLM Providers
OPENAI_API_KEY=sk-prod-your-key
GOOGLE_API_KEY=your-prod-key
PRIMARY_LLM_PROVIDER=openai
FALLBACK_LLM_PROVIDER=google_gemini

# Search Providers
TAVILY_API_KEY=tvly-prod-your-key
BRAVE_API_KEY=your-prod-key
PRIMARY_SEARCH_PROVIDER=tavily
FALLBACK_SEARCH_PROVIDER=brave

# Performance
MAX_CONCURRENT_SECTIONS=5
MAX_CONCURRENT_SEARCHES=10
REQUEST_TIMEOUT=60
ENABLE_CACHING=true
CACHE_TTL=3600

# Security
ENABLE_RATE_LIMITING=true
REQUESTS_PER_MINUTE=100
ENABLE_CONTENT_FILTER=true

# Monitoring
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
ENABLE_METRICS=true
```

### Nginx Configuration
```nginx
# nginx.conf
upstream deep_research_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;  # Additional instances
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name research.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name research.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    client_max_body_size 10M;
    
    location / {
        proxy_pass http://deep_research_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://deep_research_backend/health;
        access_log off;
    }
}
```

## Monitoring and Logging

### Health Checks

Add health check endpoints to `mcp_server.py`:

```python
@mcp.resource("text/plain")
def health():
    """Health check endpoint"""
    return "OK"

@mcp.resource("text/plain") 
def ready():
    """Readiness check endpoint"""
    # Check dependencies
    if check_api_connectivity():
        return "Ready"
    else:
        raise Exception("Not ready")
```

### Prometheus Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
research_requests_total = Counter('research_requests_total', 'Total research requests')
research_duration = Histogram('research_duration_seconds', 'Research duration')
active_research_tasks = Gauge('active_research_tasks', 'Active research tasks')
api_calls_total = Counter('api_calls_total', 'Total API calls', ['provider', 'model'])

def start_metrics_server(port=8090):
    start_http_server(port)
```

### Logging Configuration

```python
# logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger
```

### Log Aggregation (ELK Stack)

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  elasticsearch_data:
```

## Backup and Recovery

### Data Backup Strategy

#### Research Outputs
```bash
#!/bin/bash
# backup_outputs.sh

BACKUP_DIR="/backup/research-outputs"
SOURCE_DIR="/app/outputs"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
tar -czf "$BACKUP_DIR/outputs_$DATE.tar.gz" -C "$SOURCE_DIR" .

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/outputs_$DATE.tar.gz" s3://your-backup-bucket/outputs/

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "outputs_*.tar.gz" -mtime +30 -delete
```

#### Configuration Backup
```bash
#!/bin/bash
# backup_config.sh

BACKUP_DIR="/backup/config"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup configuration files
mkdir -p "$BACKUP_DIR/$DATE"
cp .env.production "$BACKUP_DIR/$DATE/"
cp multi_agents/task.json "$BACKUP_DIR/$DATE/"
cp -r multi_agents/config/ "$BACKUP_DIR/$DATE/config/"

# Create archive
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$BACKUP_DIR" "$DATE"
rm -rf "$BACKUP_DIR/$DATE"
```

### Database Backup (if using external DB)

```bash
#!/bin/bash
# backup_database.sh

DB_NAME="research_mcp"
BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Upload to cloud
aws s3 cp "$BACKUP_DIR/db_$DATE.sql.gz" s3://your-backup-bucket/database/
```

### Disaster Recovery Plan

#### Recovery Procedures
1. **Service Failure**: Restart service, check logs, failover to backup instance
2. **Data Corruption**: Restore from latest backup, verify data integrity
3. **Complete System Failure**: Deploy new instance, restore data and configuration
4. **API Provider Outage**: Switch to fallback providers automatically

#### Recovery Testing
```bash
#!/bin/bash
# test_recovery.sh

echo "Testing disaster recovery procedures..."

# Test backup restoration
./restore_from_backup.sh latest

# Test service startup
./start_services.sh

# Test API connectivity
./test_api_health.sh

# Test research functionality
python test_research_workflow.py

echo "Recovery test completed"
```

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks
```bash
#!/bin/bash
# daily_maintenance.sh

# Check service health
systemctl status deep-research-mcp

# Check disk usage
df -h /app/outputs

# Clean temporary files
find /app/temp -type f -mtime +1 -delete

# Check API usage
python scripts/check_api_usage.py

# Update metrics
python scripts/update_daily_metrics.py
```

#### Weekly Tasks
```bash
#!/bin/bash
# weekly_maintenance.sh

# Update dependencies
pip list --outdated

# Clean old outputs
find /app/outputs -type d -mtime +7 -exec rm -rf {} +

# Analyze performance metrics
python scripts/weekly_performance_report.py

# Test backup procedures
./test_backup_restore.sh

# Security scan
safety check
bandit -r multi_agents/
```

#### Monthly Tasks
```bash
#!/bin/bash
# monthly_maintenance.sh

# Security updates
apt update && apt upgrade -y

# Dependency updates
pip-review --auto

# Performance analysis
python scripts/monthly_performance_analysis.py

# Cost analysis
python scripts/cost_analysis.py

# Capacity planning
python scripts/capacity_planning.py
```

### Update Procedures

#### Application Updates
```bash
#!/bin/bash
# update_application.sh

# Backup current version
./backup_current_version.sh

# Pull latest code
git fetch origin
git checkout production
git pull origin production

# Update dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Restart service
sudo systemctl restart deep-research-mcp

# Verify deployment
./verify_deployment.sh
```

#### Rollback Procedure
```bash
#!/bin/bash
# rollback.sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "Usage: ./rollback.sh <version>"
    exit 1
fi

# Stop service
sudo systemctl stop deep-research-mcp

# Rollback code
git checkout "$VERSION"

# Restore dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl start deep-research-mcp

# Verify rollback
./verify_deployment.sh
```

## Scaling Strategies

### Horizontal Scaling

#### Load Balancer Configuration
```nginx
upstream deep_research_cluster {
    least_conn;
    server 10.0.1.10:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8080 weight=2 max_fails=3 fail_timeout=30s;
    server 10.0.1.13:8080 backup;
}
```

#### Auto-scaling (Kubernetes)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: deep-research-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deep-research-mcp
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

#### Resource Monitoring
```python
# resource_monitor.py
import psutil
import time

def monitor_resources():
    while True:
        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        if cpu_percent > 80:
            alert("High CPU usage", cpu_percent)
        
        if memory_info.percent > 85:
            alert("High memory usage", memory_info.percent)
            
        if disk_info.percent > 90:
            alert("High disk usage", disk_info.percent)
        
        time.sleep(60)
```

## Security Considerations

### Access Control

#### API Key Management
```python
# security/key_manager.py
import secrets
import hashlib
from cryptography.fernet import Fernet

class KeyManager:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
    
    def encrypt_key(self, api_key):
        return self.cipher.encrypt(api_key.encode())
    
    def decrypt_key(self, encrypted_key):
        return self.cipher.decrypt(encrypted_key).decode()
    
    def rotate_keys(self):
        # Implement key rotation logic
        pass
```

#### Rate Limiting
```python
# security/rate_limiter.py
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id):
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        self.requests[client_id].append(now)
        return True
```

### Network Security

#### Firewall Rules
```bash
# firewall_setup.sh
#!/bin/bash

# Basic firewall setup
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (change port as needed)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow application port (restrict to specific IPs if possible)
ufw allow from 10.0.0.0/8 to any port 8080

# Enable firewall
ufw --force enable
```

#### SSL/TLS Configuration
```bash
# ssl_setup.sh
#!/bin/bash

# Generate SSL certificate with Let's Encrypt
certbot certonly --nginx \
    --email admin@yourdomain.com \
    --agree-tos \
    --no-eff-email \
    -d research.yourdomain.com

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

This deployment guide provides comprehensive coverage of production deployment strategies, monitoring, and maintenance procedures. Choose the deployment method that best fits your infrastructure and requirements.