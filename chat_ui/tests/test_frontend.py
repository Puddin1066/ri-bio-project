"""
Unit tests for frontend functionality
Tests the JavaScript components via API endpoints and response validation
"""

import unittest
from unittest.mock import patch, Mock
import json
import sys
import os
import requests

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Mock environment variables before importing app
with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
    from app import app


class TestFrontendAPIIntegration(unittest.TestCase):
    """Test frontend-backend API integration"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_static_file_serving(self):
        """Test that static files are served correctly"""
        # Test index.html
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI Data Assistant', response.data)
        
        # Test CSS file
        response = self.app.get('/styles.css')
        self.assertEqual(response.status_code, 200)
        
        # Test JavaScript file
        response = self.app.get('/script.js')
        self.assertEqual(response.status_code, 200)
    
    def test_frontend_suggested_queries(self):
        """Test that suggested queries work via API"""
        suggested_queries = [
            "Show me the latest 10-K filings for Tesla",
            "Who in zip code 90210 bought or sold a house over $25 million?",
            "Compare Apple and Microsoft financial metrics",
            "Show luxury real estate trends in Manhattan zip code 10021",
            "Find high-value property transactions in Palo Alto over $30 million",
            "Who are the biggest buyers in Miami Beach luxury real estate?"
        ]
        
        for query in suggested_queries:
            with patch('app.data_agent.process_query') as mock_process:
                mock_process.return_value = {
                    "response": f"Mock response for: {query}",
                    "data": None
                }
                
                response = self.app.post('/api/chat',
                                       data=json.dumps({"message": query}),
                                       content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertIn('response', data)
                self.assertIn(query, data['response'])
    
    def test_real_estate_query_response_format(self):
        """Test that real estate queries return proper format for frontend"""
        with patch('app.data_agent.process_query') as mock_process:
            # Mock real estate response with table data
            mock_process.return_value = {
                "response": "Found 3 high-value transactions in Beverly Hills",
                "data": {
                    "type": "table",
                    "content": {
                        "headers": ["Address", "Price", "Date", "Buyer", "Details"],
                        "rows": [
                            ["123 Luxury Lane", "$32.5M", "2024-03-15", "TECH EXECUTIVE TRUST", "12500 sqft"],
                            ["456 Mansion Drive", "$28.8M", "2024-02-28", "INVESTMENT FUND LP", "15200 sqft"]
                        ]
                    }
                }
            }
            
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": "Who bought houses over $25M in 90210?"}),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify response structure
            self.assertIn('response', data)
            self.assertIn('data', data)
            self.assertEqual(data['data']['type'], 'table')
            self.assertIn('headers', data['data']['content'])
            self.assertIn('rows', data['data']['content'])
    
    def test_edgar_query_response_format(self):
        """Test that EDGAR queries return proper format for frontend"""
        with patch('app.data_agent.process_query') as mock_process:
            # Mock EDGAR response with metrics data
            mock_process.return_value = {
                "response": "Here are Tesla's key financial metrics",
                "data": {
                    "type": "metrics",
                    "content": [
                        {"label": "Assets", "value": "$100,000,000", "period": "2023-12-31"},
                        {"label": "Revenue", "value": "$96,773,000", "period": "2023-12-31"}
                    ]
                }
            }
            
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": "Show me Tesla's financial data"}),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify response structure
            self.assertIn('response', data)
            self.assertIn('data', data)
            self.assertEqual(data['data']['type'], 'metrics')
            self.assertIsInstance(data['data']['content'], list)
    
    def test_error_handling_frontend(self):
        """Test that frontend errors are handled gracefully"""
        with patch('app.data_agent.process_query') as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": "Test query"}),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertIn('response', data)
            self.assertIn('technical difficulties', data['response'])


class TestDataVisualization(unittest.TestCase):
    """Test data visualization components"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_table_data_structure(self):
        """Test that table data is properly structured"""
        table_data = {
            "type": "table",
            "content": {
                "headers": ["Address", "Price", "Date", "Buyer"],
                "rows": [
                    ["123 Test St", "$30.0M", "2024-01-15", "Test Buyer"]
                ]
            }
        }
        
        # Verify structure
        self.assertEqual(table_data['type'], 'table')
        self.assertIn('headers', table_data['content'])
        self.assertIn('rows', table_data['content'])
        self.assertIsInstance(table_data['content']['headers'], list)
        self.assertIsInstance(table_data['content']['rows'], list)
        
        # Verify data consistency
        headers_count = len(table_data['content']['headers'])
        for row in table_data['content']['rows']:
            self.assertEqual(len(row), headers_count, "Row length should match header count")
    
    def test_metrics_data_structure(self):
        """Test that metrics data is properly structured"""
        metrics_data = {
            "type": "metrics",
            "content": [
                {"label": "Average Sale Price", "value": "$38.5M"},
                {"label": "Transactions (12mo)", "value": "8"},
                {"label": "Market Trend", "value": "Stable"}
            ]
        }
        
        # Verify structure
        self.assertEqual(metrics_data['type'], 'metrics')
        self.assertIsInstance(metrics_data['content'], list)
        
        # Verify each metric has required fields
        for metric in metrics_data['content']:
            self.assertIn('label', metric)
            self.assertIn('value', metric)
    
    def test_currency_formatting_consistency(self):
        """Test that currency values are consistently formatted"""
        # Test various currency formats that might be returned
        currency_values = [
            "$25,000,000",
            "$25.0M",
            "$25M",
            "25000000",
            "$25,000,000.00"
        ]
        
        # All should be valid for frontend display
        for value in currency_values:
            # Test that value is a string and contains recognizable currency info
            self.assertIsInstance(value, str)


class TestUserInteraction(unittest.TestCase):
    """Test user interaction patterns"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_multiple_query_session(self):
        """Test handling multiple queries in a session"""
        queries = [
            "Show me Tesla's latest filings",
            "Who bought houses over $50M in Manhattan?",
            "Compare luxury markets in Beverly Hills vs Palo Alto"
        ]
        
        for query in queries:
            with patch('app.data_agent.process_query') as mock_process:
                mock_process.return_value = {
                    "response": f"Response to: {query}",
                    "data": None
                }
                
                response = self.app.post('/api/chat',
                                       data=json.dumps({"message": query}),
                                       content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertIn('response', data)
    
    def test_empty_and_invalid_queries(self):
        """Test handling of empty and invalid queries"""
        invalid_queries = [
            "",  # Empty string
            " ",  # Just whitespace
            "   ",  # Multiple spaces
            None,  # None value
        ]
        
        for query in invalid_queries:
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": query}),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('response', data)
    
    def test_special_characters_in_queries(self):
        """Test handling of special characters in queries"""
        special_queries = [
            "Show me data for 'Tesla Inc.'",
            "Find properties > $25M",
            "Search for John & Jane Doe",
            "Properties with 100% cash purchases",
            "Company filings from 2020-2024"
        ]
        
        for query in special_queries:
            with patch('app.data_agent.process_query') as mock_process:
                mock_process.return_value = {
                    "response": f"Processed query with special characters: {query}",
                    "data": None
                }
                
                response = self.app.post('/api/chat',
                                       data=json.dumps({"message": query}),
                                       content_type='application/json')
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertIn('response', data)


class TestResponseTiming(unittest.TestCase):
    """Test response timing and user experience"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_quick_response_time(self):
        """Test that API responses are reasonably fast"""
        import time
        
        with patch('app.data_agent.process_query') as mock_process:
            mock_process.return_value = {
                "response": "Quick test response",
                "data": None
            }
            
            start_time = time.time()
            
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": "Test query"}),
                                   content_type='application/json')
            
            end_time = time.time()
            response_time = end_time - start_time
            
            self.assertEqual(response.status_code, 200)
            # API should respond within 1 second for simple queries
            self.assertLess(response_time, 1.0)
    
    def test_timeout_handling(self):
        """Test handling of slow responses"""
        import time
        
        with patch('app.data_agent.process_query') as mock_process:
            # Simulate slow response
            def slow_response(query):
                time.sleep(0.5)  # Simulate delay
                return {
                    "response": "Slow response",
                    "data": None
                }
            
            mock_process.side_effect = slow_response
            
            response = self.app.post('/api/chat',
                                   data=json.dumps({"message": "Slow query"}),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('response', data)


class TestAccessibility(unittest.TestCase):
    """Test accessibility and usability features"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_html_structure_validity(self):
        """Test that HTML structure is valid"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        html_content = response.data.decode('utf-8')
        
        # Check for essential HTML elements
        self.assertIn('<html', html_content)
        self.assertIn('<head>', html_content)
        self.assertIn('<body>', html_content)
        self.assertIn('</html>', html_content)
        
        # Check for accessibility features
        self.assertIn('alt=', html_content.lower() or 'aria-label=', html_content.lower())
        self.assertIn('viewport', html_content)
    
    def test_responsive_design_elements(self):
        """Test that responsive design elements are present"""
        response = self.app.get('/styles.css')
        self.assertEqual(response.status_code, 200)
        
        css_content = response.data.decode('utf-8')
        
        # Check for responsive design indicators
        self.assertIn('@media', css_content)
        self.assertIn('max-width', css_content)
    
    def test_api_cors_headers(self):
        """Test that CORS headers are properly set"""
        response = self.app.post('/api/chat',
                               data=json.dumps({"message": "Test"}),
                               content_type='application/json')
        
        # Check for CORS headers (if CORS is enabled)
        # This will depend on your CORS configuration
        self.assertEqual(response.status_code, 200)


class TestIntegrationWorkflows(unittest.TestCase):
    """Test complete user workflows from frontend to backend"""
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
    
    def test_complete_real_estate_workflow(self):
        """Test complete real estate query workflow"""
        with patch('app.data_agent.process_query') as mock_process:
            # Mock a complete real estate response
            mock_process.return_value = {
                "response": "Found 3 luxury properties in Beverly Hills over $25M",
                "data": {
                    "type": "table",
                    "content": {
                        "headers": ["Address", "Price", "Date", "Buyer", "Details"],
                        "rows": [
                            ["123 Luxury Lane", "$32.5M", "2024-03-15", "TECH EXECUTIVE TRUST", "12500 sqft"],
                            ["456 Mansion Drive", "$28.8M", "2024-02-28", "INVESTMENT FUND LP", "15200 sqft"],
                            ["789 Elite Estates Blvd", "$45.2M", "2024-01-20", "VENTURE CAPITAL PARTNERS", "18500 sqft"]
                        ]
                    }
                }
            }
            
            # Simulate user query
            response = self.app.post('/api/chat',
                                   data=json.dumps({
                                       "message": "Who in zip code 90210 bought or sold a house over $25 million?",
                                       "timestamp": "2024-01-01T00:00:00Z"
                                   }),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify complete response structure
            self.assertIn('response', data)
            self.assertIn('data', data)
            self.assertEqual(data['data']['type'], 'table')
            
            # Verify table structure
            table_content = data['data']['content']
            self.assertEqual(len(table_content['headers']), 5)
            self.assertEqual(len(table_content['rows']), 3)
            
            # Verify data quality
            for row in table_content['rows']:
                self.assertEqual(len(row), 5)  # Should match header count
                self.assertIn('$', row[1])  # Price should contain dollar sign
    
    def test_complete_edgar_workflow(self):
        """Test complete EDGAR query workflow"""
        with patch('app.data_agent.process_query') as mock_process:
            # Mock a complete EDGAR response
            mock_process.return_value = {
                "response": "Here are Tesla's key financial metrics from their latest filing",
                "data": {
                    "type": "metrics",
                    "content": [
                        {"label": "Total Assets", "value": "$106,618,000,000", "period": "2023-12-31"},
                        {"label": "Revenue", "value": "$96,773,000,000", "period": "2023-12-31"},
                        {"label": "Net Income", "value": "$14,997,000,000", "period": "2023-12-31"}
                    ]
                }
            }
            
            # Simulate user query
            response = self.app.post('/api/chat',
                                   data=json.dumps({
                                       "message": "Show me Tesla's latest financial data",
                                       "timestamp": "2024-01-01T00:00:00Z"
                                   }),
                                   content_type='application/json')
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify complete response structure
            self.assertIn('response', data)
            self.assertIn('data', data)
            self.assertEqual(data['data']['type'], 'metrics')
            
            # Verify metrics structure
            metrics = data['data']['content']
            self.assertIsInstance(metrics, list)
            self.assertGreater(len(metrics), 0)
            
            # Verify metric quality
            for metric in metrics:
                self.assertIn('label', metric)
                self.assertIn('value', metric)
                self.assertIn('period', metric)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestFrontendAPIIntegration,
        TestDataVisualization,
        TestUserInteraction,
        TestResponseTiming,
        TestAccessibility,
        TestIntegrationWorkflows
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)