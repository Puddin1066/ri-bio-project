from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from streeteasy_integration.scraper import StreetEasyAgent
import json


class Command(BaseCommand):
    help = 'Scrape StreetEasy for property data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--property-type',
            choices=['rental', 'sale'],
            default='rental',
            help='Type of properties to scrape (rental or sale)',
        )
        parser.add_argument(
            '--neighborhood',
            type=str,
            help='Specific neighborhood to scrape',
        )
        parser.add_argument(
            '--min-price',
            type=int,
            help='Minimum price filter',
        )
        parser.add_argument(
            '--max-price',
            type=int,
            help='Maximum price filter',
        )
        parser.add_argument(
            '--min-bedrooms',
            type=int,
            help='Minimum number of bedrooms',
        )
        parser.add_argument(
            '--max-bedrooms',
            type=int,
            help='Maximum number of bedrooms',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of properties to scrape',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting StreetEasy scraper...'))
        
        # Build search parameters
        search_params = {}
        
        if options['neighborhood']:
            search_params['neighborhood'] = options['neighborhood']
        if options['min_price']:
            search_params['min_price'] = options['min_price']
        if options['max_price']:
            search_params['max_price'] = options['max_price']
        if options['min_bedrooms'] is not None:
            search_params['min_bedrooms'] = options['min_bedrooms']
        if options['max_bedrooms'] is not None:
            search_params['max_bedrooms'] = options['max_bedrooms']
        
        if options['verbose']:
            self.stdout.write(f"Search parameters: {json.dumps(search_params, indent=2)}")
        
        # Initialize agent and perform search
        agent = StreetEasyAgent()
        
        try:
            if options['property_type'] == 'sale':
                self.stdout.write('Searching for properties for sale...')
                properties = agent.search_sales(**search_params)
            else:
                self.stdout.write('Searching for rental properties...')
                properties = agent.search_rentals(**search_params)
            
            # Limit results if specified
            if options['limit'] and len(properties) > options['limit']:
                properties = properties[:options['limit']]
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully scraped {len(properties)} properties')
            )
            
            if options['verbose']:
                for i, prop in enumerate(properties[:5], 1):  # Show first 5
                    self.stdout.write(f"\n{i}. {prop.get('address', 'N/A')}")
                    self.stdout.write(f"   Price: {prop.get('formatted_price', 'N/A')}")
                    self.stdout.write(f"   Bedrooms: {prop.get('bedrooms', 'N/A')}")
                    self.stdout.write(f"   Neighborhood: {prop.get('neighborhood', 'N/A')}")
                
                if len(properties) > 5:
                    self.stdout.write(f"\n... and {len(properties) - 5} more properties")
            
        except Exception as e:
            raise CommandError(f'Scraping failed: {str(e)}')