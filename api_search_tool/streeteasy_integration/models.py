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