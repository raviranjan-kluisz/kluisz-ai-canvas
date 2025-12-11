# syntax=docker/dockerfile:1
# Direct Frontend-Only Build
# Optimized Nginx-based frontend

################################
# BUILDER STAGE - Build React App
################################
FROM node:20-slim AS builder

WORKDIR /app

# Copy package files
COPY src/frontend/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps \
    && npm install @chakra-ui/system @chakra-ui/react @emotion/react @emotion/styled framer-motion --legacy-peer-deps

# Copy source code
COPY src/frontend ./

# Build the frontend
RUN NODE_OPTIONS="--max-old-space-size=8192" \
    ESBUILD_BINARY_PATH="" \
    npm run build

################################
# RUNTIME - Nginx to serve static files
################################
FROM nginx:alpine-slim AS runtime

# Install envsubst for environment variable substitution
RUN apk add --no-cache gettext

# Copy custom nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/nginx.conf
COPY docker/frontend/default.conf.template /etc/nginx/templates/default.conf.template

# Copy built frontend from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy startup script
COPY docker/frontend/start-nginx.sh /start-nginx.sh
RUN chmod +x /start-nginx.sh

# Set default backend URL (can be overridden at runtime)
ENV BACKEND_URL=http://kluisz-backend-service:7860

EXPOSE 80

# Use the startup script
CMD ["/start-nginx.sh"]



