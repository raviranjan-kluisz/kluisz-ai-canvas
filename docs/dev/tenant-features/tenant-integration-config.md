# Tenant Integration Configuration Guide

> **Document Version**: 1.0  
> **Last Updated**: January 2025

---

## Overview

`TenantIntegrationConfig` stores tenant-specific configuration and credentials for third-party integrations (MCP servers, Langfuse, vector stores, etc.). This document explains the separation between `config` and `encrypted_config` fields.

---

## Field Separation: `config` vs `encrypted_config`

### `config` (JSON) - Non-Sensitive Configuration

**Purpose**: Stores non-sensitive, queryable configuration data.

**What goes here:**
- Public API keys (if safe to expose)
- Base URLs and endpoints
- Feature flags and settings
- Display names and labels
- Connection timeouts and retry settings
- Non-sensitive metadata

**Example:**
```json
{
  "public_key": "pk_lf_abc123",
  "base_url": "https://cloud.langfuse.com",
  "project_id": "proj_xyz789",
  "timeout": 30,
  "retry_count": 3
}
```

**Characteristics:**
- ✅ Stored as plain JSON (not encrypted)
- ✅ Queryable via SQL JSON operators
- ✅ Can be indexed (PostgreSQL JSONB)
- ✅ Visible in logs (sanitized)
- ⚠️ Should NOT contain secrets, passwords, or private keys

---

### `encrypted_config` (BLOB) - Sensitive Credentials

**Purpose**: Stores sensitive data encrypted at rest.

**What goes here:**
- Secret API keys
- Passwords and tokens
- Private keys
- OAuth client secrets
- Database connection strings with passwords
- Any PII or sensitive data

**Example:**
```python
# Encrypted bytes stored in database
encrypted_config = encrypt({
  "secret_key": "sk_lf_secret123",
  "api_password": "secure_password",
  "private_key": "-----BEGIN PRIVATE KEY-----\n..."
})
```

**Characteristics:**
- ✅ Encrypted at rest using application encryption key
- ✅ Decrypted only when needed (in memory)
- ❌ NOT queryable via SQL
- ❌ NOT indexed
- ❌ Never logged or exposed in API responses
- ⚠️ Must be decrypted before use

---

## Usage Pattern

### When Creating/Updating Config

```python
from kluisz.services.encryption import encrypt_config, decrypt_config

# Create integration config
config = TenantIntegrationConfig(
    tenant_id=tenant_id,
    integration_key="langfuse",
    config={
        # Non-sensitive data
        "public_key": "pk_lf_abc123",
        "base_url": "https://cloud.langfuse.com",
        "project_id": "proj_xyz789",
    },
    encrypted_config=encrypt_config({
        # Sensitive data
        "secret_key": "sk_lf_secret123",
        "api_password": "secure_password",
    }),
    is_enabled=True,
)
```

### When Reading Config

```python
# Read config
integration_config = session.query(TenantIntegrationConfig).filter(
    TenantIntegrationConfig.tenant_id == tenant_id,
    TenantIntegrationConfig.integration_key == "langfuse",
).first()

# Access non-sensitive data directly
base_url = integration_config.config["base_url"]

# Decrypt sensitive data when needed
secret_key = decrypt_config(integration_config.encrypted_config)["secret_key"]
```

---

## Best Practices

### ✅ DO

1. **Separate clearly**: Put queryable, non-sensitive data in `config`, secrets in `encrypted_config`
2. **Encrypt secrets**: Always encrypt sensitive data before storing
3. **Decrypt on-demand**: Only decrypt `encrypted_config` when actually needed
4. **Clear memory**: Clear decrypted secrets from memory after use
5. **Validate schema**: Use `IntegrationRegistry.config_schema` to validate structure

### ❌ DON'T

1. **Don't mix**: Don't put secrets in `config` JSON
2. **Don't log secrets**: Never log `encrypted_config` contents
3. **Don't expose**: Never return `encrypted_config` in API responses
4. **Don't query secrets**: Don't try to query encrypted data via SQL
5. **Don't store plaintext**: Never store unencrypted secrets

---

## Health Check Status

The `health_status` field tracks integration health:

| Value | Meaning |
|-------|---------|
| `healthy` | Integration is working correctly |
| `degraded` | Integration is partially functional (e.g., slow responses) |
| `unhealthy` | Integration is failing (e.g., authentication errors) |
| `NULL` | Health check not yet performed |

**CHECK Constraint**: Enforced at database level - only these values are allowed.

---

## Example: Langfuse Integration

```python
# Integration Registry Entry
integration_registry = IntegrationRegistry(
    integration_key="langfuse",
    integration_name="Langfuse",
    feature_key="integrations.langfuse",
    config_schema={
        "type": "object",
        "properties": {
            "public_key": {"type": "string"},
            "base_url": {"type": "string", "default": "https://cloud.langfuse.com"},
            "project_id": {"type": "string"},
        },
        "required": ["public_key", "project_id"],
    },
)

# Tenant-Specific Config
tenant_config = TenantIntegrationConfig(
    tenant_id="acme-corp",
    integration_key="langfuse",
    config={
        "public_key": "pk_lf_acme123",
        "base_url": "https://cloud.langfuse.com",
        "project_id": "proj_acme456",
    },
    encrypted_config=encrypt_config({
        "secret_key": "sk_lf_secret789",
    }),
    is_enabled=True,
    health_status="healthy",
    last_health_check=datetime.now(timezone.utc),
)
```

---

## Security Considerations

1. **Encryption Key Management**: 
   - Use environment variable for encryption key
   - Rotate keys periodically
   - Use key management service (AWS KMS, Azure Key Vault) in production

2. **Access Control**:
   - Only tenant admins can view/edit their tenant's configs
   - Super admins can view all configs (for support)
   - Audit all config changes via `FeatureAuditLog`

3. **Data Retention**:
   - Delete `encrypted_config` when integration is removed
   - Clear decrypted data from memory immediately after use
   - Don't cache decrypted secrets

---

## Related Documentation

- [erd.md](./erd.md) - Database schema
- [erd-critical-analysis.md](./erd-critical-analysis.md) - Design analysis
- [architecture.md](./architecture.md) - System architecture
