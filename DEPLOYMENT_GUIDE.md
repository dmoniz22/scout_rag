# Scouts Canada RAG System - Local Deployment Guide

## Prerequisites
- Python 3.8+ with pip
- Node.js 18+ with npm/yarn
- Qdrant running at your specified IP (192.168.68.8:6333)
- Ollama with models: llama3.1:8b, nomic-embed-text
- Tesseract OCR installed

## Step 1: Create Project Structure
```bash
mkdir ~/scouts-canada-rag
cd ~/scouts-canada-rag
mkdir backend frontend
```

## Step 2: Backend Setup

### Install Python Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn beautifulsoup4 pytesseract pillow PyMuPDF qdrant-client aiohttp apscheduler motor pymongo pydantic python-dotenv requests pandas numpy python-multipart
```

### Configure Environment Variables
Create `backend/.env`:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="scouts_rag_db"
CORS_ORIGINS="*"
```

## Step 3: Frontend Setup
```bash
cd frontend
npm install react react-dom react-router-dom axios lucide-react
# Install Shadcn/UI components (you'll need to copy these from the original)
```

## Step 4: System Service Setup (Recommended)

### Create systemd service for backend
```bash
sudo nano /etc/systemd/system/scouts-rag-backend.service
```

Content:
```ini
[Unit]
Description=Scouts Canada RAG Backend
After=network.target

[Service]
Type=exec
User=yourusername
WorkingDirectory=/home/yourusername/scouts-canada-rag/backend
Environment=PATH=/home/yourusername/scouts-canada-rag/backend/venv/bin
ExecStart=/home/yourusername/scouts-canada-rag/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### Create systemd service for frontend
```bash
sudo nano /etc/systemd/system/scouts-rag-frontend.service
```

Content:
```ini
[Unit]
Description=Scouts Canada RAG Frontend
After=network.target

[Service]
Type=exec
User=yourusername
WorkingDirectory=/home/yourusername/scouts-canada-rag/frontend
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable and start services
```bash
sudo systemctl daemon-reload
sudo systemctl enable scouts-rag-backend
sudo systemctl enable scouts-rag-frontend
sudo systemctl start scouts-rag-backend
sudo systemctl start scouts-rag-frontend
```

## Step 5: Test External Services

### Test Qdrant Connection
```bash
curl -X GET http://192.168.68.8:6333/collections
```

### Test Ollama
```bash
curl -X POST http://localhost:11434/api/embeddings -d '{"model": "nomic-embed-text", "prompt": "test"}'
curl -X POST http://localhost:11434/api/generate -d '{"model": "llama3.1:8b", "prompt": "Hello", "stream": false}'
```

## Step 6: Configure Reverse Proxy (Optional)
If you want to access via domain name, configure nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Step 7: Verify Installation
1. Access http://localhost:3000 (or your domain)
2. Go to Settings page to check system status
3. All services should show "Healthy" status
4. Start a manual scraping job to test

## Automatic Scraping
Yes! The system will automatically scrape scouts.ca every Sunday at 2:00 AM once deployed. The scheduler starts automatically with the backend service.

You can also trigger manual scraping anytime through the web interface.