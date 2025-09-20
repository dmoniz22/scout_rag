# GitHub Repository Setup Guide

This guide shows how to create a GitHub repository and deploy the Scouts Canada RAG System to your server.

## Step 1: Create GitHub Repository

### Option A: GitHub Web Interface
1. Go to [GitHub.com](https://github.com) and sign in
2. Click "New repository" (green button)
3. Repository details:
   - **Name**: `scouts-canada-rag`
   - **Description**: `Intelligent document retrieval and Q&A system for Scouts Canada documentation`
   - **Visibility**: Public or Private (your choice)
   - **Initialize**: Don't initialize with README (we have our own)
4. Click "Create repository"

### Option B: GitHub CLI (if you have it installed)
```bash
gh repo create scouts-canada-rag --description "Intelligent document retrieval and Q&A system for Scouts Canada documentation" --public
```

## Step 2: Prepare Files for Upload

Since you're working in a development environment, you'll need to manually copy the key files to your local machine, then upload to GitHub.

### Essential Files to Copy:

**Root Directory:**
- `docker-compose.yml`
- `nginx.conf`
- `.env.example`
- `.dockerignore`
- `README.md`
- `deploy-docker.sh`
- `build-production.sh`

**Backend Directory (`backend/`):**
- `server.py`
- `requirements.txt`
- `Dockerfile`
- `.env` (rename to `.env.example` for GitHub)

**Frontend Directory (`frontend/`):**
- `src/App.js`
- `src/App.css`
- `package.json`
- `nginx.conf`
- `Dockerfile`
- All Shadcn UI components from `src/components/ui/`

## Step 3: Upload to GitHub

### Method A: GitHub Web Interface Upload
1. Go to your new repository page
2. Click "uploading an existing file"
3. Upload files maintaining directory structure
4. Commit with message: "Initial commit: Scouts Canada RAG System"

### Method B: Git Command Line (Preferred)
If you can transfer files to your local machine:

```bash
# Clone the empty repository
git clone https://github.com/yourusername/scouts-canada-rag.git
cd scouts-canada-rag

# Copy all your files into this directory
# Maintain the directory structure:
# scouts-canada-rag/
# ├── backend/
# ├── frontend/
# ├── docker-compose.yml
# └── etc.

# Add all files
git add .

# Commit
git commit -m "Initial commit: Scouts Canada RAG System"

# Push to GitHub
git push origin main
```

## Step 4: Deploy to Your Server

### Prerequisites on Server:
- Docker and Docker Compose installed
- Qdrant running at 192.168.68.8:6333
- Ollama with required models

### Deployment Steps:

```bash
# Clone the repository
git clone https://github.com/yourusername/scouts-canada-rag.git
cd scouts-canada-rag

# Make scripts executable
chmod +x deploy-docker.sh build-production.sh

# Configure environment
cp .env.example .env
# Edit .env with your specific settings

# Deploy with Docker
./deploy-docker.sh
```

## Step 5: Verify Deployment

1. **Check System Status**: http://localhost:3000/settings
2. **Test Scraping**: http://localhost:3000/scraping
3. **Ask Questions**: http://localhost:3000

## Alternative: Quick Manual Setup

If you prefer not to use GitHub, you can manually create the files on your server:

```bash
# Create project directory
mkdir ~/scouts-canada-rag && cd ~/scouts-canada-rag

# Download files directly (you'll need to recreate them)
# Or use wget/curl if you have direct access to the files

# Then follow the deployment steps above
```

## Production Deployment

For production deployment with domain and SSL:

```bash
# Build for production
./build-production.sh

# Edit production config
nano .env.production

# Deploy with nginx reverse proxy
docker-compose --profile production up -d
```

## Updating the System

To update the system after making changes:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Or use the deploy script
./deploy-docker.sh
```

## Troubleshooting

### Common Issues:

1. **Permission Denied**: Make sure scripts are executable: `chmod +x *.sh`
2. **Docker Access**: Add user to docker group: `sudo usermod -aG docker $USER`
3. **Port Conflicts**: Check if ports 3000, 8001 are available
4. **External Services**: Verify Qdrant and Ollama are accessible

### Logs:
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Health Check:
```bash
# Check container status
docker-compose ps

# Test external connections
curl http://192.168.68.8:6333/collections  # Qdrant
curl http://localhost:11434/api/tags        # Ollama
```