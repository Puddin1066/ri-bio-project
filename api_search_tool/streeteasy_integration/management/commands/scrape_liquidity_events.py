from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from streeteasy_integration.liquidity_scraper import LiquidityEventScraper, LiquidityAnalyzer
import json


class Command(BaseCommand):
    help = 'Scrape major liquidity events and real estate transactions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-amount',
            type=int,
            default=1000000,
            help='Minimum transaction amount to scrape (default: $1M)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=365,
            help='Number of days to look back for transactions',
        )
        parser.add_argument(
            '--include-news',
            action='store_true',
            help='Include news article scraping for transactions',
        )
        parser.add_argument(
            '--update-entities',
            action='store_true',
            help='Update entity metrics after scraping',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting liquidity events scraper...')
        )
        
        min_amount = options['min_amount']
        days_back = options['days_back']
        include_news = options['include_news']
        verbose = options['verbose']
        
        if verbose:
            self.stdout.write(f"Parameters:")
            self.stdout.write(f"  Min amount: ${min_amount:,}")
            self.stdout.write(f"  Days back: {days_back}")
            self.stdout.write(f"  Include news: {include_news}")
        
        scraper = LiquidityEventScraper()
        all_events = []
        
        try:
            # Scrape StreetEasy sold data
            self.stdout.write('Scraping StreetEasy sold properties...')
            streeteasy_events = scraper.scrape_streeteasy_sold_data(
                min_amount=min_amount, 
                days_back=days_back
            )
            all_events.extend(streeteasy_events)
            
            if verbose:
                self.stdout.write(f"Found {len(streeteasy_events)} StreetEasy transactions")
            
            # Scrape news articles if requested
            if include_news:
                self.stdout.write('Scraping news articles for transactions...')
                news_events = scraper.scrape_news_articles(
                    days_back=min(days_back, 30)  # Limit news scraping
                )
                all_events.extend(news_events)
                
                if verbose:
                    self.stdout.write(f"Found {len(news_events)} news article transactions")
            
            # Save events to database
            self.stdout.write('Saving events to database...')
            created, updated = scraper.save_liquidity_events(all_events)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {len(all_events)} events:\n'
                    f'  - {created} new events created\n'
                    f'  - {updated} existing events updated'
                )
            )
            
            # Update entity metrics if requested
            if options['update_entities']:
                self.stdout.write('Updating entity metrics...')
                from streeteasy_integration.models import StreetEasyEntity
                
                updated_entities = 0
                for entity in StreetEasyEntity.objects.all():
                    entity.update_metrics()
                    updated_entities += 1
                
                self.stdout.write(f"Updated metrics for {updated_entities} entities")
            
            # Show summary of largest events if verbose
            if verbose and all_events:
                self.stdout.write('\nTop 5 largest events found:')
                sorted_events = sorted(
                    all_events, 
                    key=lambda x: x.get('transaction_amount', 0), 
                    reverse=True
                )
                
                for i, event in enumerate(sorted_events[:5], 1):
                    amount = event.get('transaction_amount', 0)
                    seller = event.get('seller_name', 'Unknown')
                    address = event.get('property_address', '')
                    
                    if amount >= 1_000_000_000:
                        amount_str = f"${amount/1_000_000_000:.1f}B"
                    elif amount >= 1_000_000:
                        amount_str = f"${amount/1_000_000:.1f}M"
                    else:
                        amount_str = f"${amount:,.0f}"
                    
                    self.stdout.write(f"  {i}. {seller} - {amount_str}")
                    if address:
                        self.stdout.write(f"     {address}")
            
        except Exception as e:
            raise CommandError(f'Scraping failed: {str(e)}')