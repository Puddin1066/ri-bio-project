"""
Unit tests for the Flask application and DataAgent
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock environment variables before importing app
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    from app import app, DataAgent


class TestDataAgent(unittest.TestCase):
    """Test the DataAgent class"""
    
    def setUp(self):
        self.agent = DataAgent()
    
    def test_initialization(self):
        """Test that DataAgent initializes correctly"""
        self.assertIsNotNone(self.agent.client)
        self.assertIsNotNone(self.agent.real_estate_scraper)
        self.assertIsNotNone(self.agent.owner_scraper)
        self.assertIsNotNone(self.agent.market_scraper)
        self.assertIsNotNone(self.agent.system_prompt)
    
    @patch('app.openai.OpenAI')
    def test_process_query_real_estate(self, mock_openai):
        """Test processing a real estate query"""
        # Mock OpenAI response for intent analysis
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "data_sources": ["real_estate"],
            "query_type": "high_value_transactions",
            "parameters": {
                "zip_code": "90210",
                "min_price": "25000000"
            },
            "specific_request": "Find properties over $25M"
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        self.agent.client = mock_client
        
        # Test query
        result = self.agent.process_query("Who bought houses over $25M in Beverly Hills?")
        
        self.assertIsInstance(result, dict)
        self.assertIn('response', result)
    
    @patch('app.openai.OpenAI')
    def test_process_query_edgar(self, mock_openai):
        """Test processing an EDGAR query"""
        # Mock OpenAI response for intent analysis
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "data_sources": ["edgar"],
            "query_type": "company_filings",
            "parameters": {
                "company": "Tesla",
                "ticker": "TSLA"
            },
            "specific_request": "Get Tesla's latest filings"
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        self.agent.client = mock_client
        
        # Test query
        result = self.agent.process_query("Show me Tesla's latest 10-K filing")
        
        self.assertIsInstance(result, dict)
        self.assertIn('response', result)
    
    def test_extract_zip_from_location(self):
        """Test location to zip code mapping"""
        # Test known locations
        self.assertEqual(self.agent._extract_zip_from_location('manhattan'), '10021')
        self.assertEqual(self.agent._extract_zip_from_location('beverly hills'), '90210')
        self.assertEqual(self.agent._extract_zip_from_location('palo alto'), '94301')
        
        # Test unknown location (should default)
        self.assertEqual(self.agent._extract_zip_from_location('unknown city'), '90210')
    
    def test_query_real_estate(self):
        """Test real estate data querying"""
        intent_data = {
            "parameters": {
                "zip_code": "90210",
                "min_price": 25000000
            }
        }
        
        result = self.agent.query_real_estate(intent_data)
        
        self.assertIsInstance(result, dict)
        if 'transactions' in result:
            self.assertIsInstance(result['transactions'], list)
    
    @patch('requests.get')
    def test_query_edgar(self, mock_get):
        """Test EDGAR API querying"""
        # Mock EDGAR API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "0": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla Inc"}
        }
        mock_get.return_value = mock_response
        
        intent_data = {
            "parameters": {
                "company": "Tesla",
                "ticker": "TSLA"
            }
        }
        
        result = self.agent.query_edgar(intent_data)
        
        self.assertIsInstance(result, dict)
    
    def test_format_real_estate_transactions(self):
        """Test formatting real estate data for frontend"""
        real_estate_data = {
            "transactions": [
                {
                    "address": "123 Test St",
                    "price": 30000000,
                    "sale_date": "2024-01-15",
                    "buyer": "Test Buyer",
                    "sqft": 5000
                }
            ]
        }
        
        result = self.agent.format_real_estate_transactions(real_estate_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'table')
        self.assertIn('content', result)
        self.assertIn('headers', result['content'])
        self.assertIn('rows', result['content'])
    
    def test_format_financial_data(self):
        """Test formatting EDGAR financial data"""
        edgar_data = {
            "company_facts": {
                "facts": {
                    "us-gaap": {
                        "Assets": {
                            "units": {
                                "USD": [
                                    {"val": 100000000, "end": "2023-12-31"}
                                ]
                            }
                        }
                    }
                }
            }
        }
        
        result = self.agent.format_financial_data(edgar_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'metrics')
        self.assertIn('content', result)


class TestFlaskApp(unittest.TestCase):
    """Test the Flask application endpoints"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test the index route"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('services', data)
    
    @patch('app.data_agent.process_query')
    def test_chat_endpoint_success(self, mock_process):
        """Test successful chat endpoint"""
        # Mock successful response
        mock_process.return_value = {
            "response": "Test response",
            "data": None
        }
        
        response = self.app.post('/api/chat', 
                               data=json.dumps({"message": "Test query"}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
        self.assertEqual(data['response'], 'Test response')
    
    def test_chat_endpoint_empty_message(self):
        """Test chat endpoint with empty message"""
        response = self.app.post('/api/chat', 
                               data=json.dumps({"message": ""}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
    
    def test_chat_endpoint_no_message(self):
        """Test chat endpoint without message field"""
        response = self.app.post('/api/chat', 
                               data=json.dumps({}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('response', data)
    
    @patch('app.data_agent.process_query')
    def test_chat_endpoint_error(self, mock_process):
        """Test chat endpoint error handling"""
        # Mock an exception
        mock_process.side_effect = Exception("Test error")
        
        response = self.app.post('/api/chat', 
                               data=json.dumps({"message": "Test query"}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('response', data)


class TestQueryParsing(unittest.TestCase):
    """Test query parsing and parameter extraction"""
    
    def setUp(self):
        self.agent = DataAgent()
    
    def test_price_string_parsing(self):
        """Test parsing of price strings"""
        # Test various price formats in query_real_estate
        intent_data_25m = {"parameters": {"min_price": "25M"}}
        intent_data_50million = {"parameters": {"min_price": "50 million"}}
        intent_data_numeric = {"parameters": {"min_price": "30000000"}}
        
        # These should not crash
        result1 = self.agent.query_real_estate(intent_data_25m)
        result2 = self.agent.query_real_estate(intent_data_50million)
        result3 = self.agent.query_real_estate(intent_data_numeric)
        
        self.assertIsInstance(result1, dict)
        self.assertIsInstance(result2, dict)
        self.assertIsInstance(result3, dict)
    
    def test_location_parameter_handling(self):
        """Test handling of location parameters"""
        # Test with zip code
        intent_data_zip = {"parameters": {"zip_code": "90210"}}
        result = self.agent.query_real_estate(intent_data_zip)
        self.assertIsInstance(result, dict)
        
        # Test with location name
        intent_data_location = {"parameters": {"location": "Manhattan"}}
        result = self.agent.query_real_estate(intent_data_location)
        self.assertIsInstance(result, dict)
        
        # Test with both (zip code should take precedence)
        intent_data_both = {"parameters": {"zip_code": "90210", "location": "Manhattan"}}
        result = self.agent.query_real_estate(intent_data_both)
        self.assertIsInstance(result, dict)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency"""
    
    def setUp(self):
        self.agent = DataAgent()
    
    def test_real_estate_data_structure(self):
        """Test that real estate queries return consistent data structure"""
        intent_data = {
            "parameters": {
                "zip_code": "90210",
                "min_price": 25000000
            }
        }
        
        result = self.agent.query_real_estate(intent_data)
        
        # Check top-level structure
        self.assertIsInstance(result, dict)
        
        # If transactions exist, check their structure
        if 'transactions' in result and result['transactions']:
            for transaction in result['transactions']:
                required_fields = ['address', 'price', 'sale_date', 'buyer', 'seller']
                for field in required_fields:
                    self.assertIn(field, transaction, f"Missing field: {field}")
    
    def test_market_analysis_structure(self):
        """Test market analysis data structure"""
        # Get market trends data
        market_data = self.agent.market_scraper.get_luxury_market_trends('90210')
        
        required_fields = [
            'zip_code', 'luxury_threshold', 'transactions_last_12_months',
            'average_sale_price', 'market_trend'
        ]
        
        for field in required_fields:
            self.assertIn(field, market_data, f"Missing field: {field}")


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and graceful degradation"""
    
    def setUp(self):
        self.agent = DataAgent()
    
    @patch('app.openai.OpenAI')
    def test_openai_api_error(self, mock_openai):
        """Test handling of OpenAI API errors"""
        # Mock OpenAI client that raises an exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        self.agent.client = mock_client
        
        result = self.agent.process_query("Test query")
        
        # Should return error response without crashing
        self.assertIsInstance(result, dict)
        self.assertIn('response', result)
    
    def test_malformed_intent_data(self):
        """Test handling of malformed intent data"""
        # Test with missing parameters
        intent_data = {}
        result = self.agent.query_real_estate(intent_data)
        self.assertIsInstance(result, dict)
        
        # Test with malformed parameters
        intent_data = {"parameters": None}
        result = self.agent.query_real_estate(intent_data)
        self.assertIsInstance(result, dict)
    
    @patch('requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors"""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        intent_data = {"parameters": {"company": "Tesla"}}
        result = self.agent.query_edgar(intent_data)
        
        # Should return error information
        self.assertIsInstance(result, dict)
        self.assertIn('error', result)


class TestPerformance(unittest.TestCase):
    """Test performance and efficiency"""
    
    def setUp(self):
        self.agent = DataAgent()
    
    def test_response_time(self):
        """Test that responses are generated in reasonable time"""
        import time
        
        start_time = time.time()
        
        # Simple real estate query
        intent_data = {"parameters": {"zip_code": "90210", "min_price": 25000000}}
        result = self.agent.query_real_estate(intent_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should complete within 5 seconds
        self.assertLess(response_time, 5.0)
        self.assertIsInstance(result, dict)
    
    def test_memory_usage(self):
        """Test that memory usage is reasonable"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform multiple queries
        for i in range(10):
            intent_data = {"parameters": {"zip_code": "90210", "min_price": 25000000}}
            self.agent.query_real_estate(intent_data)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDataAgent,
        TestFlaskApp,
        TestQueryParsing,
        TestDataIntegrity,
        TestErrorRecovery,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)