from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
import uuid
import logging
import asyncio
import aiohttp
import json
from pathlib import Path
from dotenv import load_dotenv

# New imports for RAG system
import requests
from bs4 import BeautifulSoup
import tempfile
import fitz  # PyMuPDF for PDF processing
import pytesseract
from PIL import Image
import io
import re
from urllib.parse import urljoin, urlparse
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from apscheduler.schedulers.background import BackgroundScheduler
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB and Qdrant connections
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Qdrant client
qdrant_client = QdrantClient(host="192.168.68.8", port=6333)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

# Create the main app
app = FastAPI(title="Scouts Canada RAG System", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Initialize scheduler
scheduler = BackgroundScheduler()

# Pydantic Models
class ScrapingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    urls_processed: int = 0
    documents_processed: int = 0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QueryRequest(BaseModel):
    question: str
    max_results: int = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    processing_time: float

class DocumentStatus(BaseModel):
    total_documents: int
    last_updated: Optional[datetime]
    collection_size: int

# Global variables for tracking
scraping_jobs = {}
last_scrape_time = None

# Utility Functions
async def get_ollama_embedding(text: str) -> List[float]:
    """Generate embeddings using Ollama's nomic-embed-text model"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "nomic-embed-text",
                "prompt": text
            }
            async with session.post(f"{OLLAMA_BASE_URL}/api/embeddings", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["embedding"]
                else:
                    logger.error(f"Ollama embedding failed: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []

async def query_ollama_llm(prompt: str, model: str = "llama3.1:8b") -> str:
    """Query Ollama LLM for text generation"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            async with session.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["response"]
                else:
                    logger.error(f"Ollama LLM query failed: {response.status}")
                    return ""
    except Exception as e:
        logger.error(f"Error querying LLM: {e}")
        return ""

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using PyMuPDF"""
    try:
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        return ""

def perform_ocr(image_content: bytes) -> str:
    """Perform OCR on image content"""
    try:
        image = Image.open(io.BytesIO(image_content))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            if break_point > start + chunk_size // 2:
                chunk = text[start:break_point + 1]
                end = break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
        
    return chunks

async def scrape_scouts_website(job_id: str):
    """Main scraping function for Scouts Canada website"""
    global scraping_jobs
    
    job = scraping_jobs[job_id]
    job.status = "running"
    job.start_time = datetime.now(timezone.utc)
    
    try:
        # Check Qdrant connection first
        collection_name = "scouts_canada_docs"
        try:
            qdrant_client.get_collection(collection_name)
            logger.info("Qdrant connection successful")
        except Exception as e:
            logger.error(f"Cannot connect to Qdrant: {e}")
            try:
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info("Created new Qdrant collection")
            except Exception as create_error:
                job.status = "failed"
                job.error_message = f"Cannot connect to Qdrant vector database at 192.168.68.8:6333. Please ensure Qdrant is running. Error: {str(create_error)}"
                job.end_time = datetime.now(timezone.utc)
                logger.error(f"Failed to create Qdrant collection: {create_error}")
                return
        
        base_url = "https://scouts.ca"
        visited_urls = set()
        urls_to_visit = [base_url]
        documents_processed = 0
        
        async with aiohttp.ClientSession() as session:
            while urls_to_visit and len(visited_urls) < 1000:  # Limit for demo
                current_url = urls_to_visit.pop(0)
                if current_url in visited_urls:
                    continue
                    
                visited_urls.add(current_url)
                logger.info(f"Processing: {current_url}")
                
                try:
                    async with session.get(current_url, timeout=30) as response:
                        if response.status != 200:
                            continue
                            
                        content_type = response.headers.get('content-type', '').lower()
                        content = await response.read()
                        
                        if 'text/html' in content_type:
                            # Process HTML content
                            soup = BeautifulSoup(content, 'html.parser')
                            
                            # Extract text content
                            text_content = soup.get_text(separator=' ', strip=True)
                            
                            # Find more links to scrape
                            for link in soup.find_all('a', href=True):
                                full_url = urljoin(current_url, link['href'])
                                if 'scouts.ca' in full_url and full_url not in visited_urls:
                                    urls_to_visit.append(full_url)
                            
                            # Find downloadable documents
                            for link in soup.find_all('a', href=True):
                                href = link['href']
                                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx']):
                                    doc_url = urljoin(current_url, href)
                                    try:
                                        async with session.get(doc_url, timeout=30) as doc_response:
                                            if doc_response.status == 200:
                                                doc_content = await doc_response.read()
                                                if '.pdf' in href.lower():
                                                    doc_text = extract_text_from_pdf(doc_content)
                                                    text_content += f"\n\nDocument: {doc_url}\n{doc_text}"
                                    except Exception as e:
                                        logger.error(f"Failed to process document {doc_url}: {e}")
                        
                        elif 'application/pdf' in content_type:
                            # Process PDF directly
                            text_content = extract_text_from_pdf(content)
                        
                        elif any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/tiff']):
                            # Process image with OCR
                            text_content = perform_ocr(content)
                        
                        else:
                            continue
                        
                        # Process and store the content
                        if text_content and len(text_content.strip()) > 100:
                            chunks = chunk_text(text_content)
                            
                            for i, chunk in enumerate(chunks):
                                # Generate embedding
                                embedding = await get_ollama_embedding(chunk)
                                if embedding:
                                    # Create unique ID for this chunk
                                    chunk_id = hashlib.md5(f"{current_url}_{i}_{chunk[:100]}".encode()).hexdigest()
                                    
                                    # Store in Qdrant
                                    point = PointStruct(
                                        id=chunk_id,
                                        vector=embedding,
                                        payload={
                                            "text": chunk,
                                            "url": current_url,
                                            "chunk_index": i,
                                            "scraped_at": datetime.now(timezone.utc).isoformat(),
                                            "content_type": content_type
                                        }
                                    )
                                    
                                    qdrant_client.upsert(
                                        collection_name=collection_name,
                                        points=[point]
                                    )
                            
                            documents_processed += 1
                            job.documents_processed = documents_processed
                            job.urls_processed = len(visited_urls)
                    
                except Exception as e:
                    logger.error(f"Error processing {current_url}: {e}")
                    continue
        
        job.status = "completed"
        job.end_time = datetime.now(timezone.utc)
        global last_scrape_time
        last_scrape_time = job.end_time
        
        logger.info(f"Scraping completed. Processed {documents_processed} documents from {len(visited_urls)} URLs")
        
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        job.end_time = datetime.now(timezone.utc)
        logger.error(f"Scraping failed: {e}")

# API Endpoints
@api_router.post("/scrape/start")
async def start_scraping(background_tasks: BackgroundTasks):
    """Start a new scraping job"""
    job_id = str(uuid.uuid4())
    job = ScrapingJob(id=job_id)
    scraping_jobs[job_id] = job
    
    # Run scraping in background
    background_tasks.add_task(scrape_scouts_website, job_id)
    
    return {"job_id": job_id, "status": "started"}

@api_router.get("/scrape/status/{job_id}")
async def get_scraping_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in scraping_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return scraping_jobs[job_id]

@api_router.get("/scrape/jobs")
async def list_scraping_jobs():
    """List all scraping jobs"""
    return list(scraping_jobs.values())

@api_router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system"""
    start_time = datetime.now()
    
    try:
        # Check Qdrant connection
        try:
            collection_info = qdrant_client.get_collection("scouts_canada_docs")
            if collection_info.points_count == 0:
                return QueryResponse(
                    answer="The document database is empty. Please run a scraping job first to populate the database with Scouts Canada documentation.",
                    sources=[],
                    processing_time=(datetime.now() - start_time).total_seconds()
                )
        except Exception as e:
            logger.error(f"Qdrant connection failed: {e}")
            return QueryResponse(
                answer="I'm unable to connect to the document database. Please ensure Qdrant is running at 192.168.68.8:6333 and try again.",
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Generate embedding for the query
        query_embedding = await get_ollama_embedding(request.question)
        if not query_embedding:
            return QueryResponse(
                answer="I'm unable to connect to the embedding service (Ollama). Please ensure Ollama is running with the nomic-embed-text model at localhost:11434.",
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Search Qdrant for similar documents
        search_results = qdrant_client.search(
            collection_name="scouts_canada_docs",
            query_vector=query_embedding,
            limit=request.max_results
        )
        
        if not search_results:
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                processing_time=(datetime.now() - start_time).total_seconds()
            )
        
        # Prepare context from search results
        context_chunks = []
        sources = []
        
        for result in search_results:
            context_chunks.append(result.payload["text"])
            sources.append({
                "url": result.payload["url"],
                "score": result.score,
                "chunk_index": result.payload.get("chunk_index", 0),
                "content_type": result.payload.get("content_type", ""),
                "scraped_at": result.payload.get("scraped_at", "")
            })
        
        context = "\n\n".join(context_chunks)
        
        # Generate response using LLM
        prompt = f"""Based on the following context from Scouts Canada documentation, please provide a comprehensive and accurate answer to the question. Include relevant details and be specific.

Context:
{context}

Question: {request.question}

Please provide a clear, concise answer based on the information provided. If the context doesn't contain enough information to fully answer the question, please indicate that and answer what you can based on the available information."""
        
        answer = await query_ollama_llm(prompt)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@api_router.get("/documents/status", response_model=DocumentStatus)
async def get_document_status():
    """Get status of the document database"""
    try:
        collection_info = qdrant_client.get_collection("scouts_canada_docs")
        return DocumentStatus(
            total_documents=collection_info.points_count,
            last_updated=last_scrape_time,
            collection_size=collection_info.points_count
        )
    except:
        return DocumentStatus(
            total_documents=0,
            last_updated=None,
            collection_size=0
        )

@api_router.delete("/documents/clear")
async def clear_documents():
    """Clear all documents from the database"""
    try:
        qdrant_client.delete_collection("scouts_canada_docs")
        return {"message": "Document database cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear documents")

@api_router.get("/")
async def root():
    return {"message": "Scouts Canada RAG System API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Weekly scraping scheduler
def schedule_weekly_scraping():
    """Schedule weekly scraping job"""
    logger.info("Starting scheduled weekly scraping")
    job_id = str(uuid.uuid4())
    job = ScrapingJob(id=job_id)
    scraping_jobs[job_id] = job
    asyncio.create_task(scrape_scouts_website(job_id))

# Start scheduler
scheduler.add_job(
    schedule_weekly_scraping,
    'cron',
    day_of_week='sun',
    hour=2,
    minute=0,
    id='weekly_scraping'
)
scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    client.close()
    scheduler.shutdown()