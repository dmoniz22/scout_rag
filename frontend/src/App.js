import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Search, Database, Activity, Settings as SettingsIcon, FileText, Loader2, AlertCircle, CheckCircle, Clock, ExternalLink } from 'lucide-react';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Alert, AlertDescription } from './components/ui/alert';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  const navItems = [
    { path: '/', icon: Search, label: 'Query' },
    { path: '/scraping', icon: Activity, label: 'Scraping' },
    { path: '/database', icon: Database, label: 'Database' },
    { path: '/settings', icon: Settings, label: 'Settings' }
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="w-8 h-8 text-blue-600" />
          <h1 className="text-2xl font-bold text-gray-900">Scouts Canada RAG</h1>
        </div>
        
        <div className="flex space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.path} to={item.path}>
                <Button
                  variant={location.pathname === item.path ? "default" : "ghost"}
                  className="flex items-center space-x-2"
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Button>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

// Query Interface Component
const QueryInterface = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingTime, setProcessingTime] = useState(0);

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    
    setLoading(true);
    setAnswer('');
    setSources([]);
    
    try {
      const response = await axios.post(`${API}/query`, {
        question: question.trim(),
        max_results: 5
      });
      
      setAnswer(response.data.answer);
      setSources(response.data.sources);
      setProcessingTime(response.data.processing_time);
    } catch (error) {
      console.error('Query failed:', error);
      setAnswer('Sorry, I encountered an error while processing your question. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-gray-900">Ask about Scouts Canada</h2>
        <p className="text-gray-600">Get instant answers from the official Scouts Canada documentation</p>
      </div>
      
      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleQuery} className="space-y-4">
            <div className="flex space-x-4">
              <Input
                placeholder="Ask your question about Scouts Canada..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="flex-1"
                disabled={loading}
              />
              <Button type="submit" disabled={loading || !question.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Ask
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      
      {answer && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Answer
              {processingTime > 0 && (
                <Badge variant="secondary">
                  {processingTime.toFixed(2)}s
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose max-w-none">
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">{answer}</p>
            </div>
          </CardContent>
        </Card>
      )}
      
      {sources.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sources</CardTitle>
            <CardDescription>
              Here are the sources used to generate this answer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sources.map((source, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-800 font-medium flex items-center space-x-1"
                    >
                      <span className="truncate">{source.url}</span>
                      <ExternalLink className="w-4 h-4 flex-shrink-0" />
                    </a>
                    <Badge variant="outline">
                      Score: {(source.score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  <div className="text-sm text-gray-500">
                    Content Type: {source.content_type} | Chunk: {source.chunk_index + 1}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Scraping Management Component
const ScrapingManager = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/scrape/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    }
  };

  const startScraping = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/scrape/start`);
      console.log('Scraping started:', response.data);
      fetchJobs();
    } catch (error) {
      console.error('Failed to start scraping:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Scraping Management</h2>
          <p className="text-gray-600">Monitor and manage website scraping jobs</p>
        </div>
        <Button onClick={startScraping} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Starting...
            </>
          ) : (
            <>
              <Activity className="w-4 h-4 mr-2" />
              Start New Scraping
            </>
          )}
        </Button>
      </div>

      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Scraping is automatically scheduled to run weekly on Sundays at 2:00 AM. 
          You can also manually start a scraping job using the button above.
        </AlertDescription>
      </Alert>

      <div className="space-y-4">
        {jobs.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">No scraping jobs found. Start your first scraping job above.</p>
            </CardContent>
          </Card>
        ) : (
          jobs.map((job) => (
            <Card key={job.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center space-x-2">
                    {getStatusIcon(job.status)}
                    <span>Job {job.id.slice(0, 8)}</span>
                  </CardTitle>
                  <Badge className={getStatusColor(job.status)}>
                    {job.status.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Started</p>
                    <p className="text-sm text-gray-900">
                      {job.start_time ? new Date(job.start_time).toLocaleString() : 'Not started'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">URLs Processed</p>
                    <p className="text-sm text-gray-900">{job.urls_processed}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Documents</p>
                    <p className="text-sm text-gray-900">{job.documents_processed}</p>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-500">Duration</p>
                    <p className="text-sm text-gray-900">
                      {job.start_time && job.end_time
                        ? `${Math.round((new Date(job.end_time) - new Date(job.start_time)) / 1000)}s`
                        : job.start_time
                        ? `${Math.round((new Date() - new Date(job.start_time)) / 1000)}s`
                        : 'N/A'}
                    </p>
                  </div>
                </div>
                {job.error_message && (
                  <div className="mt-4">
                    <Alert>
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Error:</strong> {job.error_message}
                      </AlertDescription>
                    </Alert>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

// Database Management Component
const DatabaseManager = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API}/documents/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch database status:', error);
    } finally {
      setLoading(false);
    }
  };

  const clearDatabase = async () => {
    if (window.confirm('Are you sure you want to clear all documents? This action cannot be undone.')) {
      try {
        await axios.delete(`${API}/documents/clear`);
        alert('Database cleared successfully');
        fetchStatus();
      } catch (error) {
        console.error('Failed to clear database:', error);
        alert('Failed to clear database');
      }
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Database Management</h2>
        <p className="text-gray-600">Monitor and manage the document vector database</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Database className="w-5 h-5" />
              <span>Total Documents</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">
              {status?.total_documents || 0}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span>Last Updated</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              {status?.last_updated
                ? new Date(status.last_updated).toLocaleString()
                : 'Never'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Collection Size</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600">
              {status?.collection_size || 0} vectors
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-red-600">Danger Zone</CardTitle>
          <CardDescription>
            Irreversible and destructive actions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            variant="destructive"
            onClick={clearDatabase}
            className="w-full"
          >
            Clear All Documents
          </Button>
          <p className="text-sm text-gray-500 mt-2">
            This will permanently delete all documents from the vector database.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// Settings Component
const Settings = () => {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Settings</h2>
        <p className="text-gray-600">Configuration and system information</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-500">Ollama Models</p>
              <p className="text-sm text-gray-900">llama3.1:8b, nomic-embed-text</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Vector Database</p>
              <p className="text-sm text-gray-900">Qdrant (192.168.68.8:6333)</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Scraping Schedule</p>
              <p className="text-sm text-gray-900">Weekly (Sundays at 2:00 AM)</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Target Website</p>
              <p className="text-sm text-gray-900">https://scouts.ca</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Features</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">Web scraping with document download</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">OCR for image-based documents</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">PDF text extraction</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">Semantic search with embeddings</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">LLM-powered answer generation</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm">Automated weekly updates</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <BrowserRouter>
        <Navigation />
        <main className="py-8">
          <Routes>
            <Route path="/" element={<QueryInterface />} />
            <Route path="/scraping" element={<ScrapingManager />} />
            <Route path="/database" element={<DatabaseManager />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </BrowserRouter>
    </div>
  );
}

export default App;