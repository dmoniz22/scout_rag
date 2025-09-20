#!/bin/bash

# Production Build Script for Scouts Canada RAG System

set -e

echo "🏗️  Building Scouts Canada RAG System for Production..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

# Create production environment file
echo "📝 Creating production environment configuration..."
cat > .env.production << EOF
# Production Environment Configuration
MONGO_URL=mongodb://mongodb:27017
DB_NAME=scouts_rag_production
CORS_ORIGINS=*

# External Services - Update these for your setup
QDRANT_HOST=192.168.68.8
QDRANT_PORT=6333
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434

# Frontend - Update with your domain
REACT_APP_BACKEND_URL=http://your-domain.com
EOF

echo "⚠️  Please edit .env.production with your production settings:"
echo "   - Update REACT_APP_BACKEND_URL with your domain"
echo "   - Verify QDRANT_HOST and OLLAMA_HOST settings"
echo "   - Consider changing DB_NAME for production"

# Build production images
echo "🐳 Building production Docker images..."
docker-compose -f docker-compose.yml --profile production build --no-cache

echo "🎉 Production build complete!"
echo ""
echo "📋 To deploy to production:"
echo "1. Edit .env.production with your settings"
echo "2. Copy .env.production to .env"
echo "3. Run: docker-compose --profile production up -d"
echo ""
echo "🌐 Production will be available at:"
echo "   - Main site: http://your-domain.com (port 80)"
echo "   - Direct backend: http://your-domain.com:8001"
echo "   - Direct frontend: http://your-domain.com:3000"