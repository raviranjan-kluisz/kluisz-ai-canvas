# Kubernetes Deployment Guide for Kluisz AI Canvas

This guide walks you through deploying Kluisz AI Canvas on a Kubernetes cluster using the Helm chart.

## Quick Start

### 1. Prerequisites Check

```bash
# Verify kubectl is configured
kubectl cluster-info

# Verify Helm is installed
helm version

# Check available storage classes
kubectl get storageclass
```

### 2. Create Namespace (Optional but Recommended)

```bash
kubectl create namespace kluisz
```

### 3. Deploy with Default Settings

```bash
helm install kluisz-ai-canvas ./kluisz-ai-chart -n kluisz
```

### 4. Monitor Deployment

```bash
# Watch pods starting up
kubectl get pods -n kluisz -w

# Check deployment status
kubectl get all -n kluisz

# View logs
kubectl logs -n kluisz -l app.kubernetes.io/component=kluisz -f
```

### 5. Access the Application

#### Option A: Port Forward (for testing)

```bash
kubectl port-forward -n kluisz svc/kluisz-ai-canvas 7860:7860
```

Then visit: http://localhost:7860

#### Option B: Using LoadBalancer (Cloud)

Update values.yaml:

```yaml
kluisz:
  service:
    type: LoadBalancer
```

Deploy:

```bash
helm upgrade kluisz-ai-canvas ./kluisz-ai-chart -n kluisz
kubectl get svc -n kluisz kluisz-ai-canvas
```

#### Option C: Using Ingress (Recommended for Production)

```bash
# First, ensure you have an Ingress controller installed
# For nginx-ingress:
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install nginx-ingress ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace

# Create custom values file
cat > production-values.yaml <<EOF
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: kluisz.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: kluisz-tls
      hosts:
        - kluisz.yourdomain.com

postgresql:
  auth:
    password: "CHANGE-ME-TO-SECURE-PASSWORD"
EOF

# Deploy with ingress
helm upgrade --install kluisz-ai-canvas ./kluisz-ai-chart -n kluisz -f production-values.yaml
```

## Production Deployment Checklist

### 1. Security Configuration

```yaml
# production-values.yaml
postgresql:
  auth:
    username: kluisz_prod
    password: "<GENERATE-STRONG-PASSWORD>"
    database: kluisz_prod

# Consider using external secrets
# Example with Sealed Secrets:
# kubectl create secret generic kluisz-db-secret \
#   --from-literal=password=<strong-password> \
#   --dry-run=client -o yaml | \
#   kubeseal -o yaml > sealed-secret.yaml
```

### 2. Resource Limits

```yaml
kluisz:
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi

postgresql:
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi
```

### 3. Persistent Storage

```yaml
# Use a production-grade storage class
kluisz:
  persistence:
    storageClass: "premium-rwo"  # GKE
    # storageClass: "gp3"         # AWS EKS
    # storageClass: "managed-premium"  # Azure AKS
    size: 50Gi

postgresql:
  persistence:
    storageClass: "premium-rwo"
    size: 100Gi
```

### 4. High Availability (Optional)

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

# For HA PostgreSQL, consider using external managed database
postgresql:
  enabled: false

# Then provide external database connection
# via secret or external secret manager
```

### 5. Monitoring and Observability

```bash
# Add Prometheus annotations (if using Prometheus)
# Add to values.yaml:
```

```yaml
kluisz:
  podAnnotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "7860"
    prometheus.io/path: "/metrics"
```

## Backup and Recovery

### Backup PostgreSQL Data

```bash
# Create a backup job
kubectl run -n kluisz postgres-backup --rm -it --restart=Never \
  --image=postgres:16 -- \
  pg_dump -h kluisz-ai-canvas-postgresql -U kluisz -d kluisz > backup.sql

# Or use a CronJob for automated backups
cat > postgres-backup-cronjob.yaml <<EOF
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: kluisz
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/bash
            - -c
            - pg_dump -h kluisz-ai-canvas-postgresql -U kluisz -d kluisz | gzip > /backup/backup-\$(date +%Y%m%d-%H%M%S).sql.gz
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: kluisz-ai-canvas-secret
                  key: postgres-password
            volumeMounts:
            - name: backup-volume
              mountPath: /backup
          restartPolicy: OnFailure
          volumes:
          - name: backup-volume
            persistentVolumeClaim:
              claimName: postgres-backup-pvc
EOF

kubectl apply -f postgres-backup-cronjob.yaml
```

### Restore PostgreSQL Data

```bash
kubectl cp backup.sql kluisz/kluisz-ai-canvas-postgresql-0:/tmp/backup.sql
kubectl exec -n kluisz kluisz-ai-canvas-postgresql-0 -- \
  psql -U kluisz -d kluisz -f /tmp/backup.sql
```

## Upgrading

### Upgrade to a New Version

```bash
# Update the image tag in values.yaml
# Or use --set flag
helm upgrade kluisz-ai-canvas ./kluisz-ai-chart -n kluisz \
  --set kluisz.image.tag=1.1.0

# Monitor the rollout
kubectl rollout status deployment/kluisz-ai-canvas -n kluisz
```

### Rollback if Needed

```bash
# View release history
helm history kluisz-ai-canvas -n kluisz

# Rollback to previous version
helm rollback kluisz-ai-canvas -n kluisz

# Or rollback to specific revision
helm rollback kluisz-ai-canvas 1 -n kluisz
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n kluisz <pod-name>

# Check events
kubectl get events -n kluisz --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n kluisz <pod-name>
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -n kluisz test-postgres --rm -it --restart=Never \
  --image=postgres:16 -- \
  psql -h kluisz-ai-canvas-postgresql -U kluisz -d kluisz

# Check secret
kubectl get secret -n kluisz kluisz-ai-canvas-secret -o yaml
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n kluisz

# Check PV
kubectl get pv

# Describe PVC for events
kubectl describe pvc -n kluisz <pvc-name>
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -n kluisz

# Check HPA status (if enabled)
kubectl get hpa -n kluisz

# Check node resources
kubectl top nodes
```

## Cleanup

### Uninstall the Release

```bash
helm uninstall kluisz-ai-canvas -n kluisz
```

### Delete Persistent Data (WARNING: Data Loss!)

```bash
# Delete PVCs
kubectl delete pvc -n kluisz -l app.kubernetes.io/instance=kluisz-ai-canvas

# Delete namespace
kubectl delete namespace kluisz
```

## Cloud-Specific Notes

### AWS EKS

```yaml
# Use GP3 storage class for better performance
kluisz:
  persistence:
    storageClass: "gp3"

postgresql:
  persistence:
    storageClass: "gp3"

# Or use RDS for PostgreSQL
postgresql:
  enabled: false
# Configure external database connection
```

### Google GKE

```yaml
# Use regional persistent disks
kluisz:
  persistence:
    storageClass: "standard-rwo"

postgresql:
  persistence:
    storageClass: "standard-rwo"

# Or use Cloud SQL
postgresql:
  enabled: false
# Use Cloud SQL Proxy sidecar
```

### Azure AKS

```yaml
# Use Azure managed disks
kluisz:
  persistence:
    storageClass: "managed-premium"

postgresql:
  persistence:
    storageClass: "managed-premium"

# Or use Azure Database for PostgreSQL
postgresql:
  enabled: false
```

## Support

For issues and questions:
- GitHub: https://github.com/kluisz/kluisz-ai-canvas/issues
- Documentation: See README.md in this directory
