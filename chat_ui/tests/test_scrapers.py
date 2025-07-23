"""
Unit tests for real estate scrapers
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scrapers import (
    RealEstateTransactionScraper,
    PropertyOwnerScraper,
    MarketAnalysisScraper,
    analyze_buyer_patterns,
    format_currency,
    search_celebrity_real_estate
)


class TestRealEstateTransactionScraper(unittest.TestCase):
    """Test the RealEstateTransactionScraper class"""
    
    def setUp(self):
        self.scraper = RealEstateTransactionScraper()
    
    def test_initialization(self):
        """Test that scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.session)
        self.assertIn('User-Agent', self.scraper.session.headers)
    
    def test_search_high_value_transactions_valid_zip(self):
        """Test searching for high-value transactions in a valid zip code"""
        transactions = self.scraper.search_high_value_transactions('90210', 25000000)
        
        # Should return a list
        self.assertIsInstance(transactions, list)
        
        # For high-value zip codes, should have transactions
        if transactions:
            for transaction in transactions:
                self.assertIsInstance(transaction, dict)
                self.assertIn('address', transaction)
                self.assertIn('price', transaction)
                self.assertIn('zip_code', transaction)
                self.assertGreaterEqual(transaction['price'], 25000000)
    
    def test_search_high_value_transactions_different_price_threshold(self):
        """Test searching with different price thresholds"""
        transactions_25m = self.scraper.search_high_value_transactions('90210', 25000000)
        transactions_50m = self.scraper.search_high_value_transactions('90210', 50000000)
        
        # Higher threshold should return fewer or equal transactions
        self.assertLessEqual(len(transactions_50m), len(transactions_25m))
    
    def test_scrape_public_records(self):
        """Test scraping public records functionality"""
        transactions = self.scraper._scrape_public_records('90210', 25000000)
        
        self.assertIsInstance(transactions, list)
        
        if transactions:
            for transaction in transactions:
                self.assertIn('source', transaction)
                self.assertEqual(transaction['source'], 'Public Records')
                self.assertIn('buyer', transaction)
                self.assertIn('seller', transaction)
    
    def test_scrape_realtor_com(self):
        """Test Realtor.com scraping functionality"""
        # Test with high-value zip code
        transactions = self.scraper._scrape_realtor_com('90210', 25000000)
        self.assertIsInstance(transactions, list)
        
        # Test with non-luxury zip code
        transactions_regular = self.scraper._scrape_realtor_com('12345', 25000000)
        self.assertIsInstance(transactions_regular, list)
    
    def test_scrape_zillow_sales(self):
        """Test Zillow sales scraping functionality"""
        transactions = self.scraper._scrape_zillow_sales('90210', 25000000)
        
        self.assertIsInstance(transactions, list)
        
        if transactions:
            for transaction in transactions:
                self.assertIn('amenities', transaction)
                self.assertIsInstance(transaction['amenities'], list)
    
    def test_deduplicate_transactions(self):
        """Test transaction deduplication"""
        # Create test data with duplicates
        transactions = [
            {'address': '123 Test St', 'price': 30000000, 'buyer': 'Test Buyer'},
            {'address': '123 Test St', 'price': 30000000, 'buyer': 'Test Buyer'},  # Duplicate
            {'address': '456 Other St', 'price': 25000000, 'buyer': 'Other Buyer'}
        ]
        
        unique_transactions = self.scraper._deduplicate_transactions(transactions)
        
        # Should remove the duplicate
        self.assertEqual(len(unique_transactions), 2)
        
        # Ensure all unique transactions are preserved
        addresses = [t['address'] for t in unique_transactions]
        self.assertIn('123 Test St', addresses)
        self.assertIn('456 Other St', addresses)


class TestPropertyOwnerScraper(unittest.TestCase):
    """Test the PropertyOwnerScraper class"""
    
    def setUp(self):
        self.scraper = PropertyOwnerScraper()
    
    def test_initialization(self):
        """Test that owner scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.session)
    
    def test_get_property_owner_details(self):
        """Test getting property owner details"""
        details = self.scraper.get_property_owner_details('123 Test Street')
        
        self.assertIsInstance(details, dict)
        
        # Check for expected keys
        expected_keys = [
            'current_owner', 'owner_type', 'ownership_date',
            'purchase_price', 'assessed_value'
        ]
        
        for key in expected_keys:
            self.assertIn(key, details)
    
    def test_get_property_owner_details_with_exception(self):
        """Test error handling in owner details retrieval"""
        # This should not raise an exception even if there are errors
        details = self.scraper.get_property_owner_details('')
        self.assertIsInstance(details, dict)


class TestMarketAnalysisScraper(unittest.TestCase):
    """Test the MarketAnalysisScraper class"""
    
    def setUp(self):
        self.scraper = MarketAnalysisScraper()
    
    def test_initialization(self):
        """Test that market scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.session)
    
    def test_get_luxury_market_trends(self):
        """Test getting luxury market trends"""
        trends = self.scraper.get_luxury_market_trends('90210')
        
        self.assertIsInstance(trends, dict)
        
        # Check for expected keys
        expected_keys = [
            'zip_code', 'luxury_threshold', 'transactions_last_12_months',
            'average_sale_price', 'market_trend', 'year_over_year_change'
        ]
        
        for key in expected_keys:
            self.assertIn(key, trends)
        
        # Verify data types
        self.assertIsInstance(trends['luxury_threshold'], int)
        self.assertIsInstance(trends['transactions_last_12_months'], int)
        self.assertIsInstance(trends['average_sale_price'], int)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_format_currency(self):
        """Test currency formatting function"""
        # Test millions
        self.assertEqual(format_currency(25000000), "$25.0M")
        self.assertEqual(format_currency(1500000), "$1.5M")
        
        # Test thousands
        self.assertEqual(format_currency(750000), "$750K")
        self.assertEqual(format_currency(1000), "$1K")
        
        # Test smaller amounts
        self.assertEqual(format_currency(500), "$500")
        self.assertEqual(format_currency(0), "$0")
    
    def test_analyze_buyer_patterns(self):
        """Test buyer pattern analysis"""
        transactions = [
            {'buyer': 'FAMILY TRUST'},
            {'buyer': 'TECH CORP LLC'},
            {'buyer': 'INVESTMENT FUND LP'},
            {'buyer': 'JOHN DOE'},
            {'buyer': 'ESTATE OF SMITH'},
            {'buyer': 'ANOTHER TRUST', 'price': 30000000},
            {'buyer': 'BIG COMPANY CORP', 'price': 45000000}
        ]
        
        analysis = analyze_buyer_patterns(transactions)
        
        self.assertIsInstance(analysis, dict)
        
        # Check for expected keys
        expected_keys = ['buyer_type_distribution', 'total_transactions', 'total_value', 'average_price']
        for key in expected_keys:
            self.assertIn(key, analysis)
        
        # Verify buyer type categorization
        distribution = analysis['buyer_type_distribution']
        self.assertIn('Family Trust', distribution)
        self.assertIn('Corporate Entity', distribution)
        self.assertIn('Investment Fund', distribution)
        self.assertIn('Individual', distribution)
        self.assertIn('Estate', distribution)
        
        # Check counts
        self.assertEqual(distribution['Family Trust'], 2)  # 2 trusts
        self.assertEqual(distribution['Corporate Entity'], 2)  # 2 corps
        self.assertEqual(analysis['total_transactions'], 7)
    
    def test_search_celebrity_real_estate(self):
        """Test celebrity real estate search"""
        results = search_celebrity_real_estate('Test Celebrity')
        
        self.assertIsInstance(results, list)
        
        if results:
            for result in results:
                self.assertIsInstance(result, dict)
                self.assertIn('person', result)
                self.assertIn('transaction_type', result)
                self.assertIn('price', result)
                self.assertIn('property_details', result)


class TestDataValidation(unittest.TestCase):
    """Test data validation and consistency"""
    
    def setUp(self):
        self.scraper = RealEstateTransactionScraper()
    
    def test_transaction_data_structure(self):
        """Test that transaction data has consistent structure"""
        transactions = self.scraper.search_high_value_transactions('90210', 25000000)
        
        for transaction in transactions:
            # Required fields
            required_fields = ['address', 'price', 'sale_date', 'buyer', 'seller', 'source']
            for field in required_fields:
                self.assertIn(field, transaction, f"Missing required field: {field}")
            
            # Data type validation
            self.assertIsInstance(transaction['price'], int)
            self.assertGreater(transaction['price'], 0)
            self.assertIsInstance(transaction['address'], str)
            self.assertIsInstance(transaction['buyer'], str)
            self.assertIsInstance(transaction['seller'], str)
    
    def test_price_filtering(self):
        """Test that price filtering works correctly"""
        min_price = 30000000
        transactions = self.scraper.search_high_value_transactions('90210', min_price)
        
        for transaction in transactions:
            self.assertGreaterEqual(
                transaction['price'], 
                min_price,
                f"Transaction price {transaction['price']} below threshold {min_price}"
            )
    
    def test_zip_code_consistency(self):
        """Test that returned transactions match requested zip code"""
        zip_code = '90210'
        transactions = self.scraper.search_high_value_transactions(zip_code, 25000000)
        
        for transaction in transactions:
            if 'zip_code' in transaction:
                self.assertEqual(
                    transaction['zip_code'], 
                    zip_code,
                    f"Transaction zip code {transaction['zip_code']} doesn't match requested {zip_code}"
                )


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.scraper = RealEstateTransactionScraper()
    
    def test_invalid_zip_code(self):
        """Test handling of invalid zip codes"""
        # Should not crash with invalid zip codes
        transactions = self.scraper.search_high_value_transactions('00000', 25000000)
        self.assertIsInstance(transactions, list)
        
        transactions = self.scraper.search_high_value_transactions('', 25000000)
        self.assertIsInstance(transactions, list)
    
    def test_invalid_price_threshold(self):
        """Test handling of invalid price thresholds"""
        # Negative price
        transactions = self.scraper.search_high_value_transactions('90210', -1000000)
        self.assertIsInstance(transactions, list)
        
        # Zero price
        transactions = self.scraper.search_high_value_transactions('90210', 0)
        self.assertIsInstance(transactions, list)
    
    def test_network_error_simulation(self):
        """Test handling of network errors"""
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Should handle gracefully without crashing
            transactions = self.scraper._scrape_public_records('90210', 25000000)
            self.assertIsInstance(transactions, list)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and real-world use cases"""
    
    def setUp(self):
        self.scraper = RealEstateTransactionScraper()
        self.owner_scraper = PropertyOwnerScraper()
        self.market_scraper = MarketAnalysisScraper()
    
    def test_complete_luxury_market_analysis(self):
        """Test complete luxury market analysis workflow"""
        zip_code = '90210'
        min_price = 25000000
        
        # Get transactions
        transactions = self.scraper.search_high_value_transactions(zip_code, min_price)
        
        # Get market trends
        market_data = self.market_scraper.get_luxury_market_trends(zip_code)
        
        # Analyze buyer patterns
        if transactions:
            buyer_analysis = analyze_buyer_patterns(transactions)
            
            # Verify analysis makes sense
            self.assertEqual(buyer_analysis['total_transactions'], len(transactions))
            self.assertGreater(buyer_analysis['total_value'], 0)
    
    def test_multi_zip_code_comparison(self):
        """Test comparing multiple zip codes"""
        zip_codes = ['90210', '10021', '94027']  # Beverly Hills, Manhattan, Palo Alto
        
        all_results = {}
        for zip_code in zip_codes:
            transactions = self.scraper.search_high_value_transactions(zip_code, 25000000)
            market_data = self.market_scraper.get_luxury_market_trends(zip_code)
            
            all_results[zip_code] = {
                'transactions': transactions,
                'market_data': market_data
            }
        
        # Verify we got data for each zip code
        for zip_code in zip_codes:
            self.assertIn(zip_code, all_results)
            self.assertIsInstance(all_results[zip_code]['transactions'], list)
            self.assertIsInstance(all_results[zip_code]['market_data'], dict)


if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestRealEstateTransactionScraper,
        TestPropertyOwnerScraper,
        TestMarketAnalysisScraper,
        TestUtilityFunctions,
        TestDataValidation,
        TestErrorHandling,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)