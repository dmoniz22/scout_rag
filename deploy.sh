#!/bin/bash

# Scouts Canada RAG System Deployment Script
# Run this on your local server

set -e

echo "🚀 Starting Scouts Canada RAG System Deployment..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run this script as root. Run as your regular user."
   exit 1
fi

# Get current user
USER=$(whoami)
HOME_DIR="/home/$USER"
PROJECT_DIR="$HOME_DIR/scouts-canada-rag"

echo "📁 Creating project directory: $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create directory structure
mkdir -p backend frontend

echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install fastapi==0.110.1 uvicorn==0.25.0 beautifulsoup4 pytesseract pillow PyMuPDF qdrant-client aiohttp apscheduler motor pymongo pydantic python-dotenv requests pandas numpy python-multipart

# Create .env file
cat > .env << EOF
MONGO_URL="mongodb://localhost:27017"
DB_NAME="scouts_rag_db"
CORS_ORIGINS="*"
EOF

echo "📦 Backend dependencies installed!"

# Go back to project root
cd "$PROJECT_DIR"

echo "⚙️ Creating systemd services..."

# Create backend systemd service
sudo tee /etc/systemd/system/scouts-rag-backend.service > /dev/null << EOF
[Unit]
Description=Scouts Canada RAG Backend
After=network.target

[Service]
Type=exec
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=$PROJECT_DIR/backend/venv/bin
ExecStart=$PROJECT_DIR/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "🔧 Services created! Next steps:"
echo "1. Copy the backend/server.py file to $PROJECT_DIR/backend/"
echo "2. Copy the frontend files to $PROJECT_DIR/frontend/"
echo "3. Install frontend dependencies with: cd frontend && npm install"
echo "4. Enable services with: sudo systemctl enable scouts-rag-backend"
echo "5. Start services with: sudo systemctl start scouts-rag-backend"

echo "✅ Deployment preparation complete!"
echo "📍 Project location: $PROJECT_DIR"