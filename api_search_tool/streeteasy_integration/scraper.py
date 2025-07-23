import requests
import re
import json
import time
import hashlib
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from .models import StreetEasyProperty, StreetEasySearch, StreetEasyAPIKey


class StreetEasyScraper:
    """
    StreetEasy scraper that extracts property data using web scraping techniques.
    This scraper respects rate limits and follows ethical scraping practices.
    """
    
    def __init__(self):
        self.base_url = "https://streeteasy.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.rate_limit_delay = 2  # seconds between requests
        self.last_request_time = 0
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(self, url, params=None):
        """Make a rate-limited request to StreetEasy"""
        self._respect_rate_limit()
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def search_properties(self, search_params):
        """
        Search for properties based on given parameters
        
        Args:
            search_params (dict): Search parameters including:
                - property_type: 'rental' or 'sale'
                - neighborhood: neighborhood name
                - min_price: minimum price
                - max_price: maximum price
                - min_bedrooms: minimum bedrooms
                - max_bedrooms: maximum bedrooms
                - amenities: list of amenities
        
        Returns:
            list: List of property data dictionaries
        """
        # Build search URL
        property_type = search_params.get('property_type', 'rental')
        if property_type == 'rental':
            search_url = f"{self.base_url}/for-rent"
        else:
            search_url = f"{self.base_url}/for-sale"
        
        # Build query parameters
        params = {}
        
        if search_params.get('neighborhood'):
            params['neighborhoods[]'] = search_params['neighborhood']
        
        if search_params.get('min_price'):
            if property_type == 'rental':
                params['min_price'] = int(search_params['min_price'])
            else:
                params['price_min'] = int(search_params['min_price'])
        
        if search_params.get('max_price'):
            if property_type == 'rental':
                params['max_price'] = int(search_params['max_price'])
            else:
                params['price_max'] = int(search_params['max_price'])
        
        if search_params.get('min_bedrooms'):
            params['min_beds'] = int(search_params['min_bedrooms'])
        
        if search_params.get('max_bedrooms'):
            params['max_beds'] = int(search_params['max_bedrooms'])
        
        # Make initial search request
        response = self._make_request(search_url, params=params)
        if not response:
            return []
        
        # Parse search results
        properties = []
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for property listings - StreetEasy uses various CSS classes
        property_cards = soup.find_all(['div', 'article'], class_=re.compile(r'listing|SearchResult|item'))
        
        if not property_cards:
            # Try alternative selectors
            property_cards = soup.find_all('div', {'data-listing-id': True})
        
        for card in property_cards:
            try:
                property_data = self._extract_property_from_card(card, property_type)
                if property_data:
                    properties.append(property_data)
            except Exception as e:
                print(f"Error extracting property data: {e}")
                continue
        
        # Try to get more pages if available
        next_page_link = soup.find('a', text=re.compile(r'Next|»'))
        page_count = 1
        max_pages = 5  # Limit to prevent excessive scraping
        
        while next_page_link and page_count < max_pages:
            next_url = urljoin(self.base_url, next_page_link.get('href'))
            response = self._make_request(next_url)
            if not response:
                break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            property_cards = soup.find_all(['div', 'article'], class_=re.compile(r'listing|SearchResult|item'))
            
            for card in property_cards:
                try:
                    property_data = self._extract_property_from_card(card, property_type)
                    if property_data:
                        properties.append(property_data)
                except Exception as e:
                    continue
            
            next_page_link = soup.find('a', text=re.compile(r'Next|»'))
            page_count += 1
        
        return properties
    
    def _extract_property_from_card(self, card, property_type):
        """Extract property data from a search result card"""
        property_data = {}
        
        # Extract StreetEasy ID
        listing_id = card.get('data-listing-id')
        if not listing_id:
            # Try to extract from URL
            link = card.find('a', href=True)
            if link:
                href = link.get('href')
                if href:
                    id_match = re.search(r'/(\d+)', href)
                    if id_match:
                        listing_id = id_match.group(1)
        
        if not listing_id:
            return None
        
        property_data['street_easy_id'] = listing_id
        property_data['property_type'] = property_type
        
        # Extract price
        price_elem = card.find(['span', 'div'], class_=re.compile(r'price|amount'))
        if price_elem:
            price_text = price_elem.get_text().strip()
            price_match = re.search(r'\$?([\d,]+)', price_text.replace(',', ''))
            if price_match:
                property_data['price'] = Decimal(price_match.group(1))
        
        # Extract address
        address_elem = card.find(['div', 'span'], class_=re.compile(r'address|location'))
        if address_elem:
            property_data['address'] = address_elem.get_text().strip()
        
        # Extract bedrooms/bathrooms
        details_elem = card.find(['div', 'span'], class_=re.compile(r'details|beds|baths'))
        if details_elem:
            details_text = details_elem.get_text()
            
            # Extract bedrooms
            bed_match = re.search(r'(\d+)\s*(?:bed|br)', details_text, re.IGNORECASE)
            if bed_match:
                property_data['bedrooms'] = int(bed_match.group(1))
            elif 'studio' in details_text.lower():
                property_data['bedrooms'] = 0
            
            # Extract bathrooms
            bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', details_text, re.IGNORECASE)
            if bath_match:
                property_data['bathrooms'] = Decimal(bath_match.group(1))
        
        # Extract unit type
        unit_elem = card.find(['div', 'span'], text=re.compile(r'Studio|1BR|2BR|3BR|4BR'))
        if unit_elem:
            property_data['unit_type'] = unit_elem.get_text().strip()
        
        # Extract listing URL
        link = card.find('a', href=True)
        if link:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    property_data['listing_url'] = urljoin(self.base_url, href)
                else:
                    property_data['listing_url'] = href
        
        # Extract neighborhood if available
        neighborhood_elem = card.find(['div', 'span'], class_=re.compile(r'neighborhood|area'))
        if neighborhood_elem:
            property_data['neighborhood'] = neighborhood_elem.get_text().strip()
        
        return property_data
    
    def get_property_details(self, listing_url):
        """
        Get detailed information about a specific property
        
        Args:
            listing_url (str): Full URL to the property listing
            
        Returns:
            dict: Detailed property information
        """
        response = self._make_request(listing_url)
        if not response:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        details = {}
        
        try:
            # Extract JSON-LD structured data if available
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Apartment':
                        details.update(self._parse_json_ld(data))
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Extract additional details from the page
            details.update(self._extract_property_details(soup))
            
        except Exception as e:
            print(f"Error extracting property details: {e}")
        
        return details
    
    def _parse_json_ld(self, data):
        """Parse JSON-LD structured data"""
        details = {}
        
        if 'address' in data:
            address_data = data['address']
            if isinstance(address_data, dict):
                details['address'] = address_data.get('streetAddress', '')
                details['neighborhood'] = address_data.get('addressLocality', '')
                details['zipcode'] = address_data.get('postalCode', '')
        
        if 'geo' in data:
            geo_data = data['geo']
            if isinstance(geo_data, dict):
                details['latitude'] = Decimal(str(geo_data.get('latitude', 0)))
                details['longitude'] = Decimal(str(geo_data.get('longitude', 0)))
        
        if 'numberOfRooms' in data:
            details['bedrooms'] = int(data['numberOfRooms'])
        
        if 'floorSize' in data:
            # floorSize might be in different formats
            floor_size = data['floorSize']
            if isinstance(floor_size, dict) and 'value' in floor_size:
                details['square_feet'] = int(floor_size['value'])
            elif isinstance(floor_size, (int, float)):
                details['square_feet'] = int(floor_size)
        
        return details
    
    def _extract_property_details(self, soup):
        """Extract additional property details from the page HTML"""
        details = {}
        
        # Extract square footage
        sqft_elem = soup.find(text=re.compile(r'\d+\s*sq\.?\s*ft', re.IGNORECASE))
        if sqft_elem:
            sqft_match = re.search(r'(\d+)\s*sq\.?\s*ft', sqft_elem, re.IGNORECASE)
            if sqft_match:
                details['square_feet'] = int(sqft_match.group(1))
        
        # Extract amenities
        amenities = []
        amenity_sections = soup.find_all(['div', 'ul'], class_=re.compile(r'amenities|features'))
        for section in amenity_sections:
            amenity_items = section.find_all(['li', 'span'])
            for item in amenity_items:
                amenity_text = item.get_text().strip()
                if amenity_text and len(amenity_text) < 100:  # Filter out long text
                    amenities.append(amenity_text)
        
        if amenities:
            details['amenities'] = list(set(amenities))  # Remove duplicates
        
        # Extract agent information
        agent_elem = soup.find(['div', 'span'], class_=re.compile(r'agent|broker'))
        if agent_elem:
            agent_name = agent_elem.find(['span', 'div'], class_=re.compile(r'name'))
            if agent_name:
                details['agent_name'] = agent_name.get_text().strip()
            
            agent_company = agent_elem.find(['span', 'div'], class_=re.compile(r'company|brokerage'))
            if agent_company:
                details['agent_company'] = agent_company.get_text().strip()
        
        # Extract building information
        building_elem = soup.find(['div', 'span'], class_=re.compile(r'building'))
        if building_elem:
            building_name = building_elem.find(['h1', 'h2', 'span'], class_=re.compile(r'name|title'))
            if building_name:
                details['building_name'] = building_name.get_text().strip()
        
        # Extract images
        image_urls = []
        img_elements = soup.find_all('img', src=True)
        for img in img_elements:
            src = img.get('src')
            if src and ('streeteasy' in src or 'listing' in src):
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(self.base_url, src)
                image_urls.append(src)
        
        if image_urls:
            details['image_urls'] = image_urls[:10]  # Limit to 10 images
        
        return details
    
    def save_properties(self, properties_data, search_params=None):
        """
        Save scraped properties to the database
        
        Args:
            properties_data (list): List of property dictionaries
            search_params (dict): Original search parameters
            
        Returns:
            tuple: (created_count, updated_count)
        """
        created_count = 0
        updated_count = 0
        
        for prop_data in properties_data:
            if not prop_data.get('street_easy_id'):
                continue
            
            # Check if property already exists
            existing_property = StreetEasyProperty.objects.filter(
                street_easy_id=prop_data['street_easy_id']
            ).first()
            
            if existing_property:
                # Update existing property
                for key, value in prop_data.items():
                    if hasattr(existing_property, key) and value is not None:
                        setattr(existing_property, key, value)
                existing_property.last_scraped = timezone.now()
                existing_property.save()
                updated_count += 1
            else:
                # Create new property
                prop_data['last_scraped'] = timezone.now()
                prop_data['raw_data'] = prop_data.copy()  # Store raw data
                StreetEasyProperty.objects.create(**prop_data)
                created_count += 1
        
        # Save search record if provided
        if search_params:
            search_id = self._generate_search_id(search_params)
            search_record, created = StreetEasySearch.objects.get_or_create(
                search_id=search_id,
                defaults={
                    'search_parameters': search_params,
                    'results_count': len(properties_data),
                    'min_price': search_params.get('min_price'),
                    'max_price': search_params.get('max_price'),
                    'min_bedrooms': search_params.get('min_bedrooms'),
                    'max_bedrooms': search_params.get('max_bedrooms'),
                    'neighborhood': search_params.get('neighborhood', ''),
                    'property_type': search_params.get('property_type', ''),
                }
            )
            
            if not created:
                search_record.results_count = len(properties_data)
                search_record.last_executed = timezone.now()
                search_record.save()
        
        return created_count, updated_count
    
    def _generate_search_id(self, search_params):
        """Generate a unique ID for a search based on parameters"""
        search_string = json.dumps(search_params, sort_keys=True)
        return hashlib.md5(search_string.encode()).hexdigest()[:20]


class StreetEasyAgent:
    """
    High-level agent interface for querying StreetEasy data
    """
    
    def __init__(self):
        self.scraper = StreetEasyScraper()
    
    def search_rentals(self, neighborhood=None, min_price=None, max_price=None, 
                      min_bedrooms=None, max_bedrooms=None, **kwargs):
        """Search for rental properties"""
        search_params = {
            'property_type': 'rental',
            'neighborhood': neighborhood,
            'min_price': min_price,
            'max_price': max_price,
            'min_bedrooms': min_bedrooms,
            'max_bedrooms': max_bedrooms,
        }
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        # First, check if we have recent data in the database
        recent_cutoff = timezone.now() - timedelta(hours=24)
        existing_properties = StreetEasyProperty.objects.filter(
            property_type='rental',
            last_scraped__gte=recent_cutoff
        )
        
        # Apply filters to existing data
        if neighborhood:
            existing_properties = existing_properties.filter(
                neighborhood__icontains=neighborhood
            )
        if min_price:
            existing_properties = existing_properties.filter(price__gte=min_price)
        if max_price:
            existing_properties = existing_properties.filter(price__lte=max_price)
        if min_bedrooms is not None:
            existing_properties = existing_properties.filter(bedrooms__gte=min_bedrooms)
        if max_bedrooms is not None:
            existing_properties = existing_properties.filter(bedrooms__lte=max_bedrooms)
        
        # If we have enough recent data, return it
        if existing_properties.count() >= 10:
            return [prop.to_dict() for prop in existing_properties[:50]]
        
        # Otherwise, scrape new data
        properties_data = self.scraper.search_properties(search_params)
        
        # Get detailed information for the first few properties
        for i, prop_data in enumerate(properties_data[:5]):  # Limit to avoid too many requests
            if prop_data.get('listing_url'):
                details = self.scraper.get_property_details(prop_data['listing_url'])
                prop_data.update(details)
        
        # Save to database
        created, updated = self.scraper.save_properties(properties_data, search_params)
        
        return properties_data
    
    def search_sales(self, neighborhood=None, min_price=None, max_price=None, 
                    min_bedrooms=None, max_bedrooms=None, **kwargs):
        """Search for properties for sale"""
        search_params = {
            'property_type': 'sale',
            'neighborhood': neighborhood,
            'min_price': min_price,
            'max_price': max_price,
            'min_bedrooms': min_bedrooms,
            'max_bedrooms': max_bedrooms,
        }
        
        # Remove None values
        search_params = {k: v for k, v in search_params.items() if v is not None}
        
        # Check for recent data
        recent_cutoff = timezone.now() - timedelta(hours=24)
        existing_properties = StreetEasyProperty.objects.filter(
            property_type='sale',
            last_scraped__gte=recent_cutoff
        )
        
        # Apply filters
        if neighborhood:
            existing_properties = existing_properties.filter(
                neighborhood__icontains=neighborhood
            )
        if min_price:
            existing_properties = existing_properties.filter(price__gte=min_price)
        if max_price:
            existing_properties = existing_properties.filter(price__lte=max_price)
        if min_bedrooms is not None:
            existing_properties = existing_properties.filter(bedrooms__gte=min_bedrooms)
        if max_bedrooms is not None:
            existing_properties = existing_properties.filter(bedrooms__lte=max_bedrooms)
        
        if existing_properties.count() >= 10:
            return [prop.to_dict() for prop in existing_properties[:50]]
        
        # Scrape new data
        properties_data = self.scraper.search_properties(search_params)
        
        # Get detailed information for the first few properties
        for i, prop_data in enumerate(properties_data[:5]):
            if prop_data.get('listing_url'):
                details = self.scraper.get_property_details(prop_data['listing_url'])
                prop_data.update(details)
        
        # Save to database
        created, updated = self.scraper.save_properties(properties_data, search_params)
        
        return properties_data
    
    def get_property_by_id(self, street_easy_id):
        """Get a specific property by its StreetEasy ID"""
        try:
            property_obj = StreetEasyProperty.objects.get(street_easy_id=street_easy_id)
            return property_obj.to_dict()
        except StreetEasyProperty.DoesNotExist:
            return None
    
    def get_neighborhoods(self):
        """Get list of available neighborhoods"""
        neighborhoods = StreetEasyProperty.objects.values_list(
            'neighborhood', flat=True
        ).distinct().exclude(neighborhood='')
        return list(neighborhoods)
    
    def get_price_range(self, property_type='rental', neighborhood=None):
        """Get price range for properties"""
        queryset = StreetEasyProperty.objects.filter(property_type=property_type)
        
        if neighborhood:
            queryset = queryset.filter(neighborhood__icontains=neighborhood)
        
        prices = queryset.values_list('price', flat=True).exclude(price__isnull=True)
        
        if prices:
            return {
                'min_price': float(min(prices)),
                'max_price': float(max(prices)),
                'avg_price': float(sum(prices) / len(prices))
            }
        
        return {'min_price': 0, 'max_price': 0, 'avg_price': 0}