# Deep Research MCP - Deployment Guide

This guide provides comprehensive instructions for deploying the Deep Research MCP server in various environments with one-click deployment capabilities.

## Table of Contents

- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [One-Click Deployments](#one-click-deployments)
- [Production Deployment](#production-deployment)
- [Cloud Deployments](#cloud-deployments)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Quick Start

The fastest way to get started is using the one-click deployment script:

```bash
# Clone and setup
git clone <repository-url>
cd deep-research-mcp-og

# One-click Docker deployment
./deploy.sh docker

# Or one-click local deployment
./deploy.sh local
```

## Deployment Options

### 1. Docker Deployment (Recommended)
- ✅ Production-ready with Docker Compose
- ✅ Includes Redis, Nginx, monitoring
- ✅ Automatic scaling and health checks
- ✅ One-click deployment

### 2. Local Development
- ✅ Python virtual environment
- ✅ Development tools included
- ✅ Hot reloading support
- ✅ Ideal for development

### 3. Cloud Deployment
- ✅ AWS Lambda (serverless)
- ✅ Google Cloud Platform
- ✅ Azure Functions
- ✅ Auto-scaling included

### 4. Archive Deployment
- ✅ Self-contained deployment package
- ✅ Portable across environments
- ✅ Minimal dependencies
- ✅ Perfect for air-gapped environments

## Prerequisites

### System Requirements

- **Python**: 3.13+ (required)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space for outputs and caching
- **Network**: Internet access for AI APIs and search providers

### For Docker Deployment

- **Docker**: 20.10+ with Docker Compose
- **System Memory**: 8GB+ recommended for full stack

### For Cloud Deployment

- **AWS CLI** (for AWS deployments)
- **gcloud CLI** (for GCP deployments)
- **Azure CLI** (for Azure deployments)

## Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.example .env
# or for production
cp .env.production .env
```

### 2. Configure API Keys

Edit `.env` with your API keys:

```bash
# Primary LLM Provider
PRIMARY_LLM_PROVIDER=google_gemini
GOOGLE_API_KEY=your_google_api_key_here

# Primary Search Provider  
PRIMARY_SEARCH_PROVIDER=brave
BRAVE_API_KEY=your_brave_api_key_here

# Fallback Providers (recommended for production)
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3. Configure Language and Features

```bash
# Research language (for final output translation)
RESEARCH_LANGUAGE=en

# Provider strategies
LLM_STRATEGY=fallback_on_error
SEARCH_STRATEGY=fallback_on_error

# Performance settings
PROVIDER_TIMEOUT=60
PROVIDER_MAX_RETRIES=5
ENABLE_CACHING=true
```

## One-Click Deployments

### Docker Deployment

```bash
# Full production setup with monitoring
./deploy.sh docker --env prod

# Development setup
./deploy.sh docker --env dev

# With verbose logging
./deploy.sh docker --env prod --verbose

# Dry run (see what would happen)
./deploy.sh docker --dry-run
```

**What it does:**
- Builds optimized Docker images
- Sets up Redis for caching
- Configures Nginx load balancer
- Starts Prometheus monitoring
- Sets up health checks
- Configures log rotation

### Local Python Deployment

```bash
# Production local setup
./deploy.sh local --env prod

# Development setup with hot reload
./deploy.sh dev

# Skip dependency checks (if already installed)
./deploy.sh local --no-deps
```

**What it does:**
- Creates Python virtual environment with uv
- Installs production dependencies
- Creates systemd service file
- Sets up log rotation
- Configures directory structure

### Cloud Deployment

```bash
# AWS Lambda deployment
./deploy.sh cloud --config deploy/aws/config.env

# Force deployment without prompts
./deploy.sh cloud --force

# Custom configuration file
./deploy.sh cloud --config my-cloud-config.env
```

**What it does:**
- Detects cloud platform (AWS/GCP/Azure)
- Creates cloud-specific configuration
- Deploys serverless functions
- Sets up API Gateway/Load Balancer
- Configures auto-scaling
- Sets up monitoring and alerts

## Production Deployment

### Docker Production Stack

The Docker deployment includes a full production stack:

```yaml
# Services included:
- deep-research-mcp: Main application server
- redis: Caching and session management  
- nginx: Load balancer and reverse proxy
- prometheus: Metrics collection
- grafana: Monitoring dashboards
```

#### Production Features

- **Auto-scaling**: Automatic container scaling based on load
- **Health Checks**: Comprehensive health monitoring
- **Security**: Non-root containers, security headers
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Backup**: Automatic data backup and retention
- **SSL/TLS**: Ready for SSL certificate integration

#### Starting Production Stack

```bash
# Start with all production features
./deploy.sh docker --env prod

# Check status
./deploy.sh health

# View logs
./deploy.sh logs

# Stop all services
./deploy.sh stop
```

### Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| MCP Server | 2 cores | 4GB | 2GB |
| Redis | 0.5 cores | 512MB | 1GB |
| Nginx | 0.5 cores | 256MB | 100MB |
| Prometheus | 1 core | 1GB | 5GB |
| Total | 4 cores | 5.75GB | 8GB |

## Cloud Deployments

### AWS Lambda Deployment

**Architecture:**
- Lambda functions for MCP server
- API Gateway for HTTP routing
- DynamoDB for metadata storage
- S3 for research outputs
- SQS for background processing
- CloudWatch for monitoring

**Deployment:**

```bash
# Install Serverless Framework
npm install -g serverless

# Deploy to AWS
cd deploy/aws
serverless deploy --stage prod

# Monitor deployment
serverless logs -f mcp-server -t
```

**Benefits:**
- ✅ Auto-scaling to zero
- ✅ Pay per request
- ✅ Built-in monitoring
- ✅ High availability

### Google Cloud Platform

**Architecture:**
- Cloud Functions for MCP server
- Cloud Load Balancer
- Cloud Storage for outputs
- Cloud Monitoring

**Deployment:**

```bash
# Deploy to GCP
gcloud functions deploy deep-research-mcp \
    --runtime python313 \
    --trigger-http \
    --allow-unauthenticated
```

### Manual Cloud Setup

If you prefer manual setup or need custom configuration:

1. **Create cloud resources** (storage, databases, etc.)
2. **Configure environment variables** in cloud console
3. **Deploy application code** using cloud-specific tools
4. **Set up monitoring and alerts**
5. **Configure auto-scaling policies**

## Monitoring and Maintenance

### Health Checks

The deployment includes comprehensive health checking:

```bash
# Manual health check
./deploy.sh health

# Check specific components
curl http://localhost:8000/health
curl http://localhost:8000/system-info
```

### Monitoring Stack

**Prometheus Metrics:**
- Request rates and response times
- Error rates and success rates
- Resource usage (CPU, memory, disk)
- AI API usage and costs
- Queue lengths and processing times

**Grafana Dashboards:**
- System overview dashboard
- Application performance dashboard
- Cost tracking dashboard
- Alert status dashboard

**Accessing Monitoring:**
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)

### Log Management

**Log Locations:**
- Docker: `docker-compose logs -f`
- Local: `./logs/mcp_server.log`
- Cloud: Platform-specific logging service

**Log Rotation:**
- Automatic rotation at 100MB
- 10 backup files retained
- Compressed archives for space efficiency

### Backup and Recovery

```bash
# Create backup
./deploy.sh backup

# Backup includes:
# - Configuration files (.env, docker-compose.yml)
# - Data directories (outputs, logs)
# - Database dumps (if applicable)

# Restore from backup
./deploy.sh restore --backup backups/backup-20240830-143022
```

## Security Considerations

### API Keys and Secrets

- ✅ Never commit API keys to version control
- ✅ Use environment variables for all secrets
- ✅ Rotate API keys regularly
- ✅ Monitor API usage for anomalies

### Network Security

- ✅ Use HTTPS in production
- ✅ Configure CORS properly
- ✅ Implement rate limiting
- ✅ Use firewalls for cloud deployments

### Container Security

- ✅ Non-root user in containers
- ✅ Read-only filesystems where possible
- ✅ Security scanning of images
- ✅ Regular security updates

### Production Checklist

- [ ] API keys configured and secured
- [ ] SSL certificates installed
- [ ] Monitoring and alerting active
- [ ] Backup procedures tested
- [ ] Rate limiting configured
- [ ] Log rotation configured
- [ ] Security headers enabled
- [ ] Health checks passing
- [ ] Documentation updated
- [ ] Team training completed

## Troubleshooting

### Common Issues

**1. API Key Issues**
```bash
# Check configuration
./deploy.sh --config

# Test specific provider
python -c "from multi_agents.providers import test_provider; test_provider('google_gemini')"
```

**2. Memory Issues**
```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
```

**3. Network Connectivity**
```bash
# Test external API access
curl -I https://api.openai.com/v1/models
curl -I https://search.brave.com/api/v1/web/search
```

**4. Port Conflicts**
```bash
# Check port usage
lsof -i :8000

# Use different ports in .env
MCP_PORT=8001
```

### Getting Help

1. **Check logs**: Always start with log analysis
2. **Health checks**: Use built-in health endpoints
3. **Monitoring**: Check Grafana dashboards for insights
4. **Community**: GitHub issues and discussions
5. **Documentation**: Comprehensive docs available

### Performance Optimization

**For High Load:**
- Increase container resources
- Enable Redis caching
- Use CDN for static content
- Implement request queuing

**For Cost Optimization:**
- Use appropriate instance sizes
- Enable auto-scaling
- Monitor API usage costs
- Implement request caching

## Deployment Commands Reference

### Setup Commands
```bash
./deploy.sh setup                    # Initial setup
./deploy.sh setup --verbose         # Setup with debug output
```

### Deployment Commands
```bash
./deploy.sh docker                  # Docker deployment
./deploy.sh local                   # Local deployment  
./deploy.sh cloud                   # Cloud deployment
./deploy.sh dev                     # Development mode
```

### Management Commands
```bash
./deploy.sh stop                    # Stop all services
./deploy.sh clean                   # Clean up artifacts
./deploy.sh health                  # Health check
./deploy.sh logs                    # View logs
./deploy.sh backup                  # Create backup
```

### Options
```bash
--env ENV                           # Environment (dev/staging/prod)
--config FILE                       # Custom config file
--no-deps                           # Skip dependencies
--force                             # No confirmation prompts
--verbose                           # Verbose output
--dry-run                           # Show actions without executing
```

---

For more detailed information, see the individual configuration files and the [main documentation](README.md).