from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .sec_edgar_integration import SECEdgarAPI, SECRealEstateAnalyzer
from .liquidity_scraper import LiquidityAnalyzer


@require_http_methods(["GET"])
def search_sec_companies(request):
    """
    Search for companies in SEC database
    
    GET /api/streeteasy/sec/companies/?query=SPG&limit=10
    """
    try:
        query = request.GET.get('query', '')
        limit = int(request.GET.get('limit', 10))
        
        if not query:
            return JsonResponse({
                'success': False,
                'error': 'Query parameter is required'
            }, status=400)
        
        sec_api = SECEdgarAPI()
        companies = sec_api.search_companies(query, limit)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'count': len(companies),
            'companies': companies
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_company_profile(request, ticker_or_cik):
    """
    Get comprehensive financial profile for a company
    
    GET /api/streeteasy/sec/company/{ticker_or_cik}/
    """
    try:
        analyzer = SECRealEstateAnalyzer()
        profile = analyzer.get_company_financial_profile(ticker_or_cik)
        
        if profile:
            return JsonResponse({
                'success': True,
                'profile': profile
            })
        else:
            return JsonResponse({
                'success': False,
                'error': f'Company not found: {ticker_or_cik}'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_real_estate_companies(request):
    """
    Get list of major real estate companies from SEC data
    
    GET /api/streeteasy/sec/real-estate-companies/
    """
    try:
        sec_api = SECEdgarAPI()
        companies = sec_api.get_real_estate_companies()
        
        return JsonResponse({
            'success': True,
            'count': len(companies),
            'companies': companies
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_sec_liquidity_events(request):
    """
    Get SEC liquidity events for real estate companies
    
    GET /api/streeteasy/sec/liquidity-events/?days_back=365
    """
    try:
        days_back = int(request.GET.get('days_back', 365))
        
        analyzer = SECRealEstateAnalyzer()
        events = analyzer.find_real_estate_liquidity_events(days_back)
        
        return JsonResponse({
            'success': True,
            'days_back': days_back,
            'count': len(events),
            'events': events
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def sec_question(request):
    """
    Answer natural language questions about SEC data
    
    POST /api/streeteasy/sec/question/
    
    JSON body:
    {
        "question": "What SEC filings has Simon Property Group made recently?"
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
        
        analyzer = SECRealEstateAnalyzer()
        answer = analyzer.answer_sec_question(question)
        
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
def comprehensive_liquidity_analysis(request):
    """
    Answer 'who has had the largest liquidity event' by combining all data sources
    
    POST /api/streeteasy/comprehensive-analysis/
    
    JSON body:
    {
        "question": "Who has had the largest liquidity event in the past year?",
        "timeframe_days": 365
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        question = data.get('question', 'Who has had the largest liquidity event in the past year?')
        timeframe_days = data.get('timeframe_days', 365)
        
        analysis_results = {
            'question': question,
            'timeframe_days': timeframe_days,
            'data_sources': ['StreetEasy', 'SEC EDGAR'],
        }
        
        combined_events = []
        
        # Get StreetEasy liquidity events
        liquidity_analyzer = LiquidityAnalyzer()
        re_events = liquidity_analyzer.get_largest_liquidity_events(timeframe_days, 10)
        
        for event in re_events:
            event['source'] = 'StreetEasy'
            event['event_type'] = 'real_estate_transaction'
        
        combined_events.extend(re_events)
        
        # Get SEC liquidity events
        sec_analyzer = SECRealEstateAnalyzer()
        sec_events = sec_analyzer.find_real_estate_liquidity_events(timeframe_days)
        
        for event in sec_events:
            # Convert SEC events to standardized format
            standardized_event = {
                'seller_name': event.get('company_name', ''),
                'buyer_name': '',
                'transaction_amount': event.get('max_amount', 0),
                'formatted_amount': '',
                'transaction_date': event.get('filing_date', ''),
                'event_type': 'sec_filing',
                'source': 'SEC',
                'keywords': event.get('keywords', []),
                'document_url': event.get('document_url', ''),
            }
            
            # Format amount
            amount = standardized_event['transaction_amount']
            if amount and amount >= 1000000:
                if amount >= 1000000000:
                    standardized_event['formatted_amount'] = f"${amount/1000000000:.1f}B"
                else:
                    standardized_event['formatted_amount'] = f"${amount/1000000:.1f}M"
            else:
                standardized_event['formatted_amount'] = 'Amount not disclosed'
            
            combined_events.append(standardized_event)
        
        # Sort all events by transaction amount
        combined_events.sort(key=lambda x: x.get('transaction_amount', 0), reverse=True)
        
        # Generate comprehensive answer
        if combined_events:
            answer = f"Based on analysis of StreetEasy and SEC EDGAR data over the past {timeframe_days} days, here are the largest liquidity events:\n\n"
            
            for i, event in enumerate(combined_events[:10], 1):
                seller = event.get('seller_name', 'Unknown')
                amount = event.get('formatted_amount', 'Amount not disclosed')
                date = event.get('transaction_date', 'Date unknown')
                source = event.get('source', 'Unknown')
                
                answer += f"{i}. {seller}"
                if amount and amount != 'Amount not disclosed':
                    answer += f" - {amount}"
                answer += f" ({date}) [Source: {source}]\n"
                
                # Add additional context for SEC events
                if event.get('source') == 'SEC' and event.get('keywords'):
                    answer += f"   Related to: {', '.join(event['keywords'][:3])}\n"
                
                # Add property details for StreetEasy events
                if event.get('source') == 'StreetEasy':
                    if event.get('property_address'):
                        answer += f"   Property: {event['property_address']}\n"
                    if event.get('neighborhood'):
                        answer += f"   Location: {event['neighborhood']}\n"
                
                answer += "\n"
            
            analysis_results['combined_answer'] = answer
            analysis_results['total_events_analyzed'] = len(combined_events)
            analysis_results['top_events'] = combined_events[:10]
            
            # Summary statistics
            total_disclosed_amount = sum([
                event.get('transaction_amount', 0) 
                for event in combined_events 
                if event.get('transaction_amount', 0) > 0
            ])
            
            if total_disclosed_amount > 0:
                if total_disclosed_amount >= 1000000000:
                    total_str = f"${total_disclosed_amount/1000000000:.1f}B"
                else:
                    total_str = f"${total_disclosed_amount/1000000:.1f}M"
                
                analysis_results['summary'] = {
                    'total_disclosed_volume': total_str,
                    'events_with_amounts': len([e for e in combined_events if e.get('transaction_amount', 0) > 0]),
                    'streeteasy_events': len([e for e in combined_events if e.get('source') == 'StreetEasy']),
                    'sec_events': len([e for e in combined_events if e.get('source') == 'SEC']),
                }
        else:
            analysis_results['combined_answer'] = f"No significant liquidity events found in the past {timeframe_days} days across StreetEasy and SEC data sources."
            analysis_results['total_events_analyzed'] = 0
            analysis_results['top_events'] = []
        
        return JsonResponse({
            'success': True,
            'analysis': analysis_results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)