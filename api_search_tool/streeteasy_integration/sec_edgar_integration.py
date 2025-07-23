import requests
import json
import time
import re
from datetime import datetime, timedelta, date
from decimal import Decimal
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import StreetEasyEntity, StreetEasyLiquidityEvent


class SECEdgarAPI:
    """
    SEC EDGAR API integration for accessing corporate filings and financial data.
    This helps identify publicly traded real estate companies and their financial events.
    """
    
    def __init__(self, user_agent="Real Estate Analytics Tool contact@example.com"):
        self.base_url = "https://data.sec.gov"
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov'
        })
        self.rate_limit_delay = 0.1  # SEC requires 10 requests per second max
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        """Ensure we respect SEC rate limits (10 requests per second)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint, params=None):
        """Make a rate-limited request to SEC EDGAR API"""
        self._respect_rate_limit()
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.RequestException as e:
            print(f"SEC API request failed for {url}: {e}")
            return None
    
    def search_companies(self, query, limit=10):
        """
        Search for companies in SEC database
        
        Args:
            query: Company name or ticker symbol
            limit: Maximum number of results
        
        Returns:
            List of company information dictionaries
        """
        # Use the company tickers endpoint
        endpoint = "/files/company_tickers.json"
        response = self._make_request(endpoint)
        
        if not response:
            return []
        
        companies = []
        query_lower = query.lower()
        
        for key, company_data in response.items():
            if isinstance(company_data, dict):
                company_name = company_data.get('title', '').lower()
                ticker = company_data.get('ticker', '').lower()
                
                if (query_lower in company_name or 
                    query_lower in ticker or
                    ticker == query_lower):
                    
                    companies.append({
                        'cik': str(company_data.get('cik_str', '')).zfill(10),
                        'ticker': company_data.get('ticker', ''),
                        'title': company_data.get('title', ''),
                    })
                    
                    if len(companies) >= limit:
                        break
        
        return companies
    
    def get_company_facts(self, cik):
        """
        Get company facts (financial data) for a specific CIK
        
        Args:
            cik: Central Index Key (10-digit string)
        
        Returns:
            Dictionary containing company facts
        """
        endpoint = f"/api/xbrl/companyfacts/CIK{cik}.json"
        return self._make_request(endpoint)
    
    def get_company_filings(self, cik, form_type=None, limit=100):
        """
        Get recent filings for a company
        
        Args:
            cik: Central Index Key
            form_type: Specific form type (e.g., '10-K', '8-K', '10-Q')
            limit: Maximum number of filings to return
        
        Returns:
            List of filing information
        """
        endpoint = f"/api/xbrl/companyconcept/CIK{cik}"
        
        # Get company submissions first
        submissions_endpoint = f"/submissions/CIK{cik}.json"
        submissions = self._make_request(submissions_endpoint)
        
        if not submissions:
            return []
        
        filings = []
        recent_filings = submissions.get('filings', {}).get('recent', {})
        
        if not recent_filings:
            return []
        
        # Extract filing data
        forms = recent_filings.get('form', [])
        filing_dates = recent_filings.get('filingDate', [])
        accession_numbers = recent_filings.get('accessionNumber', [])
        primary_documents = recent_filings.get('primaryDocument', [])
        
        for i, form in enumerate(forms):
            if form_type and form != form_type:
                continue
            
            if i >= limit:
                break
            
            filing_info = {
                'form': form,
                'filing_date': filing_dates[i] if i < len(filing_dates) else None,
                'accession_number': accession_numbers[i] if i < len(accession_numbers) else None,
                'primary_document': primary_documents[i] if i < len(primary_documents) else None,
                'cik': cik
            }
            filings.append(filing_info)
        
        return filings
    
    def get_real_estate_companies(self):
        """
        Get companies in real estate industry based on SIC codes
        
        Real estate SIC codes:
        - 6500-6599: Real Estate
        - 6531: Real Estate Agents and Managers
        - 6798: Real Estate Investment Trusts
        """
        # This would require accessing company facts for many companies
        # For now, return a curated list of major real estate companies
        major_reits = [
            'SPG',   # Simon Property Group
            'PLD',   # Prologis
            'CCI',   # Crown Castle
            'AMT',   # American Tower
            'EQIX',  # Equinix
            'PSA',   # Public Storage
            'AVB',   # AvalonBay Communities
            'EQR',   # Equity Residential
            'WELL',  # Welltower
            'DLR',   # Digital Realty Trust
            'O',     # Realty Income
            'VTR',   # Ventas
            'ESS',   # Essex Property Trust
            'MAA',   # Mid-America Apartment Communities
            'EXR',   # Extended Stay America
            'UDR',   # UDR Inc
            'CPT',   # Camden Property Trust
            'AIV',   # Apartment Investment and Management
            'BXP',   # Boston Properties
            'VNO',   # Vornado Realty Trust
            'KIM',   # Kimco Realty
            'REG',   # Regency Centers
            'FRT',   # Federal Realty Investment Trust
            'HST',   # Host Hotels & Resorts
            'RHP',   # Ryman Hospitality Properties
        ]
        
        companies = []
        for ticker in major_reits:
            company_data = self.search_companies(ticker, limit=1)
            if company_data:
                companies.extend(company_data)
        
        return companies
    
    def extract_financial_metrics(self, company_facts):
        """
        Extract key financial metrics from company facts
        
        Args:
            company_facts: Company facts dictionary from SEC API
        
        Returns:
            Dictionary of financial metrics
        """
        if not company_facts or 'facts' not in company_facts:
            return {}
        
        facts = company_facts['facts']
        metrics = {}
        
        # Common XBRL tags for real estate companies
        key_metrics = {
            'Assets': ['us-gaap:Assets'],
            'TotalRevenue': ['us-gaap:Revenues', 'us-gaap:TotalRevenues'],
            'NetIncomeLoss': ['us-gaap:NetIncomeLoss', 'us-gaap:ProfitLoss'],
            'Cash': ['us-gaap:CashAndCashEquivalentsAtCarryingValue'],
            'TotalDebt': ['us-gaap:LongTermDebt', 'us-gaap:DebtCurrent'],
            'PropertyPlantEquipment': ['us-gaap:PropertyPlantAndEquipmentNet'],
            'RealEstateInvestments': ['us-gaap:RealEstateInvestmentPropertyNet'],
            'CommonStockSharesOutstanding': ['us-gaap:CommonStockSharesOutstanding'],
            'StockholdersEquity': ['us-gaap:StockholdersEquity'],
        }
        
        # Extract most recent values for each metric
        for metric_name, xbrl_tags in key_metrics.items():
            for tag in xbrl_tags:
                if tag in facts.get('us-gaap', {}):
                    units_data = facts['us-gaap'][tag].get('units', {})
                    
                    # Look for USD values first
                    if 'USD' in units_data:
                        values = units_data['USD']
                        # Get the most recent value
                        if values:
                            latest_value = max(values, key=lambda x: x.get('end', ''))
                            metrics[metric_name] = {
                                'value': latest_value.get('val'),
                                'end_date': latest_value.get('end'),
                                'form': latest_value.get('form'),
                            }
                            break
                    
                    # If no USD, try shares or other units
                    elif 'shares' in units_data:
                        values = units_data['shares']
                        if values:
                            latest_value = max(values, key=lambda x: x.get('end', ''))
                            metrics[metric_name] = {
                                'value': latest_value.get('val'),
                                'end_date': latest_value.get('end'),
                                'form': latest_value.get('form'),
                            }
                            break
        
        return metrics
    
    def analyze_8k_filings(self, cik, days_back=365):
        """
        Analyze 8-K filings for material events (potential liquidity events)
        
        Args:
            cik: Company CIK
            days_back: Number of days to look back
        
        Returns:
            List of material events
        """
        filings = self.get_company_filings(cik, form_type='8-K', limit=50)
        cutoff_date = (datetime.now() - timedelta(days=days_back)).date()
        
        events = []
        
        for filing in filings:
            filing_date_str = filing.get('filing_date')
            if not filing_date_str:
                continue
            
            try:
                filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
                if filing_date < cutoff_date:
                    continue
            except ValueError:
                continue
            
            # Get the actual 8-K document content
            accession = filing.get('accession_number', '').replace('-', '')
            primary_doc = filing.get('primary_document')
            
            if accession and primary_doc:
                doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{primary_doc}"
                event_data = self._analyze_8k_document(doc_url, filing)
                if event_data:
                    events.append(event_data)
        
        return events
    
    def _analyze_8k_document(self, doc_url, filing_info):
        """
        Analyze individual 8-K document for material events
        
        Args:
            doc_url: URL to the 8-K document
            filing_info: Basic filing information
        
        Returns:
            Event data if significant event found, None otherwise
        """
        try:
            # Make request to get document content
            self._respect_rate_limit()
            response = self.session.get(doc_url, timeout=30)
            
            if response.status_code != 200:
                return None
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text().lower()
            
            # Look for keywords indicating liquidity events
            liquidity_keywords = [
                'acquisition', 'merger', 'purchase', 'sale', 'divestiture',
                'liquidation', 'bankruptcy', 'restructuring', 'spin-off',
                'joint venture', 'asset sale', 'property sale', 'real estate',
                'portfolio', 'transaction', 'agreement', 'financing'
            ]
            
            # Check if any keywords are present
            found_keywords = [kw for kw in liquidity_keywords if kw in text_content]
            
            if not found_keywords:
                return None
            
            # Extract monetary amounts if present
            amount_patterns = [
                r'\$(\d+(?:\.\d+)?)\s*billion',
                r'\$(\d+(?:\.\d+)?)\s*million',
                r'\$(\d{1,3}(?:,\d{3})+)',
            ]
            
            amounts = []
            for pattern in amount_patterns:
                matches = re.findall(pattern, text_content)
                for match in matches:
                    try:
                        amount = float(match.replace(',', ''))
                        if 'billion' in pattern:
                            amount *= 1_000_000_000
                        elif 'million' in pattern:
                            amount *= 1_000_000
                        amounts.append(amount)
                    except ValueError:
                        continue
            
            # Return event data
            event_data = {
                'filing_date': filing_info.get('filing_date'),
                'form': filing_info.get('form'),
                'cik': filing_info.get('cik'),
                'keywords': found_keywords,
                'document_url': doc_url,
                'amounts': amounts,
                'max_amount': max(amounts) if amounts else None,
            }
            
            return event_data
            
        except Exception as e:
            print(f"Error analyzing 8-K document {doc_url}: {e}")
            return None


class SECRealEstateAnalyzer:
    """
    Analyzer for SEC data focused on real estate companies and their liquidity events
    """
    
    def __init__(self):
        self.sec_api = SECEdgarAPI()
    
    def find_real_estate_liquidity_events(self, days_back=365):
        """
        Find liquidity events from SEC filings for real estate companies
        
        Args:
            days_back: Number of days to look back for events
        
        Returns:
            List of liquidity events from SEC data
        """
        events = []
        
        # Get real estate companies
        re_companies = self.sec_api.get_real_estate_companies()
        
        for company in re_companies[:10]:  # Limit to prevent too many API calls
            cik = company.get('cik')
            if not cik:
                continue
            
            try:
                # Analyze 8-K filings for material events
                company_events = self.sec_api.analyze_8k_filings(cik, days_back)
                
                for event in company_events:
                    # Enrich event data with company information
                    event.update({
                        'company_name': company.get('title'),
                        'ticker': company.get('ticker'),
                        'source': 'SEC_8K',
                    })
                    events.append(event)
                
            except Exception as e:
                print(f"Error processing company {company.get('title')}: {e}")
                continue
        
        return events
    
    def get_company_financial_profile(self, ticker_or_cik):
        """
        Get comprehensive financial profile for a company
        
        Args:
            ticker_or_cik: Company ticker symbol or CIK
        
        Returns:
            Dictionary with financial profile information
        """
        # Search for company if ticker provided
        if len(ticker_or_cik) <= 5:  # Assume ticker
            companies = self.sec_api.search_companies(ticker_or_cik, limit=1)
            if not companies:
                return None
            company = companies[0]
            cik = company['cik']
        else:
            cik = ticker_or_cik.zfill(10)
            company = {'cik': cik}
        
        # Get company facts
        facts = self.sec_api.get_company_facts(cik)
        if not facts:
            return None
        
        # Extract financial metrics
        metrics = self.sec_api.extract_financial_metrics(facts)
        
        # Get recent filings
        recent_filings = self.sec_api.get_company_filings(cik, limit=10)
        
        # Analyze for liquidity events
        liquidity_events = self.sec_api.analyze_8k_filings(cik, days_back=365)
        
        profile = {
            'company_info': {
                'cik': cik,
                'name': company.get('title') or facts.get('entityName'),
                'ticker': company.get('ticker'),
            },
            'financial_metrics': metrics,
            'recent_filings': recent_filings,
            'liquidity_events': liquidity_events,
            'analysis_date': datetime.now().isoformat(),
        }
        
        return profile
    
    def correlate_with_real_estate_data(self, sec_events):
        """
        Correlate SEC liquidity events with StreetEasy real estate data
        
        Args:
            sec_events: List of SEC liquidity events
        
        Returns:
            List of correlated events with real estate context
        """
        correlated_events = []
        
        for sec_event in sec_events:
            company_name = sec_event.get('company_name', '')
            ticker = sec_event.get('ticker', '')
            filing_date = sec_event.get('filing_date')
            
            if not filing_date:
                continue
            
            try:
                filing_date_obj = datetime.strptime(filing_date, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            # Look for related real estate transactions around the same time
            date_range_start = filing_date_obj - timedelta(days=30)
            date_range_end = filing_date_obj + timedelta(days=30)
            
            # Search for related StreetEasy liquidity events
            related_re_events = StreetEasyLiquidityEvent.objects.filter(
                transaction_date__gte=date_range_start,
                transaction_date__lte=date_range_end
            )
            
            # Look for name matches or related entities
            matching_events = []
            for re_event in related_re_events:
                if (company_name.lower() in re_event.seller_name.lower() or
                    company_name.lower() in re_event.buyer_name.lower() or
                    ticker.lower() in re_event.seller_name.lower() or
                    ticker.lower() in re_event.buyer_name.lower()):
                    matching_events.append(re_event.to_dict())
            
            # Create correlated event
            correlated_event = {
                'sec_event': sec_event,
                'related_real_estate_events': matching_events,
                'correlation_score': len(matching_events),
                'time_proximity_days': 0,  # Will be calculated based on closest match
            }
            
            if matching_events:
                # Calculate time proximity to closest real estate event
                min_days_diff = min([
                    abs((filing_date_obj - datetime.strptime(
                        re_event['transaction_date'], '%Y-%m-%d'
                    ).date()).days)
                    for re_event in matching_events
                ])
                correlated_event['time_proximity_days'] = min_days_diff
            
            correlated_events.append(correlated_event)
        
        return correlated_events
    
    def answer_sec_question(self, question):
        """
        Answer natural language questions about SEC data and real estate companies
        
        Examples:
        - "What SEC filings has Simon Property Group made recently?"
        - "Show me financial data for Prologis"
        - "Find recent 8-K filings for real estate companies"
        """
        question_lower = question.lower()
        
        # Extract company name or ticker from question
        company_name = None
        for word in question.split():
            if len(word) <= 5 and word.isupper():  # Likely a ticker
                company_name = word
                break
        
        # If no ticker found, look for company names
        if not company_name:
            # Common real estate company names to look for
            re_companies = [
                'simon', 'prologis', 'equinix', 'public storage', 'avalonbay',
                'equity residential', 'welltower', 'digital realty', 'realty income',
                'ventas', 'essex', 'camden', 'boston properties', 'vornado',
                'kimco', 'regency', 'federal realty', 'host hotels'
            ]
            
            for company in re_companies:
                if company in question_lower:
                    company_name = company
                    break
        
        if company_name:
            # Get company profile
            profile = self.get_company_financial_profile(company_name)
            if profile:
                company_info = profile['company_info']
                metrics = profile['financial_metrics']
                filings = profile['recent_filings']
                
                answer = f"SEC Data for {company_info['name']} ({company_info.get('ticker', 'N/A')}):\n\n"
                
                if metrics:
                    answer += "Key Financial Metrics:\n"
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
                            answer += f"  - {metric}: {value_str}\n"
                
                if filings:
                    answer += f"\nRecent SEC Filings (last {len(filings)}):\n"
                    for filing in filings[:5]:
                        answer += f"  - {filing['form']} filed on {filing['filing_date']}\n"
                
                return answer
            else:
                return f"Could not find SEC data for {company_name}"
        
        # General questions about real estate companies
        elif any(phrase in question_lower for phrase in ['real estate', 'reit', 'property']):
            if 'filings' in question_lower or '8-k' in question_lower:
                events = self.find_real_estate_liquidity_events(days_back=90)
                if events:
                    answer = f"Recent SEC liquidity events for real estate companies:\n\n"
                    for i, event in enumerate(events[:5], 1):
                        answer += f"{i}. {event['company_name']} ({event['ticker']})\n"
                        answer += f"   Filed: {event['filing_date']}\n"
                        answer += f"   Keywords: {', '.join(event['keywords'][:3])}\n"
                        if event.get('max_amount'):
                            amount = event['max_amount']
                            if amount >= 1000000000:
                                amount_str = f"${amount/1000000000:.1f}B"
                            else:
                                amount_str = f"${amount/1000000:.1f}M"
                            answer += f"   Amount mentioned: {amount_str}\n"
                        answer += "\n"
                    return answer
                else:
                    return "No recent SEC liquidity events found for real estate companies."
        
        return "I can help you find SEC filing information for real estate companies. Try asking about a specific company ticker or recent filings."