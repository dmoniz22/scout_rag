#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Scouts Canada RAG System
Tests all API endpoints using the public URL
"""

import requests
import sys
import time
import json
from datetime import datetime

class ScoutsRAGAPITester:
    def __init__(self, base_url="https://scout-buddy.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.job_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def test_health_check(self):
        """Test the root health check endpoint"""
        try:
            response = requests.get(f"{self.api_url}/", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                data = response.json()
                details += f", Response: {data.get('message', 'No message')}"
            return self.log_test("Health Check", success, details)
        except Exception as e:
            return self.log_test("Health Check", False, f"Error: {str(e)}")

    def test_start_scraping(self):
        """Test starting a scraping job"""
        try:
            response = requests.post(f"{self.api_url}/scrape/start", timeout=30)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                self.job_id = data.get('job_id')
                details += f", Job ID: {self.job_id}, Status: {data.get('status')}"
            
            return self.log_test("Start Scraping", success, details)
        except Exception as e:
            return self.log_test("Start Scraping", False, f"Error: {str(e)}")

    def test_scraping_status(self):
        """Test getting scraping job status"""
        if not self.job_id:
            return self.log_test("Scraping Status", False, "No job ID available")
        
        try:
            response = requests.get(f"{self.api_url}/scrape/status/{self.job_id}", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Job Status: {data.get('status')}, URLs: {data.get('urls_processed', 0)}, Docs: {data.get('documents_processed', 0)}"
            
            return self.log_test("Scraping Status", success, details)
        except Exception as e:
            return self.log_test("Scraping Status", False, f"Error: {str(e)}")

    def test_list_scraping_jobs(self):
        """Test listing all scraping jobs"""
        try:
            response = requests.get(f"{self.api_url}/scrape/jobs", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Jobs found: {len(data)}"
                if data:
                    latest_job = data[-1]
                    details += f", Latest job status: {latest_job.get('status')}"
            
            return self.log_test("List Scraping Jobs", success, details)
        except Exception as e:
            return self.log_test("List Scraping Jobs", False, f"Error: {str(e)}")

    def test_document_status(self):
        """Test getting document database status"""
        try:
            response = requests.get(f"{self.api_url}/documents/status", timeout=10)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                data = response.json()
                details += f", Total docs: {data.get('total_documents', 0)}, Collection size: {data.get('collection_size', 0)}"
                if data.get('last_updated'):
                    details += f", Last updated: {data.get('last_updated')}"
            
            return self.log_test("Document Status", success, details)
        except Exception as e:
            return self.log_test("Document Status", False, f"Error: {str(e)}")

    def test_query_system(self):
        """Test querying the RAG system"""
        test_questions = [
            "What is Scouts Canada?",
            "How do I join Scouts?",
            "What are the different sections in Scouting?"
        ]
        
        for question in test_questions:
            try:
                payload = {
                    "question": question,
                    "max_results": 5
                }
                response = requests.post(f"{self.api_url}/query", json=payload, timeout=60)
                success = response.status_code == 200
                details = f"Status: {response.status_code}, Question: '{question}'"
                
                if success:
                    data = response.json()
                    answer_length = len(data.get('answer', ''))
                    sources_count = len(data.get('sources', []))
                    processing_time = data.get('processing_time', 0)
                    details += f", Answer length: {answer_length}, Sources: {sources_count}, Time: {processing_time:.2f}s"
                
                self.log_test(f"Query System - {question[:30]}...", success, details)
                
                # Only test one question if we get a successful response
                if success:
                    break
                    
            except Exception as e:
                self.log_test(f"Query System - {question[:30]}...", False, f"Error: {str(e)}")

    def wait_for_scraping_completion(self, max_wait_time=300):
        """Wait for scraping job to complete or timeout"""
        if not self.job_id:
            print("⏳ No job ID to monitor")
            return False
            
        print(f"⏳ Monitoring scraping job {self.job_id} (max wait: {max_wait_time}s)...")
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(f"{self.api_url}/scrape/status/{self.job_id}", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    urls = data.get('urls_processed', 0)
                    docs = data.get('documents_processed', 0)
                    
                    print(f"⏳ Status: {status}, URLs: {urls}, Docs: {docs}")
                    
                    if status in ['completed', 'failed']:
                        if status == 'completed':
                            print(f"✅ Scraping completed! Processed {docs} documents from {urls} URLs")
                            return True
                        else:
                            error_msg = data.get('error_message', 'Unknown error')
                            print(f"❌ Scraping failed: {error_msg}")
                            return False
                
                time.sleep(10)  # Wait 10 seconds between checks
                
            except Exception as e:
                print(f"⚠️ Error checking status: {e}")
                time.sleep(10)
        
        print(f"⏰ Timeout reached after {max_wait_time}s")
        return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Scouts Canada RAG API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity tests
        self.test_health_check()
        
        # Document status (should work even without data)
        self.test_document_status()
        
        # Scraping tests
        self.test_start_scraping()
        self.test_scraping_status()
        self.test_list_scraping_jobs()
        
        # Wait a bit for scraping to potentially process some data
        print("\n⏳ Waiting 30 seconds for scraping to process some data...")
        time.sleep(30)
        
        # Check status again
        self.test_scraping_status()
        self.test_document_status()
        
        # Test query system (may fail if no documents are processed yet)
        print("\n🔍 Testing query system...")
        self.test_query_system()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️ Some tests failed. Check the logs above for details.")
            return 1

def main():
    """Main test execution"""
    tester = ScoutsRAGAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())