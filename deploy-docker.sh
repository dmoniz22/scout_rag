#!/bin/bash

# Scouts Canada RAG System - Docker Deployment Script
# Run this on your server after cloning the repository

set -e

echo "🐳 Starting Docker Deployment for Scouts Canada RAG System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

echo "📋 Pre-deployment checklist:"
echo "✓ Docker and Docker Compose are installed"
echo "✓ Found docker-compose.yml file"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file to match your configuration before continuing."
    echo "   Key settings to verify:"
    echo "   - QDRANT_HOST (currently: 192.168.68.8)"
    echo "   - OLLAMA_HOST (currently: host.docker.internal)"
    read -p "Press Enter after editing .env file..."
fi

# Check external services
echo "🔍 Checking external services..."

# Check Qdrant
QDRANT_HOST=$(grep QDRANT_HOST .env | cut -d '=' -f2)
QDRANT_PORT=$(grep QDRANT_PORT .env | cut -d '=' -f2)
echo "Testing Qdrant connection at $QDRANT_HOST:$QDRANT_PORT..."

if curl -s --connect-timeout 5 "http://$QDRANT_HOST:$QDRANT_PORT/collections" > /dev/null; then
    echo "✅ Qdrant is accessible"
else
    echo "⚠️  Warning: Cannot connect to Qdrant at $QDRANT_HOST:$QDRANT_PORT"
    echo "   The application will still start but scraping/querying won't work until Qdrant is available."
fi

# Check Ollama (will be accessible via host.docker.internal from containers)
echo "Testing Ollama connection..."
if curl -s --connect-timeout 5 "http://localhost:11434/api/tags" > /dev/null; then
    echo "✅ Ollama is accessible"
    
    # Check for required models
    if ollama list | grep -q "llama3.1:8b"; then
        echo "✅ llama3.1:8b model found"
    else
        echo "⚠️  Warning: llama3.1:8b model not found. Run: ollama pull llama3.1:8b"
    fi
    
    if ollama list | grep -q "nomic-embed-text"; then
        echo "✅ nomic-embed-text model found"
    else
        echo "⚠️  Warning: nomic-embed-text model not found. Run: ollama pull nomic-embed-text"
    fi
else
    echo "⚠️  Warning: Cannot connect to Ollama at localhost:11434"
    echo "   Make sure Ollama is running with the required models."
fi

echo ""
echo "🚀 Starting Docker containers..."

# Stop existing containers if they exist
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check container status
echo "📊 Container status:"
docker-compose ps

# Check if services are healthy
echo "🏥 Checking service health..."

# Check backend health
if curl -s --connect-timeout 10 "http://localhost:8001/api/" | grep -q "Scouts Canada RAG System API"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    echo "📋 Backend logs:"
    docker-compose logs --tail=20 backend
fi

# Check frontend
if curl -s --connect-timeout 10 "http://localhost:3000/" > /dev/null; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend not accessible"
    echo "📋 Frontend logs:"
    docker-compose logs --tail=20 frontend
fi

echo ""
echo "🎉 Deployment complete!"
echo "📍 Access your application:"
echo "   🌐 Web Interface: http://localhost:3000"
echo "   📚 API Docs: http://localhost:8001/docs"
echo "   ⚙️  System Status: http://localhost:3000/settings"
echo ""
echo "📝 Next steps:"
echo "1. Visit http://localhost:3000/settings to check system status"
echo "2. Go to http://localhost:3000/scraping to start your first scraping job"
echo "3. Use http://localhost:3000 to ask questions about Scouts Canada"
echo ""
echo "🔧 Useful commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop: docker-compose down"
echo "   Restart: docker-compose restart [service]"
echo "   Update: git pull && docker-compose up -d --build"