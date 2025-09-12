#!/usr/bin/env python3
"""
Backend Test Suite for Digital Krishi Officer Multi-Agent System
Tests all backend functionality including agent coordination, translation, and database operations.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get backend URL from frontend .env file
def get_backend_url():
    """Get backend URL from frontend environment"""
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"  # fallback

BASE_URL = get_backend_url()
API_BASE_URL = f"{BASE_URL}/api"

print(f"Testing backend at: {API_BASE_URL}")

class KrishiOfficerTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.malayalam_queries = [
            {
                "text": "എന്റെ നെല്ല് വിളയിൽ പുഴുക്കൾ വന്നിട്ടുണ്ട്. എന്ത് ചെയ്യണം?",
                "description": "Rice crop has worms, what to do?",
                "expected_intent": "pest_disease"
            },
            {
                "text": "തെങ്ങിന് എന്ത് വളം ഇടണം?",
                "description": "What fertilizer for coconut?",
                "expected_intent": "crop_query"
            },
            {
                "text": "കുരുമുളകിന്റെ രോഗത്തിന് ചികിത്സ എന്താണ്?",
                "description": "Treatment for pepper disease?",
                "expected_intent": "pest_disease"
            }
        ]
    
    async def setup(self):
        """Setup test session"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
    
    async def test_health_check(self):
        """Test /api/health endpoint"""
        try:
            async with self.session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    required_fields = ["status", "service", "timestamp", "agents"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        self.log_test("Health Check", False, f"Missing fields: {missing_fields}", data)
                        return False
                    
                    # Verify agents are active
                    agents = data.get("agents", {})
                    expected_agents = ["translation", "query_understanding", "agriculture_advisor"]
                    inactive_agents = [agent for agent in expected_agents if agents.get(agent) != "active"]
                    
                    if inactive_agents:
                        self.log_test("Health Check", False, f"Inactive agents: {inactive_agents}", data)
                        return False
                    
                    self.log_test("Health Check", True, "All systems healthy", data)
                    return True
                else:
                    error_text = await response.text()
                    self.log_test("Health Check", False, f"HTTP {response.status}: {error_text}")
                    return False
                    
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False
    
    async def test_translation_endpoint(self):
        """Test /api/translate endpoint"""
        success_count = 0
        total_tests = len(self.malayalam_queries)
        
        for query in self.malayalam_queries:
            try:
                payload = {
                    "text": query["text"],
                    "source_lang": "ml",
                    "target_lang": "en"
                }
                
                async with self.session.post(
                    f"{API_BASE_URL}/translate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify response structure
                        required_fields = ["success", "original_text", "translated_text"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            self.log_test(f"Translation - {query['description']}", False, 
                                        f"Missing fields: {missing_fields}", data)
                            continue
                        
                        if data.get("success") and data.get("translated_text"):
                            self.log_test(f"Translation - {query['description']}", True, 
                                        f"Translated: '{data['translated_text']}'")
                            success_count += 1
                        else:
                            self.log_test(f"Translation - {query['description']}", False, 
                                        f"Translation failed: {data.get('error', 'Unknown error')}", data)
                    else:
                        error_text = await response.text()
                        self.log_test(f"Translation - {query['description']}", False, 
                                    f"HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                self.log_test(f"Translation - {query['description']}", False, f"Exception: {str(e)}")
        
        overall_success = success_count == total_tests
        self.log_test("Translation Endpoint Overall", overall_success, 
                     f"{success_count}/{total_tests} translations successful")
        return overall_success
    
    async def test_farmer_query_endpoint(self):
        """Test /api/farmer-query endpoint with multi-agent processing"""
        success_count = 0
        total_tests = len(self.malayalam_queries)
        query_ids = []
        
        for query in self.malayalam_queries:
            try:
                payload = {
                    "text": query["text"],
                    "query_type": "agricultural_support",
                    "location": "Kerala",
                    "farmer_id": f"test_farmer_{int(time.time())}"
                }
                
                async with self.session.post(
                    f"{API_BASE_URL}/farmer-query",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify response structure
                        required_fields = ["id", "original_text", "timestamp", "status"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            self.log_test(f"Farmer Query - {query['description']}", False, 
                                        f"Missing fields: {missing_fields}", data)
                            continue
                        
                        query_id = data.get("id")
                        if query_id:
                            query_ids.append(query_id)
                        
                        # Check if processing was successful
                        if data.get("status") == "completed":
                            # Verify agent responses
                            agent_responses = data.get("agent_responses", {})
                            expected_agents = ["translation", "analysis", "advice"]
                            
                            missing_agents = [agent for agent in expected_agents if agent not in agent_responses]
                            if missing_agents:
                                self.log_test(f"Farmer Query - {query['description']}", False, 
                                            f"Missing agent responses: {missing_agents}", data)
                                continue
                            
                            # Check translation
                            translation = agent_responses.get("translation", {})
                            if not translation.get("success"):
                                self.log_test(f"Farmer Query - {query['description']}", False, 
                                            "Translation agent failed", data)
                                continue
                            
                            # Check analysis
                            analysis = agent_responses.get("analysis", {})
                            detected_intent = analysis.get("intent")
                            confidence = analysis.get("confidence", 0)
                            
                            # Check advice
                            advice = agent_responses.get("advice", {})
                            if not advice.get("success"):
                                self.log_test(f"Farmer Query - {query['description']}", False, 
                                            "Agriculture advisor failed", data)
                                continue
                            
                            # Verify recommendations
                            recommendations = data.get("recommendations", [])
                            if not recommendations:
                                self.log_test(f"Farmer Query - {query['description']}", False, 
                                            "No recommendations provided", data)
                                continue
                            
                            self.log_test(f"Farmer Query - {query['description']}", True, 
                                        f"Intent: {detected_intent}, Confidence: {confidence:.2f}, "
                                        f"Recommendations: {len(recommendations)}")
                            success_count += 1
                            
                        elif data.get("status") == "error":
                            self.log_test(f"Farmer Query - {query['description']}", False, 
                                        f"Query processing failed with error status", data)
                        else:
                            self.log_test(f"Farmer Query - {query['description']}", False, 
                                        f"Unexpected status: {data.get('status')}", data)
                    else:
                        error_text = await response.text()
                        self.log_test(f"Farmer Query - {query['description']}", False, 
                                    f"HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                self.log_test(f"Farmer Query - {query['description']}", False, f"Exception: {str(e)}")
        
        overall_success = success_count == total_tests
        self.log_test("Farmer Query Endpoint Overall", overall_success, 
                     f"{success_count}/{total_tests} queries processed successfully")
        
        return overall_success, query_ids
    
    async def test_database_storage(self, query_ids: List[str]):
        """Test database storage by retrieving stored queries"""
        if not query_ids:
            self.log_test("Database Storage", False, "No query IDs to test")
            return False
        
        success_count = 0
        for query_id in query_ids:
            try:
                async with self.session.get(f"{API_BASE_URL}/queries/{query_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Verify stored data structure
                        required_fields = ["id", "original_text", "timestamp", "status"]
                        missing_fields = [field for field in required_fields if field not in data]
                        
                        if missing_fields:
                            self.log_test(f"Database Retrieval - {query_id}", False, 
                                        f"Missing fields: {missing_fields}", data)
                            continue
                        
                        if data.get("id") == query_id:
                            self.log_test(f"Database Retrieval - {query_id}", True, 
                                        f"Query stored and retrieved successfully")
                            success_count += 1
                        else:
                            self.log_test(f"Database Retrieval - {query_id}", False, 
                                        f"ID mismatch: expected {query_id}, got {data.get('id')}")
                    else:
                        error_text = await response.text()
                        self.log_test(f"Database Retrieval - {query_id}", False, 
                                    f"HTTP {response.status}: {error_text}")
                        
            except Exception as e:
                self.log_test(f"Database Retrieval - {query_id}", False, f"Exception: {str(e)}")
        
        overall_success = success_count == len(query_ids)
        self.log_test("Database Storage Overall", overall_success, 
                     f"{success_count}/{len(query_ids)} queries retrieved successfully")
        return overall_success
    
    async def test_error_handling(self):
        """Test error handling with invalid inputs"""
        test_cases = [
            {
                "name": "Empty Translation Request",
                "endpoint": "/translate",
                "payload": {"text": "", "source_lang": "ml", "target_lang": "en"},
                "expected_status": [200, 400]  # Either handled gracefully or rejected
            },
            {
                "name": "Invalid Farmer Query",
                "endpoint": "/farmer-query", 
                "payload": {"text": ""},
                "expected_status": [200, 400, 422]  # Validation error expected
            },
            {
                "name": "Non-existent Query ID",
                "endpoint": "/queries/non-existent-id",
                "method": "GET",
                "expected_status": [404]
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            try:
                url = f"{API_BASE_URL}{test_case['endpoint']}"
                method = test_case.get("method", "POST")
                
                if method == "GET":
                    async with self.session.get(url) as response:
                        if response.status in test_case["expected_status"]:
                            self.log_test(f"Error Handling - {test_case['name']}", True, 
                                        f"Correctly returned HTTP {response.status}")
                            success_count += 1
                        else:
                            error_text = await response.text()
                            self.log_test(f"Error Handling - {test_case['name']}", False, 
                                        f"Unexpected status {response.status}: {error_text}")
                else:
                    async with self.session.post(
                        url,
                        json=test_case["payload"],
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status in test_case["expected_status"]:
                            self.log_test(f"Error Handling - {test_case['name']}", True, 
                                        f"Correctly returned HTTP {response.status}")
                            success_count += 1
                        else:
                            error_text = await response.text()
                            self.log_test(f"Error Handling - {test_case['name']}", False, 
                                        f"Unexpected status {response.status}: {error_text}")
                            
            except Exception as e:
                self.log_test(f"Error Handling - {test_case['name']}", False, f"Exception: {str(e)}")
        
        overall_success = success_count == len(test_cases)
        self.log_test("Error Handling Overall", overall_success, 
                     f"{success_count}/{len(test_cases)} error cases handled correctly")
        return overall_success
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 80)
        print("DIGITAL KRISHI OFFICER BACKEND TEST SUITE")
        print("=" * 80)
        print(f"Testing backend at: {API_BASE_URL}")
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        await self.setup()
        
        try:
            # Test 1: Health Check
            print("1. Testing Health Check Endpoint...")
            health_ok = await self.test_health_check()
            print()
            
            # Test 2: Translation
            print("2. Testing Translation Functionality...")
            translation_ok = await self.test_translation_endpoint()
            print()
            
            # Test 3: Multi-Agent Query Processing
            print("3. Testing Multi-Agent Query Processing...")
            query_ok, query_ids = await self.test_farmer_query_endpoint()
            print()
            
            # Test 4: Database Storage
            print("4. Testing Database Storage...")
            db_ok = await self.test_database_storage(query_ids)
            print()
            
            # Test 5: Error Handling
            print("5. Testing Error Handling...")
            error_ok = await self.test_error_handling()
            print()
            
            # Summary
            print("=" * 80)
            print("TEST SUMMARY")
            print("=" * 80)
            
            total_tests = 5
            passed_tests = sum([health_ok, translation_ok, query_ok, db_ok, error_ok])
            
            print(f"Health Check: {'✅ PASS' if health_ok else '❌ FAIL'}")
            print(f"Translation: {'✅ PASS' if translation_ok else '❌ FAIL'}")
            print(f"Multi-Agent Processing: {'✅ PASS' if query_ok else '❌ FAIL'}")
            print(f"Database Storage: {'✅ PASS' if db_ok else '❌ FAIL'}")
            print(f"Error Handling: {'✅ PASS' if error_ok else '❌ FAIL'}")
            print()
            print(f"Overall: {passed_tests}/{total_tests} test suites passed")
            
            if passed_tests == total_tests:
                print("🎉 ALL TESTS PASSED! Backend is working correctly.")
            else:
                print("⚠️  Some tests failed. Check details above.")
            
            return passed_tests == total_tests
            
        finally:
            await self.cleanup()

async def main():
    """Main test runner"""
    tester = KrishiOfficerTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)