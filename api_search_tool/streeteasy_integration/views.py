from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
import json
from .scraper import StreetEasyAgent
from .liquidity_scraper import LiquidityEventScraper, LiquidityAnalyzer
from .models import StreetEasyProperty, StreetEasySearch, StreetEasyLiquidityEvent, StreetEasyEntity


@csrf_exempt
@require_http_methods(["GET", "POST"])
def search_rentals(request):
    """
    API endpoint to search for rental properties
    
    GET /api/streeteasy/rentals/
    POST /api/streeteasy/rentals/ with JSON body
    
    Parameters:
    - neighborhood: string
    - min_price: integer
    - max_price: integer
    - min_bedrooms: integer
    - max_bedrooms: integer
    """
    try:
        if request.method == "POST":
            data = json.loads(request.body)
        else:
            data = request.GET.dict()
        
        # Convert string parameters to appropriate types
        search_params = {}
        
        if 'neighborhood' in data:
            search_params['neighborhood'] = data['neighborhood']
        
        if 'min_price' in data and data['min_price']:
            search_params['min_price'] = int(data['min_price'])
        
        if 'max_price' in data and data['max_price']:
            search_params['max_price'] = int(data['max_price'])
        
        if 'min_bedrooms' in data and data['min_bedrooms']:
            search_params['min_bedrooms'] = int(data['min_bedrooms'])
        
        if 'max_bedrooms' in data and data['max_bedrooms']:
            search_params['max_bedrooms'] = int(data['max_bedrooms'])
        
        # Initialize agent and search
        agent = StreetEasyAgent()
        properties = agent.search_rentals(**search_params)
        
        return JsonResponse({
            'success': True,
            'count': len(properties),
            'properties': properties,
            'search_params': search_params
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def search_sales(request):
    """
    API endpoint to search for properties for sale
    
    GET /api/streeteasy/sales/
    POST /api/streeteasy/sales/ with JSON body
    """
    try:
        if request.method == "POST":
            data = json.loads(request.body)
        else:
            data = request.GET.dict()
        
        # Convert string parameters to appropriate types
        search_params = {}
        
        if 'neighborhood' in data:
            search_params['neighborhood'] = data['neighborhood']
        
        if 'min_price' in data and data['min_price']:
            search_params['min_price'] = int(data['min_price'])
        
        if 'max_price' in data and data['max_price']:
            search_params['max_price'] = int(data['max_price'])
        
        if 'min_bedrooms' in data and data['min_bedrooms']:
            search_params['min_bedrooms'] = int(data['min_bedrooms'])
        
        if 'max_bedrooms' in data and data['max_bedrooms']:
            search_params['max_bedrooms'] = int(data['max_bedrooms'])
        
        # Initialize agent and search
        agent = StreetEasyAgent()
        properties = agent.search_sales(**search_params)
        
        return JsonResponse({
            'success': True,
            'count': len(properties),
            'properties': properties,
            'search_params': search_params
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_property(request, property_id):
    """
    Get a specific property by ID
    
    GET /api/streeteasy/property/{property_id}/
    """
    try:
        agent = StreetEasyAgent()
        property_data = agent.get_property_by_id(property_id)
        
        if property_data:
            return JsonResponse({
                'success': True,
                'property': property_data
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Property not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_neighborhoods(request):
    """
    Get list of available neighborhoods
    
    GET /api/streeteasy/neighborhoods/
    """
    try:
        agent = StreetEasyAgent()
        neighborhoods = agent.get_neighborhoods()
        
        return JsonResponse({
            'success': True,
            'neighborhoods': neighborhoods
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_price_range(request):
    """
    Get price range for properties
    
    GET /api/streeteasy/price-range/?property_type=rental&neighborhood=Manhattan
    """
    try:
        property_type = request.GET.get('property_type', 'rental')
        neighborhood = request.GET.get('neighborhood')
        
        agent = StreetEasyAgent()
        price_range = agent.get_price_range(property_type, neighborhood)
        
        return JsonResponse({
            'success': True,
            'price_range': price_range,
            'property_type': property_type,
            'neighborhood': neighborhood
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def agent_query(request):
    """
    Natural language query interface for agents
    
    POST /api/streeteasy/query/
    
    JSON body:
    {
        "query": "Find me 2 bedroom apartments in Manhattan under $5000",
        "context": "rental" // optional context
    }
    """
    try:
        data = json.loads(request.body)
        query = data.get('query', '').lower()
        context = data.get('context', '')
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Query parameter is required'
            }, status=400)
        
        # Parse natural language query
        search_params = parse_natural_language_query(query, context)
        
        if not search_params:
            return JsonResponse({
                'success': False,
                'error': 'Could not understand the query. Please try a more specific search.'
            }, status=400)
        
        # Determine if it's rental or sale based on context
        agent = StreetEasyAgent()
        
        if search_params.get('property_type') == 'sale':
            properties = agent.search_sales(**{k: v for k, v in search_params.items() if k != 'property_type'})
        else:
            properties = agent.search_rentals(**{k: v for k, v in search_params.items() if k != 'property_type'})
        
        return JsonResponse({
            'success': True,
            'query': query,
            'parsed_params': search_params,
            'count': len(properties),
            'properties': properties
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def parse_natural_language_query(query, context=""):
    """
    Parse natural language queries into search parameters
    
    Examples:
    - "2 bedroom apartments in Manhattan under $5000"
    - "Find condos for sale in Brooklyn between $500k and $1M"
    - "Studios in East Village"
    """
    import re
    
    params = {}
    query_lower = query.lower()
    
    # Determine property type
    if any(word in query_lower for word in ['rent', 'rental', 'apartment', 'apt']):
        params['property_type'] = 'rental'
    elif any(word in query_lower for word in ['sale', 'buy', 'purchase', 'condo', 'co-op', 'house']):
        params['property_type'] = 'sale'
    elif context:
        params['property_type'] = context
    else:
        params['property_type'] = 'rental'  # default
    
    # Extract number of bedrooms
    bedroom_patterns = [
        r'(\d+)\s*(?:bed(?:room)?s?|br)',
        r'(\d+)br',
        r'(\d+)\s*bed'
    ]
    
    for pattern in bedroom_patterns:
        match = re.search(pattern, query_lower)
        if match:
            params['min_bedrooms'] = int(match.group(1))
            params['max_bedrooms'] = int(match.group(1))
            break
    
    # Handle studio
    if 'studio' in query_lower:
        params['min_bedrooms'] = 0
        params['max_bedrooms'] = 0
    
    # Extract price ranges
    price_patterns = [
        r'under\s*\$?([\d,]+)(?:k|000)?',  # under $5000
        r'below\s*\$?([\d,]+)(?:k|000)?',  # below $5000
        r'max\s*\$?([\d,]+)(?:k|000)?',    # max $5000
        r'between\s*\$?([\d,]+)(?:k|000)?\s*(?:and|to|-)\s*\$?([\d,]+)(?:k|000)?',  # between $1000 and $2000
        r'\$?([\d,]+)(?:k|000)?\s*(?:to|-)\s*\$?([\d,]+)(?:k|000)?',  # $1000 to $2000
        r'over\s*\$?([\d,]+)(?:k|000)?',   # over $1000
        r'above\s*\$?([\d,]+)(?:k|000)?',  # above $1000
        r'min\s*\$?([\d,]+)(?:k|000)?',    # min $1000
    ]
    
    # Handle "under/below/max" price
    for pattern in [r'under\s*\$?([\d,]+)(?:k|000)?', r'below\s*\$?([\d,]+)(?:k|000)?', r'max\s*\$?([\d,]+)(?:k|000)?']:
        match = re.search(pattern, query_lower)
        if match:
            price_str = match.group(1).replace(',', '')
            price = int(price_str)
            if 'k' in match.group(0) and price < 1000:
                price *= 1000
            params['max_price'] = price
            break
    
    # Handle "between" price ranges
    between_match = re.search(r'between\s*\$?([\d,]+)(?:k|000)?\s*(?:and|to|-)\s*\$?([\d,]+)(?:k|000)?', query_lower)
    if between_match:
        min_price_str = between_match.group(1).replace(',', '')
        max_price_str = between_match.group(2).replace(',', '')
        min_price = int(min_price_str)
        max_price = int(max_price_str)
        
        # Handle 'k' notation
        if 'k' in between_match.group(0):
            if min_price < 1000:
                min_price *= 1000
            if max_price < 1000:
                max_price *= 1000
        
        params['min_price'] = min_price
        params['max_price'] = max_price
    
    # Handle "over/above/min" price
    for pattern in [r'over\s*\$?([\d,]+)(?:k|000)?', r'above\s*\$?([\d,]+)(?:k|000)?', r'min\s*\$?([\d,]+)(?:k|000)?']:
        match = re.search(pattern, query_lower)
        if match:
            price_str = match.group(1).replace(',', '')
            price = int(price_str)
            if 'k' in match.group(0) and price < 1000:
                price *= 1000
            params['min_price'] = price
            break
    
    # Extract neighborhoods (NYC-specific)
    neighborhoods = [
        'manhattan', 'brooklyn', 'queens', 'bronx', 'staten island',
        'upper east side', 'upper west side', 'east village', 'west village',
        'soho', 'tribeca', 'chelsea', 'midtown', 'downtown', 'financial district',
        'williamsburg', 'park slope', 'bushwick', 'dumbo', 'carroll gardens',
        'red hook', 'bay ridge', 'sunset park', 'greenpoint', 'cobble hill',
        'astoria', 'long island city', 'flushing', 'jackson heights',
        'fordham', 'riverdale', 'mott haven', 'hunts point',
        'st. george', 'stapleton', 'new brighton'
    ]
    
    for neighborhood in neighborhoods:
        if neighborhood in query_lower:
            params['neighborhood'] = neighborhood.title()
            break
    
    return params if params else None


@require_http_methods(["GET"])
def api_status(request):
    """
    Get API status and statistics
    
    GET /api/streeteasy/status/
    """
    try:
        # Get database statistics
        total_properties = StreetEasyProperty.objects.count()
        total_rentals = StreetEasyProperty.objects.filter(property_type='rental').count()
        total_sales = StreetEasyProperty.objects.filter(property_type='sale').count()
        total_searches = StreetEasySearch.objects.count()
        
        # Get recent activity
        from django.utils import timezone
        from datetime import timedelta
        
        recent_cutoff = timezone.now() - timedelta(days=7)
        recent_properties = StreetEasyProperty.objects.filter(
            created_at__gte=recent_cutoff
        ).count()
        
        return JsonResponse({
            'success': True,
            'status': 'active',
            'statistics': {
                'total_properties': total_properties,
                'total_rentals': total_rentals,
                'total_sales': total_sales,
                'total_searches': total_searches,
                'recent_properties_7_days': recent_properties,
            },
            'endpoints': {
                'search_rentals': '/api/streeteasy/rentals/',
                'search_sales': '/api/streeteasy/sales/',
                'get_property': '/api/streeteasy/property/{id}/',
                'neighborhoods': '/api/streeteasy/neighborhoods/',
                'price_range': '/api/streeteasy/price-range/',
                'agent_query': '/api/streeteasy/query/',
                'status': '/api/streeteasy/status/',
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def dashboard(request):
    """
    Web dashboard for StreetEasy integration
    """
    try:
        # Get basic statistics
        total_properties = StreetEasyProperty.objects.count()
        total_rentals = StreetEasyProperty.objects.filter(property_type='rental').count()
        total_sales = StreetEasyProperty.objects.filter(property_type='sale').count()
        
        # Get recent properties
        recent_properties = StreetEasyProperty.objects.order_by('-created_at')[:10]
        
        context = {
            'total_properties': total_properties,
            'total_rentals': total_rentals,
            'total_sales': total_sales,
            'recent_properties': recent_properties,
        }
        
        return render(request, 'streeteasy_integration/dashboard.html', context)
        
    except Exception as e:
        return render(request, 'streeteasy_integration/error.html', {'error': str(e)})


@require_http_methods(["GET"])
def get_largest_liquidity_events(request):
    """
    Get the largest liquidity events within a timeframe
    
    GET /api/streeteasy/liquidity/largest/?timeframe_days=365&limit=10
    """
    try:
        timeframe_days = int(request.GET.get('timeframe_days', 365))
        limit = int(request.GET.get('limit', 10))
        
        analyzer = LiquidityAnalyzer()
        events = analyzer.get_largest_liquidity_events(timeframe_days, limit)
        
        return JsonResponse({
            'success': True,
            'timeframe_days': timeframe_days,
            'count': len(events),
            'events': events
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_most_active_entities(request):
    """
    Get entities with the most transaction volume
    
    GET /api/streeteasy/liquidity/entities/?timeframe_days=365&limit=10
    """
    try:
        timeframe_days = int(request.GET.get('timeframe_days', 365))
        limit = int(request.GET.get('limit', 10))
        
        analyzer = LiquidityAnalyzer()
        entities = analyzer.get_most_active_entities(timeframe_days, limit)
        
        return JsonResponse({
            'success': True,
            'timeframe_days': timeframe_days,
            'count': len(entities),
            'entities': entities
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def liquidity_question(request):
    """
    Answer natural language questions about liquidity events
    
    POST /api/streeteasy/liquidity/question/
    
    JSON body:
    {
        "question": "Who has had the largest liquidity event in the past year?"
    }
    """
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        
        if not question:
            return JsonResponse({
                'success': False,
                'error': 'Question parameter is required'
            }, status=400)
        
        analyzer = LiquidityAnalyzer()
        answer = analyzer.answer_liquidity_question(question)
        
        return JsonResponse({
            'success': True,
            'question': question,
            'answer': answer
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def scrape_liquidity_events(request):
    """
    Manually trigger scraping of liquidity events
    
    POST /api/streeteasy/liquidity/scrape/
    
    JSON body:
    {
        "min_amount": 1000000,
        "days_back": 365,
        "include_news": true
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        
        min_amount = data.get('min_amount', 1000000)
        days_back = data.get('days_back', 365)
        include_news = data.get('include_news', True)
        
        scraper = LiquidityEventScraper()
        all_events = []
        
        # Scrape StreetEasy sold data
        streeteasy_events = scraper.scrape_streeteasy_sold_data(min_amount, days_back)
        all_events.extend(streeteasy_events)
        
        # Scrape news articles if requested
        if include_news:
            news_events = scraper.scrape_news_articles(min(days_back, 30))  # Limit news scraping
            all_events.extend(news_events)
        
        # Save events to database
        created, updated = scraper.save_liquidity_events(all_events)
        
        return JsonResponse({
            'success': True,
            'total_events_found': len(all_events),
            'events_created': created,
            'events_updated': updated,
            'parameters': {
                'min_amount': min_amount,
                'days_back': days_back,
                'include_news': include_news
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def liquidity_stats(request):
    """
    Get overall liquidity statistics
    
    GET /api/streeteasy/liquidity/stats/
    """
    try:
        from django.db.models import Sum, Count, Max, Avg
        from django.utils import timezone
        from datetime import timedelta
        
        # Overall stats
        total_events = StreetEasyLiquidityEvent.objects.count()
        total_volume = StreetEasyLiquidityEvent.objects.aggregate(Sum('transaction_amount'))['transaction_amount__sum'] or 0
        avg_transaction = StreetEasyLiquidityEvent.objects.aggregate(Avg('transaction_amount'))['transaction_amount__avg'] or 0
        largest_transaction = StreetEasyLiquidityEvent.objects.aggregate(Max('transaction_amount'))['transaction_amount__max'] or 0
        
        # Recent activity (past 30 days)
        recent_cutoff = timezone.now().date() - timedelta(days=30)
        recent_events = StreetEasyLiquidityEvent.objects.filter(transaction_date__gte=recent_cutoff).count()
        recent_volume = StreetEasyLiquidityEvent.objects.filter(
            transaction_date__gte=recent_cutoff
        ).aggregate(Sum('transaction_amount'))['transaction_amount__sum'] or 0
        
        # Entity stats
        total_entities = StreetEasyEntity.objects.count()
        most_active_entity = StreetEasyEntity.objects.order_by('-total_transaction_volume').first()
        
        return JsonResponse({
            'success': True,
            'overall_stats': {
                'total_events': total_events,
                'total_volume': float(total_volume),
                'avg_transaction': float(avg_transaction),
                'largest_transaction': float(largest_transaction),
                'total_entities': total_entities,
            },
            'recent_activity_30_days': {
                'events': recent_events,
                'volume': float(recent_volume),
            },
            'most_active_entity': most_active_entity.to_dict() if most_active_entity else None,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)