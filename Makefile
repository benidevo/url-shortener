# Default help command
help:
	@echo "🔗 URL Shortener - Kubernetes Deployment"
	@echo ""
	@echo "Quick Start:"
	@echo "  make k8s-deploy     - Deploy to Kubernetes"
	@echo "  make k8s-access     - Access via port forwarding"
	@echo "  make k8s-status     - Check deployment status"
	@echo "  make k8s-stop       - Remove all resources"
	@echo ""
	@echo "For detailed command list: make k8s-help"


##
## Kubernetes Deployment Commands
##

.PHONY: k8s-help k8s-deploy k8s-access k8s-status k8s-logs k8s-cleanup k8s-stop k8s-restart

# Show Kubernetes help
k8s-help:
	@echo "🔗 URL Shortener - Kubernetes Deployment"
	@echo ""
	@echo "Kubernetes commands:"
	@echo "  make k8s-deploy     - Deploy the complete application to Kubernetes"
	@echo "  make k8s-access     - Start port forwarding to access the application"
	@echo "  make k8s-status     - Check the status of all services"
	@echo "  make k8s-logs       - Show logs from all services"
	@echo "  make k8s-cleanup    - Remove ALL resources created by deployment"
	@echo "  make k8s-stop       - Alias for k8s-cleanup"
	@echo "  make k8s-restart    - Stop and redeploy the application"
	@echo ""
	@echo "📡 After deployment, access the application at:"
	@echo "  • Frontend: http://localhost:3000/"

# Deploy the complete application to Kubernetes
k8s-deploy:
	@echo "🚀 Deploying URL Shortener to Kubernetes..."
	@./deploy.sh

# Start port forwarding to access the application
k8s-access:
	@echo "🌐 Starting port forwarding to access the application..."
	@echo "📡 Application will be available at: http://localhost:3000/"
	@echo "Press Ctrl+C to stop port forwarding"
	@echo ""
	kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 3000:3000

# Check status of all Kubernetes resources
k8s-status:
	@echo "📊 Checking application status..."
	@echo ""
	@echo "=== Namespaces ==="
	@kubectl get namespaces | grep -E "(url-shortener|ingress-nginx|NAME)"
	@echo ""
	@echo "=== Pods ==="
	@kubectl get pods -n url-shortener -o wide 2>/dev/null || echo "No url-shortener namespace found"
	@echo ""
	@echo "=== Services ==="
	@kubectl get services -n url-shortener 2>/dev/null || echo "No url-shortener namespace found"
	@echo ""
	@echo "=== Ingress ==="
	@kubectl get ingress -n url-shortener 2>/dev/null || echo "No ingress found"
	@echo ""
	@echo "=== NGINX Ingress Controller ==="
	@kubectl get pods -n ingress-nginx 2>/dev/null || echo "No ingress-nginx namespace found"

# Show logs from all Kubernetes services
k8s-logs:
	@echo "📝 Recent logs from all services..."
	@echo ""
	@if kubectl get namespace url-shortener >/dev/null 2>&1; then \
		echo "=== Shortener Service Logs ==="; \
		kubectl logs deployment/shortener -n url-shortener --tail=20 2>/dev/null || echo "Shortener not ready"; \
		echo ""; \
		echo "=== Analytics Service Logs ==="; \
		kubectl logs deployment/analytics -n url-shortener --tail=20 2>/dev/null || echo "Analytics not ready"; \
		echo ""; \
		echo "=== Frontend Service Logs ==="; \
		kubectl logs deployment/frontend -n url-shortener --tail=20 2>/dev/null || echo "Frontend not ready"; \
		echo ""; \
		echo "=== PostgreSQL Logs ==="; \
		kubectl logs statefulset/postgres -n url-shortener --tail=10 2>/dev/null || echo "PostgreSQL not ready"; \
	else \
		echo "url-shortener namespace not found. Run 'make k8s-deploy' first."; \
	fi

# Clean up all Kubernetes resources created by deployment
k8s-cleanup:
	@echo "🧹 Cleaning up URL Shortener resources..."
	@echo ""
	@echo "⚠️  This will remove ALL resources created by the deployment:"
	@echo "   • url-shortener namespace (all apps, databases, etc.)"
	@echo "   • ingress-nginx namespace (NGINX controller)"
	@echo "   • metrics-server (for HPA auto-scaling)"
	@echo ""
	@echo "Are you sure? Press Ctrl+C to cancel, or Enter to continue..."
	@read
	@echo ""
	@echo "Stopping port forwarding processes..."
	@pkill -f "kubectl port-forward" 2>/dev/null || true
	@sleep 2
	@echo ""
	@echo "Deleting application namespace..."
	@kubectl delete namespace url-shortener 2>/dev/null || echo "Namespace url-shortener not found"
	@echo ""
	@echo "Deleting NGINX Ingress Controller..."
	@kubectl delete namespace ingress-nginx 2>/dev/null || echo "Namespace ingress-nginx not found"
	@echo ""
	@echo "Deleting Metrics Server..."
	@kubectl delete -f k8s/infrastructure/metrics-server.yaml 2>/dev/null || echo "Metrics server not found"
	@echo ""
	@echo "✅ Complete cleanup finished!"
	@echo ""
	@echo "All resources created by deploy.sh have been removed."

# Alias for k8s-cleanup
k8s-stop: k8s-cleanup

# Force cleanup without confirmation (for scripts/automation)
k8s-cleanup-force:
	@echo "🧹 Force cleaning up URL Shortener resources..."
	@echo ""
	@echo "Stopping port forwarding processes..."
	@pkill -f "kubectl port-forward" 2>/dev/null || true
	@sleep 2
	@echo ""
	@echo "Deleting application namespace..."
	@kubectl delete namespace url-shortener 2>/dev/null || echo "Namespace url-shortener not found"
	@echo ""
	@echo "Deleting NGINX Ingress Controller..."
	@kubectl delete namespace ingress-nginx 2>/dev/null || echo "Namespace ingress-nginx not found"
	@echo ""
	@echo "Deleting Metrics Server..."
	@kubectl delete -f k8s/infrastructure/metrics-server.yaml 2>/dev/null || echo "Metrics server not found"
	@echo ""
	@echo "✅ Complete cleanup finished!"

# Restart the Kubernetes application (cleanup + deploy)
k8s-restart: k8s-cleanup-force
	@echo ""
	@echo "⏳ Waiting 10 seconds for cleanup to complete..."
	@sleep 10
	@echo ""
	@echo "🔄 Redeploying application..."
	@$(MAKE) k8s-deploy
