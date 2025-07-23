import requests
import re
import json
import time
import hashlib
from datetime import datetime, timedelta, date
from decimal import Decimal
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from django.utils import timezone
from .models import StreetEasyLiquidityEvent, StreetEasyEntity


class LiquidityEventScraper:
    """
    Scraper for major liquidity events and real estate transactions.
    Sources include StreetEasy sold data, news articles, and public records.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.rate_limit_delay = 3  # More conservative for news sources
        self.last_request_time = 0
        
        # News sources that cover major NYC real estate transactions
        self.news_sources = [
            'https://www.therealdeal.com',
            'https://www.crainsnewyork.com',
            'https://nypost.com/section/real-estate',
            'https://commercialobserver.com',
        ]
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url, params=None):
        """Make a rate-limited request"""
        self._respect_rate_limit()
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def scrape_streeteasy_sold_data(self, min_amount=1000000, days_back=365):
        """
        Scrape high-value sold properties from StreetEasy
        
        Args:
            min_amount: Minimum transaction amount to consider (default $1M)
            days_back: Number of days to look back (default 365)
        """
        events = []
        
        # StreetEasy sold listings URL
        base_url = "https://streeteasy.com/for-sale/nyc/status:sold"
        
        # Date range for the past year
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'sold_gte': start_date.strftime('%Y-%m-%d'),
            'sold_lt': end_date.strftime('%Y-%m-%d'),
            'price_min': min_amount,
        }
        
        response = self._make_request(base_url, params=params)
        if not response:
            return events
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for sold property listings
        property_cards = soup.find_all(['div', 'article'], class_=re.compile(r'listing|item|sold'))
        
        for card in property_cards:
            try:
                event_data = self._extract_sold_property_data(card)
                if event_data and event_data.get('transaction_amount', 0) >= min_amount:
                    events.append(event_data)
            except Exception as e:
                print(f"Error extracting sold property: {e}")
                continue
        
        return events
    
    def _extract_sold_property_data(self, card):
        """Extract transaction data from a sold property card"""
        data = {}
        
        # Extract sale price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price|sold'))
        if price_elem:
            price_text = price_elem.get_text()
            price_match = re.search(r'\$?([\d,]+)', price_text.replace(',', ''))
            if price_match:
                data['transaction_amount'] = Decimal(price_match.group(1))
        
        # Extract address
        address_elem = card.find(['div', 'span'], class_=re.compile(r'address|location'))
        if address_elem:
            data['property_address'] = address_elem.get_text().strip()
        
        # Extract sold date
        date_elem = card.find(['span', 'div'], class_=re.compile(r'date|sold'))
        if date_elem:
            date_text = date_elem.get_text()
            # Try to parse various date formats
            for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y']:
                try:
                    parsed_date = datetime.strptime(date_text.strip(), date_format).date()
                    data['transaction_date'] = parsed_date
                    break
                except ValueError:
                    continue
        
        # Set default values
        data['event_type'] = 'sale'
        data['event_id'] = self._generate_event_id(data)
        
        # Extract property details if available
        details_elem = card.find(['div', 'span'], class_=re.compile(r'details|specs'))
        if details_elem:
            details_text = details_elem.get_text()
            
            # Extract square footage
            sqft_match = re.search(r'(\d+)\s*sq\.?\s*ft', details_text, re.IGNORECASE)
            if sqft_match:
                data['square_footage'] = int(sqft_match.group(1))
            
            # Calculate price per sqft
            if data.get('square_footage') and data.get('transaction_amount'):
                data['price_per_sqft'] = data['transaction_amount'] / data['square_footage']
        
        return data if data.get('transaction_amount') else None
    
    def scrape_news_articles(self, days_back=30):
        """
        Scrape news articles for major real estate transactions
        
        Args:
            days_back: Number of days to look back for articles
        """
        events = []
        
        # Keywords to search for in articles
        keywords = [
            'sold for', 'purchased for', 'acquired for', 'billion', 'million',
            'real estate deal', 'property sale', 'record sale', 'liquidity event'
        ]
        
        for source_url in self.news_sources:
            try:
                # This is a simplified approach - in practice, you'd need
                # specific scrapers for each news source
                source_events = self._scrape_news_source(source_url, keywords, days_back)
                events.extend(source_events)
            except Exception as e:
                print(f"Error scraping {source_url}: {e}")
                continue
        
        return events
    
    def _scrape_news_source(self, source_url, keywords, days_back):
        """Scrape a specific news source for transaction articles"""
        events = []
        
        response = self._make_request(source_url)
        if not response:
            return events
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find article links
        article_links = soup.find_all('a', href=True)
        
        for link in article_links[:20]:  # Limit to prevent too many requests
            href = link.get('href')
            if not href:
                continue
            
            # Check if the link text contains transaction keywords
            link_text = link.get_text().lower()
            if any(keyword in link_text for keyword in keywords):
                article_url = urljoin(source_url, href)
                article_data = self._extract_article_transaction_data(article_url)
                if article_data:
                    events.append(article_data)
        
        return events
    
    def _extract_article_transaction_data(self, article_url):
        """Extract transaction data from a news article"""
        response = self._make_request(article_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get article text
        article_body = soup.find(['div', 'article'], class_=re.compile(r'content|body|article'))
        if not article_body:
            article_body = soup.find('body')
        
        if not article_body:
            return None
        
        article_text = article_body.get_text()
        
        # Extract transaction amount using regex patterns
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*billion',
            r'\$(\d+(?:\.\d+)?)\s*million',
            r'\$(\d{1,3}(?:,\d{3})+)',
            r'sold for \$?([\d,]+)',
            r'purchased for \$?([\d,]+)',
            r'acquired for \$?([\d,]+)',
        ]
        
        transaction_amount = None
        for pattern in amount_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    if 'billion' in match.group(0).lower():
                        amount *= 1_000_000_000
                    elif 'million' in match.group(0).lower():
                        amount *= 1_000_000
                    transaction_amount = Decimal(str(amount))
                    break
                except (ValueError, IndexError):
                    continue
        
        if not transaction_amount or transaction_amount < 1000000:  # Less than $1M
            return None
        
        # Extract other details
        data = {
            'transaction_amount': transaction_amount,
            'event_type': 'sale',
            'source_url': article_url,
            'source_publication': urlparse(article_url).netloc,
        }
        
        # Extract names of parties involved
        # Look for patterns like "Company A sold to Company B"
        name_patterns = [
            r'(\w+(?:\s+\w+)*)\s+sold\s+(?:to\s+)?(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+purchased\s+(?:from\s+)?(\w+(?:\s+\w+)*)',
            r'(\w+(?:\s+\w+)*)\s+acquired\s+(?:from\s+)?(\w+(?:\s+\w+)*)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                data['seller_name'] = match.group(1).strip()
                data['buyer_name'] = match.group(2).strip()
                break
        
        # Extract address if mentioned
        address_patterns = [
            r'(\d+\s+\w+(?:\s+\w+)*(?:\s+Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd))',
            r'(building at \d+\s+\w+(?:\s+\w+)*)',
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, article_text, re.IGNORECASE)
            if match:
                data['property_address'] = match.group(1).strip()
                break
        
        # Try to extract date from article
        # This is complex and would need more sophisticated parsing
        data['transaction_date'] = date.today()  # Default to today
        
        data['event_id'] = self._generate_event_id(data)
        
        return data
    
    def _generate_event_id(self, event_data):
        """Generate a unique event ID based on transaction details"""
        id_string = f"{event_data.get('seller_name', '')}-{event_data.get('transaction_amount', 0)}-{event_data.get('transaction_date', date.today())}"
        return hashlib.md5(id_string.encode()).hexdigest()[:20]
    
    def save_liquidity_events(self, events_data):
        """
        Save liquidity events to the database
        
        Args:
            events_data: List of event dictionaries
            
        Returns:
            tuple: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        for event_data in events_data:
            if not event_data.get('event_id'):
                continue
            
            # Check if event already exists
            existing_event = StreetEasyLiquidityEvent.objects.filter(
                event_id=event_data['event_id']
            ).first()
            
            if existing_event:
                # Update existing event
                for key, value in event_data.items():
                    if hasattr(existing_event, key) and value is not None:
                        setattr(existing_event, key, value)
                existing_event.save()
                updated_count += 1
            else:
                # Create new event
                StreetEasyLiquidityEvent.objects.create(**event_data)
                created_count += 1
            
            # Update or create entities mentioned in the transaction
            self._update_entities_from_event(event_data)
        
        return created_count, updated_count
    
    def _update_entities_from_event(self, event_data):
        """Update entity records based on transaction data"""
        for party_type in ['seller', 'buyer']:
            name_key = f'{party_type}_name'
            type_key = f'{party_type}_type'
            
            if not event_data.get(name_key):
                continue
            
            entity_name = event_data[name_key]
            entity_type = event_data.get(type_key, 'company')
            
            # Generate entity ID
            entity_id = hashlib.md5(entity_name.lower().encode()).hexdigest()[:20]
            
            # Get or create entity
            entity, created = StreetEasyEntity.objects.get_or_create(
                entity_id=entity_id,
                defaults={
                    'name': entity_name,
                    'entity_type': entity_type,
                }
            )
            
            # Update entity metrics
            entity.update_metrics()


class LiquidityAnalyzer:
    """
    Analyzer for liquidity events and transaction patterns
    """
    
    def get_largest_liquidity_events(self, timeframe_days=365, limit=10):
        """
        Get the largest liquidity events within a timeframe
        
        Args:
            timeframe_days: Number of days to look back
            limit: Maximum number of events to return
        """
        cutoff_date = timezone.now().date() - timedelta(days=timeframe_days)
        
        events = StreetEasyLiquidityEvent.objects.filter(
            transaction_date__gte=cutoff_date
        ).order_by('-transaction_amount')[:limit]
        
        return [event.to_dict() for event in events]
    
    def get_most_active_entities(self, timeframe_days=365, limit=10):
        """
        Get entities with the most transaction volume in a timeframe
        """
        cutoff_date = timezone.now().date() - timedelta(days=timeframe_days)
        
        # Get entities involved in transactions within the timeframe
        recent_events = StreetEasyLiquidityEvent.objects.filter(
            transaction_date__gte=cutoff_date
        )
        
        # Update metrics for all entities
        for entity in StreetEasyEntity.objects.all():
            entity.update_metrics()
        
        # Get top entities by transaction volume
        entities = StreetEasyEntity.objects.filter(
            last_transaction_date__gte=cutoff_date
        ).order_by('-total_transaction_volume')[:limit]
        
        return [entity.to_dict() for entity in entities]
    
    def answer_liquidity_question(self, question):
        """
        Answer natural language questions about liquidity events
        
        Examples:
        - "Who has had the largest liquidity event in the past year?"
        - "What are the biggest real estate deals this year?"
        - "Which company has sold the most properties?"
        """
        question_lower = question.lower()
        
        # Determine timeframe
        if 'past year' in question_lower or 'this year' in question_lower:
            timeframe_days = 365
        elif 'past month' in question_lower or 'this month' in question_lower:
            timeframe_days = 30
        elif 'past week' in question_lower or 'this week' in question_lower:
            timeframe_days = 7
        else:
            timeframe_days = 365  # default to past year
        
        # Determine what type of answer is needed
        if any(phrase in question_lower for phrase in ['largest', 'biggest', 'major', 'significant']):
            if any(phrase in question_lower for phrase in ['event', 'deal', 'transaction', 'sale']):
                # They want the largest individual transactions
                events = self.get_largest_liquidity_events(timeframe_days, 5)
                
                if events:
                    answer = f"The largest liquidity events in the past {timeframe_days} days:\n\n"
                    for i, event in enumerate(events, 1):
                        answer += f"{i}. {event['seller_name']} - {event['formatted_amount']}"
                        if event['property_address']:
                            answer += f" ({event['property_address']})"
                        answer += f" on {event['transaction_date']}\n"
                    return answer
                else:
                    return f"No major liquidity events found in the past {timeframe_days} days."
            
            elif any(phrase in question_lower for phrase in ['who', 'entity', 'company', 'person']):
                # They want the most active entities
                entities = self.get_most_active_entities(timeframe_days, 5)
                
                if entities:
                    answer = f"Entities with the largest transaction volume in the past {timeframe_days} days:\n\n"
                    for i, entity in enumerate(entities, 1):
                        volume = entity['total_transaction_volume']
                        if volume >= 1_000_000_000:
                            volume_str = f"${volume/1_000_000_000:.1f}B"
                        elif volume >= 1_000_000:
                            volume_str = f"${volume/1_000_000:.1f}M"
                        else:
                            volume_str = f"${volume:,.0f}"
                        
                        answer += f"{i}. {entity['name']} ({entity['entity_type']}) - {volume_str} "
                        answer += f"across {entity['transaction_count']} transactions\n"
                    return answer
                else:
                    return f"No active entities found in the past {timeframe_days} days."
        
        # Default response
        return "I can help you find information about liquidity events. Try asking about 'largest deals this year' or 'most active companies'."