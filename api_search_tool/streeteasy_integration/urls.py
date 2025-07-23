from django.urls import path
from . import views
from . import sec_views

app_name = 'streeteasy_integration'

urlpatterns = [
    # API endpoints
    path('api/streeteasy/rentals/', views.search_rentals, name='search_rentals'),
    path('api/streeteasy/sales/', views.search_sales, name='search_sales'),
    path('api/streeteasy/property/<str:property_id>/', views.get_property, name='get_property'),
    path('api/streeteasy/neighborhoods/', views.get_neighborhoods, name='get_neighborhoods'),
    path('api/streeteasy/price-range/', views.get_price_range, name='get_price_range'),
    path('api/streeteasy/query/', views.agent_query, name='agent_query'),
    path('api/streeteasy/status/', views.api_status, name='api_status'),
    
    # Liquidity events API endpoints
    path('api/streeteasy/liquidity/largest/', views.get_largest_liquidity_events, name='largest_liquidity_events'),
    path('api/streeteasy/liquidity/entities/', views.get_most_active_entities, name='most_active_entities'),
    path('api/streeteasy/liquidity/question/', views.liquidity_question, name='liquidity_question'),
    path('api/streeteasy/liquidity/scrape/', views.scrape_liquidity_events, name='scrape_liquidity_events'),
    path('api/streeteasy/liquidity/stats/', views.liquidity_stats, name='liquidity_stats'),
    
    # SEC EDGAR API endpoints
    path('api/streeteasy/sec/companies/', sec_views.search_sec_companies, name='search_sec_companies'),
    path('api/streeteasy/sec/company/<str:ticker_or_cik>/', sec_views.get_company_profile, name='get_company_profile'),
    path('api/streeteasy/sec/real-estate-companies/', sec_views.get_real_estate_companies, name='get_real_estate_companies'),
    path('api/streeteasy/sec/liquidity-events/', sec_views.get_sec_liquidity_events, name='get_sec_liquidity_events'),
    path('api/streeteasy/sec/question/', sec_views.sec_question, name='sec_question'),
    
    # Comprehensive analysis combining all data sources
    path('api/streeteasy/comprehensive-analysis/', sec_views.comprehensive_liquidity_analysis, name='comprehensive_analysis'),
    
    # Web dashboard
    path('streeteasy/', views.dashboard, name='dashboard'),
]