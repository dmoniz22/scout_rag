# Scouts Canada RAG System

An intelligent document retrieval and question-answering system for Scouts Canada documentation using RAG (Retrieval-Augmented Generation) architecture.

## Features

- 🔍 **Intelligent Q&A**: Ask questions about Scouts Canada and get accurate answers with source citations
- 🕷️ **Web Scraping**: Automatically scrapes scouts.ca website including downloadable documents
- 📄 **OCR Processing**: Extracts text from images and PDFs using advanced OCR
- 🧠 **Vector Search**: Semantic search using Qdrant vector database and Ollama embeddings
- 🤖 **LLM Integration**: Powered by Ollama's llama3.1:8b for answer generation
- ⏰ **Automated Updates**: Weekly scraping schedule (Sundays at 2:00 AM)
- 📊 **Management Interface**: Web UI for monitoring scraping jobs and database status
- 🏥 **Health Monitoring**: Real-time system status and dependency health checks

## Architecture

- **Backend**: FastAPI with async processing
- **Frontend**: React with modern UI components
- **Vector Database**: Qdrant for semantic search
- **LLM**: Ollama (llama3.1:8b + nomic-embed-text)
- **Database**: MongoDB for metadata and job tracking
- **OCR**: Tesseract for image text extraction

## Quick Start with Docker

### Prerequisites

1. **Docker and Docker Compose** installed
2. **Qdrant** running at `192.168.68.8:6333`
3. **Ollama** running locally with models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```

### Deployment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd scouts-canada-rag
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your specific configuration
   ```

3. **Start the services**:
   ```bash
   # Development mode
   docker-compose up -d
   
   # Production mode with nginx
   docker-compose --profile production up -d
   ```

4. **Access the application**:
   - **Web Interface**: http://localhost:3000
   - **API Documentation**: http://localhost:8001/docs
   - **System Status**: http://localhost:3000/settings

### Configuration

Edit the `.env` file to match your setup:

```env
# External Services
QDRANT_HOST=192.168.68.8  # Your Qdrant server IP
QDRANT_PORT=6333
OLLAMA_HOST=host.docker.internal  # Access host Ollama from container
OLLAMA_PORT=11434

# Application
REACT_APP_BACKEND_URL=http://localhost:8001
```

## Usage

1. **System Status**: Check `/settings` to verify all services are healthy
2. **Start Scraping**: Go to `/scraping` and click "Start New Scraping"
3. **Ask Questions**: Use the main interface to query the documentation
4. **Monitor Progress**: Track scraping jobs and database growth

## Automatic Scraping

The system automatically scrapes scouts.ca every Sunday at 2:00 AM. You can also trigger manual scraping through the web interface.

## Development

### Local Development Setup

1. **Backend**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn server:app --reload --port 8001
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

### API Endpoints

- `GET /api/` - Health check
- `POST /api/scrape/start` - Start scraping job
- `GET /api/scrape/jobs` - List scraping jobs
- `POST /api/query` - Query the RAG system
- `GET /api/documents/status` - Database status
- `GET /api/system/status` - System health check

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**:
   - Verify Qdrant is running: `curl http://192.168.68.8:6333/collections`
   - Check firewall settings
   - Update QDRANT_HOST in .env

2. **Ollama Not Responding**:
   - Verify Ollama is running: `ollama list`
   - Check models are installed: `ollama pull llama3.1:8b && ollama pull nomic-embed-text`
   - Verify Docker can access host: `docker run --rm busybox nslookup host.docker.internal`

3. **Scraping Jobs Failing**:
   - Check system status in `/settings`
   - Review job error messages in `/scraping`
   - Verify external service connectivity

### Logs

View container logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]
