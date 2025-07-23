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
    
    # Web dashboard
    path('streeteasy/', views.dashboard, name='dashboard'),
]