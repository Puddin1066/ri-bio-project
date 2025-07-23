from django.core.management.base import BaseCommand, CommandError
from streeteasy_integration.sec_edgar_integration import SECRealEstateAnalyzer


class Command(BaseCommand):
    help = 'Analyze SEC liquidity events for real estate companies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Specific company ticker or name to analyze',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=365,
            help='Number of days to look back for events',
        )
        parser.add_argument(
            '--correlate',
            action='store_true',
            help='Correlate SEC events with real estate data',
        )
        parser.add_argument(
            '--question',
            type=str,
            help='Ask a specific question about SEC data',
        )

    def handle(self, *args, **options):
        analyzer = SECRealEstateAnalyzer()
        
        if options['question']:
            # Answer specific question
            question = options['question']
            self.stdout.write(f"Question: {question}")
            self.stdout.write("-" * 50)
            
            try:
                answer = analyzer.answer_sec_question(question)
                self.stdout.write(answer)
            except Exception as e:
                raise CommandError(f'Question analysis failed: {str(e)}')
        
        elif options['company']:
            # Analyze specific company
            company = options['company']
            self.stdout.write(f"Analyzing SEC data for: {company}")
            self.stdout.write("-" * 50)
            
            try:
                profile = analyzer.get_company_financial_profile(company)
                
                if profile:
                    company_info = profile['company_info']
                    metrics = profile['financial_metrics']
                    filings = profile['recent_filings']
                    events = profile['liquidity_events']
                    
                    self.stdout.write(f"Company: {company_info['name']} ({company_info.get('ticker', 'N/A')})")
                    self.stdout.write(f"CIK: {company_info['cik']}")
                    
                    if metrics:
                        self.stdout.write("\nKey Financial Metrics:")
                        for metric, data in metrics.items():
                            if isinstance(data, dict) and 'value' in data:
                                value = data['value']
                                if isinstance(value, (int, float)) and value > 1000000:
                                    if value >= 1000000000:
                                        value_str = f"${value/1000000000:.1f}B"
                                    else:
                                        value_str = f"${value/1000000:.1f}M"
                                else:
                                    value_str = f"{value:,}" if isinstance(value, (int, float)) else str(value)
                                self.stdout.write(f"  {metric}: {value_str}")
                    
                    if filings:
                        self.stdout.write(f"\nRecent SEC Filings ({len(filings)}):")
                        for filing in filings[:5]:
                            self.stdout.write(f"  {filing['form']} - {filing['filing_date']}")
                    
                    if events:
                        self.stdout.write(f"\nLiquidity Events ({len(events)}):")
                        for event in events:
                            keywords = ', '.join(event.get('keywords', [])[:3])
                            amount = event.get('max_amount')
                            amount_str = ''
                            if amount:
                                if amount >= 1000000000:
                                    amount_str = f" (${amount/1000000000:.1f}B)"
                                else:
                                    amount_str = f" (${amount/1000000:.1f}M)"
                            
                            self.stdout.write(f"  {event['filing_date']}: {keywords}{amount_str}")
                else:
                    self.stdout.write(f"No SEC data found for {company}")
                    
            except Exception as e:
                raise CommandError(f'Company analysis failed: {str(e)}')
        
        else:
            # General analysis of real estate companies
            days_back = options['days_back']
            correlate = options['correlate']
            
            self.stdout.write(f"Analyzing SEC liquidity events for real estate companies")
            self.stdout.write(f"Timeframe: {days_back} days")
            self.stdout.write("-" * 50)
            
            try:
                events = analyzer.find_real_estate_liquidity_events(days_back)
                
                if events:
                    self.stdout.write(f"Found {len(events)} SEC liquidity events:")
                    
                    for i, event in enumerate(events, 1):
                        company = event.get('company_name', 'Unknown')
                        ticker = event.get('ticker', 'N/A')
                        date = event.get('filing_date', 'Unknown')
                        keywords = ', '.join(event.get('keywords', [])[:3])
                        amount = event.get('max_amount')
                        
                        self.stdout.write(f"\n{i}. {company} ({ticker})")
                        self.stdout.write(f"   Filed: {date}")
                        self.stdout.write(f"   Keywords: {keywords}")
                        
                        if amount:
                            if amount >= 1000000000:
                                amount_str = f"${amount/1000000000:.1f}B"
                            else:
                                amount_str = f"${amount/1000000:.1f}M"
                            self.stdout.write(f"   Amount: {amount_str}")
                
                # Correlate with real estate data if requested
                if correlate and events:
                    self.stdout.write("\n" + "="*50)
                    self.stdout.write("CORRELATION WITH REAL ESTATE DATA")
                    self.stdout.write("="*50)
                    
                    correlations = analyzer.correlate_with_real_estate_data(events)
                    
                    significant_correlations = [
                        c for c in correlations if c['correlation_score'] > 0
                    ]
                    
                    if significant_correlations:
                        self.stdout.write(f"Found {len(significant_correlations)} correlations:")
                        
                        for corr in significant_correlations:
                            sec_event = corr['sec_event']
                            re_events = corr['related_real_estate_events']
                            
                            self.stdout.write(f"\nSEC Event: {sec_event['company_name']} ({sec_event['filing_date']})")
                            self.stdout.write(f"Related Real Estate Events ({len(re_events)}):")
                            
                            for re_event in re_events:
                                self.stdout.write(f"  - {re_event['seller_name']}: {re_event['formatted_price']}")
                                if re_event.get('property_address'):
                                    self.stdout.write(f"    {re_event['property_address']}")
                    else:
                        self.stdout.write("No significant correlations found.")
                else:
                    self.stdout.write(f"No SEC liquidity events found in the past {days_back} days.")
                    
            except Exception as e:
                raise CommandError(f'SEC analysis failed: {str(e)}')