from django.core.management.base import BaseCommand, CommandError
from streeteasy_integration.liquidity_scraper import LiquidityAnalyzer


class Command(BaseCommand):
    help = 'Answer liquidity questions using the analyzer'

    def add_arguments(self, parser):
        parser.add_argument(
            'question',
            type=str,
            help='Question to ask about liquidity events',
        )

    def handle(self, *args, **options):
        question = options['question']
        
        self.stdout.write(f"Question: {question}")
        self.stdout.write("-" * 50)
        
        try:
            analyzer = LiquidityAnalyzer()
            answer = analyzer.answer_liquidity_question(question)
            
            self.stdout.write(answer)
            
        except Exception as e:
            raise CommandError(f'Analysis failed: {str(e)}')