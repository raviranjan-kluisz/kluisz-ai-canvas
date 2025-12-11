# Kluisz AI Canvas Helm Chart

This Helm chart deploys Kluisz AI Canvas on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (for persistent storage)
- Optional: Ingress controller (if using Ingress)

## Installation

### Add the chart repository (if applicable)

```bash
helm repo add kluisz https://charts.kluisz.io
helm repo update
```

### Install from local directory

```bash
cd /Users/raviranjan/kluisz-ai-canvas
helm install kluisz-ai-canvas ./kluisz-ai-chart
```

### Install with custom values

```bash
helm install kluisz-ai-canvas ./kluisz-ai-chart -f custom-values.yaml
```

### Install in a specific namespace

```bash
kubectl create namespace kluisz
helm install kluisz-ai-canvas ./kluisz-ai-chart -n kluisz
```

## Configuration

The following table lists the configurable parameters and their default values.

### Kluisz Application Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `kluisz.replicaCount` | Number of Kluisz replicas | `1` |
| `kluisz.image.repository` | Kluisz image repository | `kluisz/kluisz-ai-canvas` |
| `kluisz.image.tag` | Kluisz image tag | `latest` |
| `kluisz.image.pullPolicy` | Image pull policy | `Always` |
| `kluisz.service.type` | Kubernetes service type | `ClusterIP` |
| `kluisz.service.port` | Service port | `7860` |
| `kluisz.resources.limits.cpu` | CPU limit | `2000m` |
| `kluisz.resources.limits.memory` | Memory limit | `4Gi` |
| `kluisz.resources.requests.cpu` | CPU request | `500m` |
| `kluisz.resources.requests.memory` | Memory request | `1Gi` |
| `kluisz.persistence.enabled` | Enable persistence | `true` |
| `kluisz.persistence.size` | Size of persistent volume | `10Gi` |
| `kluisz.persistence.storageClass` | Storage class name | `""` (default) |

### PostgreSQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `postgresql.enabled` | Enable PostgreSQL | `true` |
| `postgresql.image.repository` | PostgreSQL image repository | `postgres` |
| `postgresql.image.tag` | PostgreSQL image tag | `16` |
| `postgresql.auth.username` | Database username | `kluisz` |
| `postgresql.auth.password` | Database password | `kluisz` |
| `postgresql.auth.database` | Database name | `kluisz` |
| `postgresql.persistence.enabled` | Enable persistence | `true` |
| `postgresql.persistence.size` | Size of persistent volume | `20Gi` |
| `postgresql.resources.limits.cpu` | CPU limit | `1000m` |
| `postgresql.resources.limits.memory` | Memory limit | `2Gi` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hosts[0].host` | Hostname | `kluisz-ai-canvas.example.com` |
| `ingress.tls` | TLS configuration | `[]` |

### Autoscaling Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU % | `80` |

## Examples

### Example 1: Install with custom database credentials

Create a `custom-values.yaml` file:

```yaml
postgresql:
  auth:
    username: myuser
    password: mysecurepassword
    database: mydb
```

Install:

```bash
helm install kluisz-ai-canvas ./kluisz-ai-chart -f custom-values.yaml
```

### Example 2: Enable Ingress with TLS

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: kluisz.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: kluisz-tls
      hosts:
        - kluisz.yourdomain.com
```

### Example 3: Enable Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Example 4: Use external PostgreSQL

```yaml
postgresql:
  enabled: false

# Then manually set the database URL in the secret
# or use an external secret management solution
```

## Upgrading

```bash
helm upgrade kluisz-ai-canvas ./kluisz-ai-chart
```

## Uninstalling

```bash
helm uninstall kluisz-ai-canvas
```

Note: PersistentVolumeClaims are not deleted automatically. To delete them:

```bash
kubectl delete pvc -l app.kubernetes.io/instance=kluisz-ai-canvas
```

## Persistence

The chart mounts PersistentVolumes for both the application data and PostgreSQL data. The volumes are created using dynamic volume provisioning.

If you want to use a specific storage class:

```yaml
kluisz:
  persistence:
    storageClass: "fast-ssd"

postgresql:
  persistence:
    storageClass: "fast-ssd"
```

## Security Considerations

1. **Change default credentials**: Always change the default PostgreSQL credentials in production:

```yaml
postgresql:
  auth:
    password: <strong-password>
```

2. **Use Secrets**: Consider using Kubernetes external secrets or sealed secrets for sensitive data.

3. **Network Policies**: Implement network policies to restrict pod-to-pod communication.

4. **RBAC**: The chart creates a ServiceAccount. Configure RBAC as needed for your environment.

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l app.kubernetes.io/instance=kluisz-ai-canvas
```

### View logs

```bash
kubectl logs -l app.kubernetes.io/name=kluisz-ai-canvas
```

### Check PostgreSQL connection

```bash
kubectl exec -it <kluisz-pod-name> -- env | grep DATABASE
```

### Access the application locally

```bash
kubectl port-forward svc/kluisz-ai-canvas 7860:7860
```

Then visit http://localhost:7860

## Architecture

The Helm chart deploys:

- **Deployment**: For the Kluisz AI Canvas application
- **StatefulSet**: For PostgreSQL database (ensures stable storage)
- **Services**: ClusterIP services for both components
- **PersistentVolumeClaims**: For data persistence
- **ConfigMap**: For application configuration
- **Secret**: For database credentials
- **Ingress** (optional): For external access
- **HorizontalPodAutoscaler** (optional): For autoscaling

## Contributing

Please report issues at: https://github.com/kluisz/kluisz-ai-canvas/issues

## License

This chart is provided as-is for deploying Kluisz AI Canvas on Kubernetes.
