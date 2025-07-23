from django.urls import path
from . import views

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
    
    # Web dashboard
    path('streeteasy/', views.dashboard, name='dashboard'),
]