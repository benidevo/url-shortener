# URL Shortener with Analytics

A production-ready distributed URL shortening system with geographic analytics, built using microservices architecture, FastAPI, and Kubernetes.

## 🏗️ Architecture

![Architecture Diagram](architecture.png)

### Core Components

- **Shortener Service**: FastAPI service for URL shortening and redirection
- **Analytics Service**: gRPC-enabled service for usage analytics and geographic tracking
- **PostgreSQL**: Persistent storage with separate databases per service
- **Redis**: Caching layer for improved performance

### Key Features

✅ **Production-Ready Kubernetes Deployment**

- Security hardening (RBAC, Network Policies, Pod Security)
- Auto-scaling with Horizontal Pod Autoscaler
- High availability with Pod Disruption Budgets
- Health probes and rolling updates

✅ **Microservices Architecture**

- Independent scaling and deployment
- gRPC inter-service communication
- RESTful APIs for external clients

✅ **Observability & Monitoring**

- Structured logging with correlation IDs

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** with Kubernetes enabled
   - Go to Docker Desktop > Settings > Kubernetes > Enable Kubernetes
2. **Git** for cloning the repository

### One-Command Deployment (Recommended)

#### Option 1: Using Make (Recommended)

```bash
# Clone and deploy everything
git clone <your-repo-url>
cd url-shortener

# Deploy to Kubernetes
make k8s-deploy

# Start port forwarding to access the application
make k8s-access

# Check status
make k8s-status

# View logs
make k8s-logs

# Stop everything (removes all deployment resources)
make k8s-stop
```

#### Option 2: Direct script execution

```bash
# Clone and deploy everything
git clone <your-repo-url>
cd url-shortener
./deploy.sh
```

**Deployment handles:**

- ✅ Prerequisites checking
- ✅ Docker image building
- ✅ Database credentials creation
- ✅ Kubernetes deployment
- ✅ Health verification

**Access the application:**
- Run `make k8s-access` to start port forwarding
- Visit http://localhost:3000/

### 🎯 Available Make Commands

```bash
# Show all available commands
make help

# Kubernetes deployment
make k8s-deploy     # Deploy everything
make k8s-access     # Start port forwarding for access
make k8s-status     # Check status
make k8s-logs       # View logs
make k8s-stop       # Remove all resources
make k8s-restart    # Stop and redeploy
```


## 📡 API Usage

After deploying with `make k8s-deploy`, access via the frontend at **<http://localhost:3000>**:

```bash
# Use the web interface for URL shortening and analytics
open http://localhost:3000

# For development/testing - API endpoints through frontend proxy:
curl -X POST http://localhost:3000/api/shortener/api/v1/ \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/your-awesome-project"}'

# Access short URL
curl -L http://localhost:3000/abc123

# Get analytics
curl http://localhost:3000/api/analytics/api/v1/abc123
```

## 🛠️ Development

### Development Commands

```bash
# Start development environment
make k8s-deploy

# View application status
make k8s-status

# View service logs
make k8s-logs

# Access the application
make k8s-access
```

### Project Structure

```plaintext
├── shortener/          # URL shortening service
├── analytics/          # Analytics service
├── k8s/               # Kubernetes manifests
│   ├── scripts/       # Deployment automation
│   └── storage/       # StatefulSets for databases
├── frontend/          # Simple web interface
└── proto/             # gRPC protocol definitions
```

## 🔒 Security Features

- **Non-root containers** with read-only filesystems
- **Network policies** for service isolation
- **RBAC** with minimal permissions
- **Resource limits** and security contexts
- **Secret management** for sensitive data

## 📊 Monitoring & Observability

### Key Metrics

- HTTP request rates and latency
- Database connection pool status
- Pod resource utilization
- Service health and availability

## 🌐 Production Deployment

### Cloud Provider Setup

**AWS EKS:**

```bash
eksctl create cluster --name url-shortener --region us-west-2
```

**Google GKE:**

```bash
gcloud container clusters create url-shortener --zone us-central1-a
```

**Azure AKS:**

```bash
az aks create --resource-group myResourceGroup --name url-shortener
```

### Image Registry

```bash
# Push to your registry
docker tag url-shortener/shortener:latest your-registry/shortener:latest
docker push your-registry/shortener:latest

# Update k8s/*/deployment.yaml with your registry URLs
```

## 🧪 Testing

```bash
# Health check
make k8s-status

# Service health through frontend
curl http://localhost:3000/api/shortener/health
curl http://localhost:3000/api/analytics/health
```

## 🚨 Troubleshooting

### Common Issues

**Pods stuck in Pending:**

```bash
kubectl describe pods -n url-shortener
kubectl get events -n url-shortener --sort-by='.lastTimestamp'
```

**Database connection errors:**

```bash
kubectl logs -f deployment/postgres -n url-shortener
kubectl exec -it postgres-0 -n url-shortener -- psql -U postgres
```

**Image pull errors:**

```bash
# For Docker Desktop Kubernetes (rebuild images)
docker build -t url-shortener/shortener:latest ./shortener/
docker build -t url-shortener/analytics:latest ./analytics/

# For cloud deployments
docker push your-registry/shortener:latest
```

### Health Checks

```bash
# Check all services
./k8s/scripts/check-health.sh

# Individual service logs
kubectl logs -f deployment/shortener -n url-shortener
kubectl logs -f deployment/analytics -n url-shortener
```

## 🧹 Cleanup

```bash
# Remove all deployment resources
make k8s-stop

# Or manually remove Kubernetes resources
kubectl delete namespace url-shortener
kubectl delete namespace ingress-nginx
```
