#!/usr/bin/env python3
"""
Master test runner for AI Data Assistant
Runs all test suites and provides comprehensive reporting
"""

import unittest
import sys
import os
import time
from io import StringIO
import json

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import all test modules
from test_scrapers import *
from test_app import *
from test_frontend import *


class TestResult:
    """Custom test result class for detailed reporting"""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.start_time = None
        self.end_time = None
        
    def start_testing(self):
        self.start_time = time.time()
        
    def finish_testing(self):
        self.end_time = time.time()
        
    def add_test_result(self, test_name, result, details=None):
        self.test_results[test_name] = {
            'result': result,
            'details': details
        }
        self.total_tests += 1
        
        if result == 'PASS':
            self.passed_tests += 1
        elif result == 'FAIL':
            self.failed_tests += 1
        elif result == 'ERROR':
            self.error_tests += 1
        elif result == 'SKIP':
            self.skipped_tests += 1
    
    def get_summary(self):
        duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        return {
            'total_tests': self.total_tests,
            'passed': self.passed_tests,
            'failed': self.failed_tests,
            'errors': self.error_tests,
            'skipped': self.skipped_tests,
            'duration': duration,
            'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        }


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.result = TestResult()
        
    def run_test_suite(self, test_classes, suite_name):
        """Run a specific test suite"""
        print(f"\n{'='*60}")
        print(f"Running {suite_name} Test Suite")
        print(f"{'='*60}")
        
        suite = unittest.TestSuite()
        
        # Add all test classes to suite
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Capture output
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=self.verbosity)
        test_result = runner.run(suite)
        
        # Process results
        for test, error in test_result.failures:
            self.result.add_test_result(str(test), 'FAIL', error)
            
        for test, error in test_result.errors:
            self.result.add_test_result(str(test), 'ERROR', error)
            
        # Calculate passed tests
        total_in_suite = test_result.testsRun
        failed_in_suite = len(test_result.failures) + len(test_result.errors)
        passed_in_suite = total_in_suite - failed_in_suite
        
        for i in range(passed_in_suite):
            self.result.add_test_result(f"{suite_name}_passed_{i}", 'PASS')
        
        # Print suite summary
        print(f"\n{suite_name} Results:")
        print(f"  Tests run: {total_in_suite}")
        print(f"  Passed: {passed_in_suite}")
        print(f"  Failed: {len(test_result.failures)}")
        print(f"  Errors: {len(test_result.errors)}")
        
        if test_result.failures:
            print(f"  Failures:")
            for test, error in test_result.failures:
                print(f"    - {test}")
                
        if test_result.errors:
            print(f"  Errors:")
            for test, error in test_result.errors:
                print(f"    - {test}")
        
        return test_result.wasSuccessful()
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🤖 AI Data Assistant - Comprehensive Test Suite")
        print("=" * 80)
        
        self.result.start_testing()
        
        # Define test suites
        test_suites = [
            {
                'name': 'Scrapers',
                'description': 'Real estate scraping functionality',
                'classes': [
                    TestRealEstateTransactionScraper,
                    TestPropertyOwnerScraper,
                    TestMarketAnalysisScraper,
                    TestUtilityFunctions,
                    TestDataValidation,
                    TestErrorHandling,
                    TestIntegrationScenarios
                ]
            },
            {
                'name': 'Application',
                'description': 'Flask app and DataAgent functionality',
                'classes': [
                    TestDataAgent,
                    TestFlaskApp,
                    TestQueryParsing,
                    TestDataIntegrity,
                    TestErrorRecovery,
                    TestPerformance
                ]
            },
            {
                'name': 'Frontend',
                'description': 'Frontend integration and user experience',
                'classes': [
                    TestFrontendAPIIntegration,
                    TestDataVisualization,
                    TestUserInteraction,
                    TestResponseTiming,
                    TestAccessibility,
                    TestIntegrationWorkflows
                ]
            }
        ]
        
        # Run each test suite
        all_successful = True
        suite_results = {}
        
        for suite_info in test_suites:
            print(f"\n📋 {suite_info['description']}")
            success = self.run_test_suite(suite_info['classes'], suite_info['name'])
            suite_results[suite_info['name']] = success
            if not success:
                all_successful = False
        
        self.result.finish_testing()
        
        # Generate comprehensive report
        self.generate_report(suite_results, all_successful)
        
        return all_successful
    
    def generate_report(self, suite_results, all_successful):
        """Generate comprehensive test report"""
        summary = self.result.get_summary()
        
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST REPORT")
        print(f"{'='*80}")
        
        # Overall summary
        print(f"🎯 Overall Results:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   ✅ Passed: {summary['passed']}")
        print(f"   ❌ Failed: {summary['failed']}")
        print(f"   🚫 Errors: {summary['errors']}")
        print(f"   ⏭️  Skipped: {summary['skipped']}")
        print(f"   ⏱️  Duration: {summary['duration']:.2f} seconds")
        print(f"   📈 Success Rate: {summary['success_rate']:.1f}%")
        
        # Suite-by-suite results
        print(f"\n📋 Suite Results:")
        for suite_name, success in suite_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {suite_name}: {status}")
        
        # Overall status
        print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_successful else '❌ SOME TESTS FAILED'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if all_successful:
            print("   🎉 Excellent! All tests are passing.")
            print("   🚀 The application is ready for deployment.")
            print("   📝 Consider adding more edge case tests as the app grows.")
        else:
            print("   🔍 Review failed tests and fix issues before deployment.")
            print("   🐛 Check error messages for debugging information.")
            print("   🔄 Re-run tests after making fixes.")
        
        # Save detailed report to file
        self.save_detailed_report(summary, suite_results)
    
    def save_detailed_report(self, summary, suite_results):
        """Save detailed test report to JSON file"""
        try:
            report_data = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'summary': summary,
                'suite_results': suite_results,
                'test_details': self.result.test_results
            }
            
            # Create reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            # Save report
            report_file = os.path.join(reports_dir, f"test_report_{int(time.time())}.json")
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            print(f"\n📄 Detailed report saved to: {report_file}")
            
        except Exception as e:
            print(f"\n⚠️  Could not save detailed report: {e}")


def run_specific_tests(test_type):
    """Run specific type of tests"""
    runner = ComprehensiveTestRunner()
    
    if test_type == 'scrapers':
        test_classes = [
            TestRealEstateTransactionScraper,
            TestPropertyOwnerScraper,
            TestMarketAnalysisScraper,
            TestUtilityFunctions
        ]
        return runner.run_test_suite(test_classes, 'Scrapers')
        
    elif test_type == 'app':
        test_classes = [
            TestDataAgent,
            TestFlaskApp,
            TestQueryParsing
        ]
        return runner.run_test_suite(test_classes, 'Application')
        
    elif test_type == 'frontend':
        test_classes = [
            TestFrontendAPIIntegration,
            TestDataVisualization,
            TestUserInteraction
        ]
        return runner.run_test_suite(test_classes, 'Frontend')
        
    else:
        print(f"Unknown test type: {test_type}")
        return False


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Data Assistant Test Runner')
    parser.add_argument('--type', choices=['all', 'scrapers', 'app', 'frontend'], 
                       default='all', help='Type of tests to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Increase verbosity')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='Run quick tests only (skip performance tests)')
    
    args = parser.parse_args()
    
    # Set verbosity
    verbosity = 2 if args.verbose else 1
    
    try:
        if args.type == 'all':
            runner = ComprehensiveTestRunner(verbosity)
            success = runner.run_all_tests()
        else:
            success = run_specific_tests(args.type)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()