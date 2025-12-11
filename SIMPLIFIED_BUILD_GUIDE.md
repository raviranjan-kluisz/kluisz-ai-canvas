# Simplified Backend Build Guide

## 🎯 New: Direct Backend-Only Build

Instead of the complex two-stage build, you can now build the backend directly!

### What's Different?

**Before** (Old way - 2 stages):
```
Step 1: Build base image (backend + frontend) → mohan021/kluisz:latest
Step 2: Remove frontend → mohan021/kluisz-backend:latest
```

**Now** (New way - 1 step):
```
Build backend only → mohan021/kluisz-backend:latest ✨
```

### Benefits

✅ **Faster builds** - Only one Docker build instead of two
✅ **Smaller image** - No frontend bundled (~1.8-2GB)
✅ **Simpler** - Single Dockerfile, single command
✅ **No Node.js** - Runtime image doesn't need Node.js
✅ **Cleaner** - No intermediate images

## Quick Start

### Build and Push (Recommended)

```bash
cd /Users/mohankumar/kluisz/ed_tech_main/kluisz-ai-canvas/k8s

# Build and push optimized backend
./build-backend-direct.sh
```

That's it! One command builds and pushes `mohan021/kluisz-backend:latest`.

### Build Without Pushing (For Testing)

```bash
./build-backend-direct.sh --no-push
```

### Build with Custom Tag

```bash
./build-backend-direct.sh --tag v1.0.0
```

## Files Created

1. **`docker/build_backend_direct.Dockerfile`**
   - Direct backend-only build
   - No frontend dependencies
   - Optimized for size (~2GB)

2. **`k8s/build-backend-direct.sh`**
   - Simple build script
   - One command to build and push

## Deployment

After building, deploy to Kubernetes:

```bash
# Deploy the new image
kubectl set image deployment/kluisz-backend \
  kluisz-backend=mohan021/kluisz-backend:latest \
  -n kluisz-prod

# Watch rollout
kubectl rollout status deployment/kluisz-backend -n kluisz-prod

# Check pods
kubectl get pods -n kluisz-prod -l component=backend
```

## Comparison

| Method | Steps | Images Created | Build Time | Final Size |
|--------|-------|----------------|------------|------------|
| **Old (2-stage)** | 2 builds | 2 images | ~15-20 min | ~5.3 GB |
| **New (direct)** | 1 build | 1 image | ~10-15 min | ~2 GB |

## What's Removed from Runtime Image?

To achieve the smaller size, we removed:
- ❌ Frontend files (not needed for backend-only)
- ❌ Node.js and npm (not needed at runtime)
- ❌ Build tools (gcc, git, build-essential)
- ❌ Development dependencies
- ❌ Test files
- ❌ Python cache files

## What's Included?

Only what's needed to run the backend:
- ✅ Python 3.12
- ✅ Backend code
- ✅ Python dependencies (production only)
- ✅ PostgreSQL client library (libpq5)
- ✅ curl and ca-certificates

## Troubleshooting

### Build fails with "Dockerfile not found"
```bash
# Make sure you're in the k8s directory
cd k8s
./build-backend-direct.sh
```

### Want to test locally first?
```bash
# Build without pushing
./build-backend-direct.sh --no-push

# Run locally
docker run --rm -p 7860:7860 \
  -e KLUISZ_DATABASE_URL="sqlite:///./test.db" \
  mohan021/kluisz-backend:latest
```

### Need to revert to old method?
The old build scripts still work:
```bash
# Old two-stage build
./build-images.sh --backend-only
```

## Next Steps

1. **Build the image**: `./k8s/build-backend-direct.sh`
2. **Deploy to K8s**: `kubectl set image deployment/kluisz-backend...`
3. **Monitor logs**: `kubectl logs -f -l component=backend`

That's it! Much simpler than before. 🎉

