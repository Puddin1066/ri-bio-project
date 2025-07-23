# StreetEasy & SEC EDGAR Integration

This platform provides comprehensive API integration with both StreetEasy real estate data and SEC EDGAR corporate filings to answer questions about liquidity events, particularly **"Who has had the largest liquidity event in the past year?"**

## Overview

The platform combines three main data sources:

1. **StreetEasy Real Estate Data** - Property transactions, sales, and rental data
2. **SEC EDGAR Filings** - Corporate filings, 8-K events, and financial data for public companies
3. **Liquidity Event Analysis** - Cross-platform analysis to identify major financial events

## Key Features

### 1. StreetEasy Integration
- Property search (rentals and sales)
- Market data analysis
- Neighborhood insights
- Price range analysis
- Natural language property queries

### 2. SEC EDGAR Integration
- Company search and profiles
- Financial metrics extraction
- 8-K filing analysis for material events
- Real estate company focus (REITs, property companies)
- Corporate liquidity event identification

### 3. Liquidity Event Tracking
- Major property transactions (>$1M)
- Corporate material events from SEC filings
- Entity relationship tracking
- Transaction volume analysis
- Cross-platform event correlation

### 4. Comprehensive Analysis
- Combines StreetEasy and SEC data
- Identifies largest liquidity events across all sources
- Provides detailed transaction context
- Supports natural language queries

## API Endpoints

### StreetEasy Endpoints

#### Property Search
```
GET /api/streeteasy/rentals/?neighborhood=Manhattan&min_price=3000&max_price=5000
GET /api/streeteasy/sales/?min_bedrooms=2&max_bedrooms=3
POST /api/streeteasy/query/
{
  "query": "Find me 2 bedroom apartments in Manhattan under $5000"
}
```

#### Property Details
```
GET /api/streeteasy/property/{property_id}/
GET /api/streeteasy/neighborhoods/
GET /api/streeteasy/price-range/?property_type=rental&neighborhood=Manhattan
```

### Liquidity Events Endpoints

#### Largest Events
```
GET /api/streeteasy/liquidity/largest/?timeframe_days=365&limit=10
GET /api/streeteasy/liquidity/entities/?timeframe_days=365&limit=10
GET /api/streeteasy/liquidity/stats/
```

#### Natural Language Queries
```
POST /api/streeteasy/liquidity/question/
{
  "question": "Who has had the largest liquidity event in the past year?"
}
```

#### Data Management
```
POST /api/streeteasy/liquidity/scrape/
{
  "min_amount": 1000000,
  "days_back": 365,
  "include_news": true
}
```

### SEC EDGAR Endpoints

#### Company Search
```
GET /api/streeteasy/sec/companies/?query=SPG&limit=10
GET /api/streeteasy/sec/company/{ticker_or_cik}/
GET /api/streeteasy/sec/real-estate-companies/
```

#### SEC Analysis
```
GET /api/streeteasy/sec/liquidity-events/?days_back=365
POST /api/streeteasy/sec/question/
{
  "question": "What SEC filings has Simon Property Group made recently?"
}
```

### Comprehensive Analysis

#### Combined Analysis (Main Feature)
```
POST /api/streeteasy/comprehensive-analysis/
{
  "question": "Who has had the largest liquidity event in the past year?",
  "timeframe_days": 365
}
```

This endpoint combines data from both StreetEasy and SEC EDGAR to provide a comprehensive answer to liquidity questions.

## Management Commands

### StreetEasy Data Collection
```bash
# Scrape StreetEasy property data
python manage.py scrape_streeteasy --property-type=rental --neighborhood=Manhattan --verbose

# Scrape liquidity events
python manage.py scrape_liquidity_events --min-amount=1000000 --days-back=365 --include-news --verbose

# Ask liquidity questions
python manage.py ask_liquidity_question "Who has had the largest liquidity event in the past year?"
```

### SEC Data Analysis
```bash
# Analyze specific company
python manage.py analyze_sec_liquidity --company=SPG

# General real estate company analysis
python manage.py analyze_sec_liquidity --days-back=365 --correlate

# Ask SEC-specific questions
python manage.py analyze_sec_liquidity --question="What recent 8-K filings have real estate companies made?"
```

## Data Models

### StreetEasyProperty
Stores individual property listings with details like:
- Address, neighborhood, borough
- Price, bedrooms, bathrooms, square footage
- Amenities, building information
- Agent and listing details
- Images and raw scraped data

### StreetEasyLiquidityEvent
Tracks major financial transactions including:
- Transaction amount and parties involved
- Property/asset details
- Event type (sale, merger, acquisition, etc.)
- Source information and confidence scores
- Cross-references with entities

### StreetEasyEntity
Maintains profiles of real estate entities:
- Company/individual information
- Transaction history and metrics
- Market focus areas
- Related entities and aliases

## Usage Examples

### 1. Find Largest Liquidity Events
```python
import requests

# Comprehensive analysis combining all data sources
response = requests.post('http://localhost:8000/api/streeteasy/comprehensive-analysis/', 
    json={
        "question": "Who has had the largest liquidity event in the past year?",
        "timeframe_days": 365
    }
)

result = response.json()
print(result['analysis']['combined_answer'])
```

### 2. Search for Properties
```python
# Search for rentals in Manhattan
response = requests.get('http://localhost:8000/api/streeteasy/rentals/', 
    params={
        'neighborhood': 'Manhattan',
        'min_price': 3000,
        'max_price': 8000,
        'min_bedrooms': 1
    }
)

properties = response.json()['properties']
for prop in properties[:5]:
    print(f"{prop['address']} - {prop['formatted_price']}")
```

### 3. Get SEC Company Information
```python
# Get company profile
response = requests.get('http://localhost:8000/api/streeteasy/sec/company/SPG/')
profile = response.json()['profile']

print(f"Company: {profile['company_info']['name']}")
print(f"Recent filings: {len(profile['recent_filings'])}")
```

### 4. Natural Language Queries
```python
# Ask about properties
response = requests.post('http://localhost:8000/api/streeteasy/query/',
    json={"query": "Find me studios in East Village under $3000"}
)

# Ask about liquidity events
response = requests.post('http://localhost:8000/api/streeteasy/liquidity/question/',
    json={"question": "What are the biggest real estate deals this year?"}
)

# Ask about SEC data
response = requests.post('http://localhost:8000/api/streeteasy/sec/question/',
    json={"question": "Show me financial data for Prologis"}
)
```

## Installation and Setup

### 1. Install Dependencies
```bash
pip install django requests beautifulsoup4 lxml python-dateutil
```

### 2. Configure Django Settings
Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    # ... other apps
    'streeteasy_integration',
]
```

### 3. Run Migrations
```bash
python manage.py makemigrations streeteasy_integration
python manage.py migrate
```

### 4. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 5. Start Development Server
```bash
python manage.py runserver
```

### 6. Access Admin Interface
Visit `http://localhost:8000/admin/` to manage data through Django admin.

## Key Capabilities

### Answering "Who has had the largest liquidity event in the past year?"

The platform can answer this question by:

1. **Scraping StreetEasy** for high-value property transactions
2. **Analyzing SEC filings** for corporate material events
3. **Cross-referencing data** to identify related transactions
4. **Ranking events** by transaction amount
5. **Providing context** about the parties involved and transaction details

Example response:
```
Based on analysis of StreetEasy and SEC EDGAR data over the past 365 days, 
here are the largest liquidity events:

1. Blackstone Group - $2.1B (2024-03-15) [Source: SEC]
   Related to: acquisition, real estate, portfolio

2. ABC Real Estate Corp - $485M (2024-02-28) [Source: StreetEasy] 
   Property: 432 Park Avenue, Manhattan
   Location: Midtown East

3. Simon Property Group - $320M (2024-01-10) [Source: SEC]
   Related to: divestiture, property sale, agreement
```

## Rate Limiting and Ethics

- **StreetEasy**: 2-second delays between requests
- **SEC EDGAR**: 0.1-second delays (10 requests/second max)
- **Respectful scraping**: User agents, error handling, timeout management
- **Data caching**: Reduces redundant requests
- **Incremental updates**: Only fetches new data when needed

## Admin Interface

The Django admin provides management for:
- Property listings with filtering and search
- Liquidity events with transaction analysis
- Entity profiles with relationship tracking
- Search history and performance metrics
- Data quality monitoring and updates

## Future Enhancements

1. **Additional Data Sources**: Integrate with other real estate platforms
2. **Machine Learning**: Predictive models for market trends
3. **Real-time Updates**: Webhook integration for live data feeds
4. **Advanced Analytics**: Market sentiment analysis and forecasting
5. **API Authentication**: Rate limiting and access control
6. **Data Export**: CSV/Excel export functionality
7. **Visualization**: Charts and graphs for data presentation

## Support and Maintenance

The platform includes comprehensive error handling, logging, and monitoring capabilities. Regular maintenance tasks include:

- Data freshness validation
- Rate limit compliance monitoring  
- Database performance optimization
- API endpoint health checks
- Security updates and patches

## Contributing

To extend the platform:

1. Add new data sources in separate modules
2. Follow the existing pattern for scrapers and analyzers
3. Implement proper rate limiting and error handling
4. Add comprehensive tests for new functionality
5. Update documentation for new endpoints or features