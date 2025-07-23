from django.db import models
from django.utils import timezone
import json


class StreetEasyProperty(models.Model):
    """Model to store StreetEasy property information"""
    
    PROPERTY_TYPES = [
        ('rental', 'Rental'),
        ('sale', 'Sale'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('sold', 'Sold/Rented'),
        ('expired', 'Expired'),
    ]
    
    # Basic property information
    street_easy_id = models.CharField(max_length=50, unique=True, db_index=True)
    property_type = models.CharField(max_length=10, choices=PROPERTY_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    # Address and location
    address = models.CharField(max_length=500)
    neighborhood = models.CharField(max_length=100, blank=True)
    borough = models.CharField(max_length=50, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    
    # Property details
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    bedrooms = models.IntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    square_feet = models.IntegerField(null=True, blank=True)
    unit_type = models.CharField(max_length=50, blank=True)  # e.g., "Studio", "1BR", "2BR"
    
    # Building details
    building_name = models.CharField(max_length=200, blank=True)
    building_type = models.CharField(max_length=50, blank=True)  # e.g., "Condo", "Co-op", "Rental Building"
    year_built = models.IntegerField(null=True, blank=True)
    
    # Amenities and features
    amenities = models.JSONField(default=list, blank=True)
    pet_policy = models.CharField(max_length=100, blank=True)
    parking = models.BooleanField(default=False)
    doorman = models.BooleanField(default=False)
    elevator = models.BooleanField(default=False)
    
    # Agent and listing information
    agent_name = models.CharField(max_length=100, blank=True)
    agent_company = models.CharField(max_length=200, blank=True)
    listing_url = models.URLField(blank=True)
    
    # Images and media
    image_urls = models.JSONField(default=list, blank=True)
    
    # Raw data from StreetEasy
    raw_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "StreetEasy Property"
        verbose_name_plural = "StreetEasy Properties"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.address} - ${self.price} ({self.property_type})"
    
    @property
    def formatted_price(self):
        """Return formatted price string"""
        if self.price:
            if self.property_type == 'rental':
                return f"${self.price:,.0f}/month"
            else:
                return f"${self.price:,.0f}"
        return "Price not available"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'id': self.street_easy_id,
            'property_type': self.property_type,
            'status': self.status,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'borough': self.borough,
            'zipcode': self.zipcode,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'price': float(self.price) if self.price else None,
            'formatted_price': self.formatted_price,
            'bedrooms': self.bedrooms,
            'bathrooms': float(self.bathrooms) if self.bathrooms else None,
            'square_feet': self.square_feet,
            'unit_type': self.unit_type,
            'building_name': self.building_name,
            'building_type': self.building_type,
            'year_built': self.year_built,
            'amenities': self.amenities,
            'pet_policy': self.pet_policy,
            'parking': self.parking,
            'doorman': self.doorman,
            'elevator': self.elevator,
            'agent_name': self.agent_name,
            'agent_company': self.agent_company,
            'listing_url': self.listing_url,
            'image_urls': self.image_urls,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_scraped': self.last_scraped.isoformat(),
        }


class StreetEasySearch(models.Model):
    """Model to store search parameters and results for agent queries"""
    
    search_id = models.CharField(max_length=100, unique=True, db_index=True)
    search_parameters = models.JSONField()  # Store search criteria
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_executed = models.DateTimeField(default=timezone.now)
    
    # Search parameters fields for easy filtering
    min_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    max_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    min_bedrooms = models.IntegerField(null=True, blank=True)
    max_bedrooms = models.IntegerField(null=True, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)
    property_type = models.CharField(max_length=10, blank=True)
    
    class Meta:
        verbose_name = "StreetEasy Search"
        verbose_name_plural = "StreetEasy Searches"
        ordering = ['-last_executed']
    
    def __str__(self):
        return f"Search {self.search_id} - {self.results_count} results"


class StreetEasyAPIKey(models.Model):
    """Model to store API configuration and rate limiting info"""
    
    name = models.CharField(max_length=100, unique=True)
    api_key = models.CharField(max_length=500, blank=True)  # If we get access to official API
    rate_limit_per_hour = models.IntegerField(default=100)
    requests_made_today = models.IntegerField(default=0)
    last_request_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "StreetEasy API Key"
        verbose_name_plural = "StreetEasy API Keys"
    
    def __str__(self):
        return f"API Key: {self.name}"


class StreetEasyLiquidityEvent(models.Model):
    """Model to track major liquidity events and transactions"""
    
    EVENT_TYPES = [
        ('sale', 'Property Sale'),
        ('portfolio_sale', 'Portfolio Sale'),
        ('building_sale', 'Building Sale'),
        ('development_sale', 'Development Sale'),
        ('refinancing', 'Refinancing'),
        ('ipo', 'Real Estate IPO'),
        ('merger', 'Merger/Acquisition'),
        ('fund_raise', 'Fund Raising'),
    ]
    
    ENTITY_TYPES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('fund', 'Investment Fund'),
        ('reit', 'REIT'),
        ('developer', 'Developer'),
        ('broker', 'Brokerage'),
        ('family_office', 'Family Office'),
    ]
    
    # Event identification
    event_id = models.CharField(max_length=100, unique=True, db_index=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    transaction_date = models.DateField()
    
    # Financial details
    transaction_amount = models.DecimalField(max_digits=20, decimal_places=2)  # Large amounts
    currency = models.CharField(max_length=3, default='USD')
    
    # Parties involved
    seller_name = models.CharField(max_length=200)
    seller_type = models.CharField(max_length=20, choices=ENTITY_TYPES, blank=True)
    buyer_name = models.CharField(max_length=200, blank=True)
    buyer_type = models.CharField(max_length=20, choices=ENTITY_TYPES, blank=True)
    
    # Property/Asset details
    property_address = models.CharField(max_length=500, blank=True)
    neighborhood = models.CharField(max_length=100, blank=True)
    borough = models.CharField(max_length=50, blank=True)
    property_type = models.CharField(max_length=100, blank=True)  # e.g., "Office Building", "Residential Portfolio"
    square_footage = models.IntegerField(null=True, blank=True)
    unit_count = models.IntegerField(null=True, blank=True)
    
    # Transaction details
    price_per_sqft = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cap_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    broker_firm = models.CharField(max_length=200, blank=True)
    broker_name = models.CharField(max_length=200, blank=True)
    
    # Source and metadata
    source_url = models.URLField(blank=True)
    source_publication = models.CharField(max_length=100, blank=True)
    confidence_score = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)  # 0-1 confidence
    
    # Additional data
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Liquidity Event"
        verbose_name_plural = "Liquidity Events"
        ordering = ['-transaction_amount', '-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date', 'transaction_amount']),
            models.Index(fields=['seller_name']),
            models.Index(fields=['buyer_name']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.seller_name} - ${self.transaction_amount:,.0f} ({self.transaction_date})"
    
    @property
    def formatted_amount(self):
        """Return formatted transaction amount"""
        amount = float(self.transaction_amount)
        if amount >= 1_000_000_000:
            return f"${amount/1_000_000_000:.1f}B"
        elif amount >= 1_000_000:
            return f"${amount/1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"${amount/1_000:.1f}K"
        else:
            return f"${amount:,.0f}"
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'transaction_date': self.transaction_date.isoformat(),
            'transaction_amount': float(self.transaction_amount),
            'formatted_amount': self.formatted_amount,
            'currency': self.currency,
            'seller_name': self.seller_name,
            'seller_type': self.seller_type,
            'buyer_name': self.buyer_name,
            'buyer_type': self.buyer_type,
            'property_address': self.property_address,
            'neighborhood': self.neighborhood,
            'borough': self.borough,
            'property_type': self.property_type,
            'square_footage': self.square_footage,
            'unit_count': self.unit_count,
            'price_per_sqft': float(self.price_per_sqft) if self.price_per_sqft else None,
            'cap_rate': float(self.cap_rate) if self.cap_rate else None,
            'broker_firm': self.broker_firm,
            'broker_name': self.broker_name,
            'source_url': self.source_url,
            'source_publication': self.source_publication,
            'confidence_score': float(self.confidence_score),
            'notes': self.notes,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class StreetEasyEntity(models.Model):
    """Model to track real estate entities and their transaction history"""
    
    ENTITY_TYPES = [
        ('individual', 'Individual'),
        ('company', 'Company'),
        ('fund', 'Investment Fund'),
        ('reit', 'REIT'),
        ('developer', 'Developer'),
        ('broker', 'Brokerage'),
        ('family_office', 'Family Office'),
        ('government', 'Government Entity'),
    ]
    
    # Entity identification
    entity_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    
    # Entity details
    description = models.TextField(blank=True)
    headquarters_location = models.CharField(max_length=200, blank=True)
    founded_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    
    # Financial metrics (aggregated)
    total_transaction_volume = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)
    largest_transaction = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    avg_transaction_size = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Time-based metrics
    last_transaction_date = models.DateField(null=True, blank=True)
    most_active_year = models.IntegerField(null=True, blank=True)
    
    # Market focus
    primary_markets = models.JSONField(default=list, blank=True)  # neighborhoods/boroughs
    property_types_focus = models.JSONField(default=list, blank=True)
    
    # Additional data
    aliases = models.JSONField(default=list, blank=True)  # Alternative names
    related_entities = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Real Estate Entity"
        verbose_name_plural = "Real Estate Entities"
        ordering = ['-total_transaction_volume', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['entity_type']),
            models.Index(fields=['total_transaction_volume']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"
    
    def update_metrics(self):
        """Update aggregated transaction metrics"""
        from django.db.models import Sum, Count, Max, Avg
        
        # Get transactions where this entity was involved
        seller_transactions = StreetEasyLiquidityEvent.objects.filter(seller_name__icontains=self.name)
        buyer_transactions = StreetEasyLiquidityEvent.objects.filter(buyer_name__icontains=self.name)
        
        all_transactions = seller_transactions.union(buyer_transactions)
        
        if all_transactions.exists():
            metrics = all_transactions.aggregate(
                total_volume=Sum('transaction_amount'),
                count=Count('id'),
                largest=Max('transaction_amount'),
                average=Avg('transaction_amount'),
                last_date=Max('transaction_date')
            )
            
            self.total_transaction_volume = metrics['total_volume'] or 0
            self.transaction_count = metrics['count'] or 0
            self.largest_transaction = metrics['largest']
            self.avg_transaction_size = metrics['average']
            self.last_transaction_date = metrics['last_date']
            
            self.save()
    
    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'entity_id': self.entity_id,
            'name': self.name,
            'entity_type': self.entity_type,
            'description': self.description,
            'headquarters_location': self.headquarters_location,
            'founded_year': self.founded_year,
            'website': self.website,
            'total_transaction_volume': float(self.total_transaction_volume),
            'transaction_count': self.transaction_count,
            'largest_transaction': float(self.largest_transaction) if self.largest_transaction else None,
            'avg_transaction_size': float(self.avg_transaction_size) if self.avg_transaction_size else None,
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'most_active_year': self.most_active_year,
            'primary_markets': self.primary_markets,
            'property_types_focus': self.property_types_focus,
            'aliases': self.aliases,
            'related_entities': self.related_entities,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }