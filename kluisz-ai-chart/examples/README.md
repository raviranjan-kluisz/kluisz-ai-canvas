# Helm Chart Values Examples

This directory contains example values files for different deployment scenarios.

## Available Examples

### 1. Development (values-development.yaml)

Minimal resource configuration for local development or testing:
- Single replica
- Reduced resource limits
- NodePort service for easy access
- Simple credentials
- Latest image tag

**Usage:**
```bash
helm install kluisz-dev ../kluisz-ai-chart -f values-development.yaml
```

### 2. Production (values-production.yaml)

Production-ready configuration with:
- Multiple replicas
- Higher resource limits
- Ingress with TLS
- Autoscaling enabled
- Premium storage class
- Specific version tag

**Usage:**
```bash
helm install kluisz-prod ../kluisz-ai-chart -f values-production.yaml -n production
```

**Important:** Change the database password before deploying!

### 3. External Database (values-external-db.yaml)

Configuration for using external managed database services:
- Internal PostgreSQL disabled
- Configured for external database
- Autoscaling enabled
- Production resource limits

**Usage:**
```bash
# First, create secret with external database URL
kubectl create secret generic kluisz-ai-canvas-external-db \
  --from-literal=database-url="postgresql://user:password@external-db:5432/dbname"

# Then deploy
helm install kluisz-prod ../kluisz-ai-chart -f values-external-db.yaml
```

**Note:** You'll need to modify the deployment template to use the external secret.

### 4. High Availability (values-high-availability.yaml)

HA configuration with:
- 3+ replicas
- Pod anti-affinity rules
- Aggressive autoscaling
- Higher resource allocations
- Rate limiting on ingress

**Usage:**
```bash
helm install kluisz-ha ../kluisz-ai-chart -f values-high-availability.yaml -n production
```

## Combining Multiple Values Files

You can combine multiple values files:

```bash
helm install kluisz-prod ../kluisz-ai-chart \
  -f values-production.yaml \
  -f my-custom-overrides.yaml
```

Files specified later take precedence.

## Using --set Flags

Override specific values from command line:

```bash
helm install kluisz-prod ../kluisz-ai-chart \
  -f values-production.yaml \
  --set kluisz.image.tag=1.2.0 \
  --set postgresql.auth.password=SecurePassword123
```

## Cloud-Specific Storage Classes

Update the `storageClass` based on your cloud provider:

**AWS EKS:**
```yaml
persistence:
  storageClass: "gp3"  # or "gp2"
```

**Google GKE:**
```yaml
persistence:
  storageClass: "standard-rwo"  # or "premium-rwo"
```

**Azure AKS:**
```yaml
persistence:
  storageClass: "managed-premium"  # or "managed"
```

**On-Premises:**
```yaml
persistence:
  storageClass: "nfs-client"  # or your custom storage class
```

## Testing Your Configuration

Before deploying to production, you can:

1. **Dry run:**
```bash
helm install kluisz-test ../kluisz-ai-chart -f values-production.yaml --dry-run --debug
```

2. **Template rendering:**
```bash
helm template kluisz-test ../kluisz-ai-chart -f values-production.yaml > rendered-manifests.yaml
```

3. **Validate:**
```bash
helm lint ../kluisz-ai-chart -f values-production.yaml
```

## Security Best Practices

1. **Never commit secrets:** Use external secret management
   - Sealed Secrets
   - External Secrets Operator
   - HashiCorp Vault
   - Cloud provider secret managers

2. **Change default passwords:** Always override database passwords

3. **Use specific image tags:** Avoid `latest` in production

4. **Enable network policies:** Restrict pod-to-pod communication

5. **Regular updates:** Keep images and charts up to date

## Customizing for Your Environment

Create your own values file:

```bash
cp values-production.yaml my-company-prod.yaml
# Edit my-company-prod.yaml with your settings
helm install kluisz-prod ../kluisz-ai-chart -f my-company-prod.yaml
```

Key things to customize:
- Domain names
- Resource limits based on your workload
- Storage class and sizes
- Database credentials
- Ingress annotations
- Node selectors and tolerations
- Monitoring annotations

## Support

For more information:
- See main README.md in parent directory
- Check DEPLOYMENT_GUIDE.md for detailed deployment instructions
- Report issues: https://github.com/kluisz/kluisz-ai-canvas/issues
