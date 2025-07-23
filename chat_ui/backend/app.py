from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
import os
import requests
import json
from datetime import datetime
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# API configurations
EDGAR_BASE_URL = "https://data.sec.gov"
STREETEASY_BASE_URL = "https://streeteasy.com/nyc/api"

# Import our scrapers
from scrapers import (
    RealEstateTransactionScraper, 
    PropertyOwnerScraper, 
    MarketAnalysisScraper,
    analyze_buyer_patterns,
    format_currency
)

class DataAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=openai.api_key)
        # Initialize scrapers
        self.real_estate_scraper = RealEstateTransactionScraper()
        self.owner_scraper = PropertyOwnerScraper()
        self.market_scraper = MarketAnalysisScraper()
        
        self.system_prompt = """
        You are an AI Data Assistant specialized in querying and analyzing data from EDGAR (SEC filings) and Real Estate transaction databases.

        EDGAR API Capabilities:
        - Company filings (10-K, 10-Q, 8-K, proxy statements)
        - Financial data and metrics
        - Insider trading information
        - Company facts and submissions
        - Mutual fund data

        Real Estate Data Capabilities:
        - High-value property transactions ($25M+)
        - Property ownership records and buyer/seller information
        - Luxury real estate market trends and analytics
        - Celebrity and high-profile real estate transactions
        - Property tax records and assessed values
        - Deed information and financing details

        When users ask about real estate transactions, you can:
        - Search for properties bought/sold over specific price thresholds
        - Identify buyers and sellers in high-value transactions
        - Analyze luxury market trends by zip code or area
        - Find ownership patterns and investment activity
        - Track celebrity or notable person real estate activity

        When users ask questions:
        1. Determine which data source(s) to use based on the query
        2. Extract relevant parameters (zip codes, price ranges, names, dates)
        3. Retrieve and analyze the appropriate data
        4. Present findings with specific details and insights
        5. Offer to dive deeper into any aspect of the data

        Always provide specific, actionable insights and offer to explore related information.
        """

    def process_query(self, user_message):
        """Process user query and determine appropriate API calls"""
        try:
            # Determine intent and extract parameters
            intent_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""
                    Analyze this query and determine:
                    1. Which data source(s) to use (EDGAR, real_estate, or both)
                    2. What specific data to fetch
                    3. Key parameters to extract
                    
                    Query: {user_message}
                    
                    Respond in JSON format:
                    {{
                        "data_sources": ["edgar" | "real_estate"],
                        "query_type": "description",
                        "parameters": {{
                            "company": "if applicable",
                            "ticker": "if applicable",
                            "zip_code": "if applicable",
                            "location": "if applicable", 
                            "min_price": "if applicable (numeric)",
                            "max_price": "if applicable (numeric)",
                            "person_name": "if applicable",
                            "transaction_type": "buy/sell/both"
                        }},
                        "specific_request": "what exactly to fetch"
                    }}
                    """}
                ],
                temperature=0.1
            )
            
            intent_data = json.loads(intent_response.choices[0].message.content)
            logger.info(f"Intent analysis: {intent_data}")
            
            # Fetch data based on intent
            api_data = {}
            
            if "edgar" in intent_data.get("data_sources", []):
                api_data["edgar"] = self.query_edgar(intent_data)
            
            if "real_estate" in intent_data.get("data_sources", []):
                api_data["real_estate"] = self.query_real_estate(intent_data)
            
            # Generate response using OpenAI with the fetched data
            response = self.generate_response(user_message, api_data, intent_data)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error while processing your request. Please try rephrasing your question or ask about specific companies or locations.",
                "data": None
            }

    def query_edgar(self, intent_data):
        """Query EDGAR API for financial/company data"""
        try:
            params = intent_data.get("parameters", {})
            results = {}
            
            # Company lookup
            if params.get("company") or params.get("ticker"):
                search_term = params.get("ticker") or params.get("company")
                
                # Get company CIK
                company_tickers_url = f"{EDGAR_BASE_URL}/files/company_tickers.json"
                headers = {
                    'User-Agent': 'AI Data Assistant contact@example.com'
                }
                
                response = requests.get(company_tickers_url, headers=headers)
                if response.status_code == 200:
                    companies = response.json()
                    
                    # Find matching company
                    for company_data in companies.values():
                        if (search_term.lower() in company_data.get('title', '').lower() or 
                            search_term.upper() == company_data.get('ticker', '').upper()):
                            
                            cik = str(company_data['cik_str']).zfill(10)
                            
                            # Get company facts
                            facts_url = f"{EDGAR_BASE_URL}/api/xbrl/companyfacts/CIK{cik}.json"
                            facts_response = requests.get(facts_url, headers=headers)
                            
                            if facts_response.status_code == 200:
                                facts_data = facts_response.json()
                                results['company_facts'] = facts_data
                            
                            # Get recent filings
                            submissions_url = f"{EDGAR_BASE_URL}/api/xbrl/companyconcept/CIK{cik}/us-gaap/Assets.json"
                            submissions_response = requests.get(submissions_url, headers=headers)
                            
                            if submissions_response.status_code == 200:
                                submissions_data = submissions_response.json()
                                results['submissions'] = submissions_data
                            
                            break
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying EDGAR: {str(e)}")
            return {"error": f"EDGAR API error: {str(e)}"}

    def query_real_estate(self, intent_data):
        """Query real estate transaction data"""
        try:
            params = intent_data.get("parameters", {})
            results = {}
            
            zip_code = params.get("zip_code", "")
            location = params.get("location", "")
            min_price = params.get("min_price", 25000000)  # Default to $25M
            person_name = params.get("person_name", "")
            
            # Convert min_price to int if it's a string
            if isinstance(min_price, str):
                # Extract numbers from string like "$25M" or "25 million"
                price_str = min_price.upper().replace('$', '').replace(',', '')
                if 'M' in price_str or 'MILLION' in price_str:
                    price_num = float(re.findall(r'[\d.]+', price_str)[0]) * 1000000
                    min_price = int(price_num)
                elif 'K' in price_str or 'THOUSAND' in price_str:
                    price_num = float(re.findall(r'[\d.]+', price_str)[0]) * 1000
                    min_price = int(price_num)
                else:
                    min_price = int(float(price_str)) if price_str.replace('.', '').isdigit() else 25000000
            
            # Search for high-value transactions
            if zip_code or location:
                search_zip = zip_code if zip_code else self._extract_zip_from_location(location)
                transactions = self.real_estate_scraper.search_high_value_transactions(search_zip, min_price)
                results['transactions'] = transactions
                
                if transactions:
                    # Get market analysis for the area
                    market_data = self.market_scraper.get_luxury_market_trends(search_zip)
                    results['market_analysis'] = market_data
                    
                    # Analyze buyer patterns
                    buyer_analysis = analyze_buyer_patterns(transactions)
                    results['buyer_patterns'] = buyer_analysis
            
            # Search for specific person's real estate activity
            if person_name:
                from scrapers import search_celebrity_real_estate
                celebrity_transactions = search_celebrity_real_estate(person_name)
                results['celebrity_transactions'] = celebrity_transactions
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying real estate data: {str(e)}")
            return {"error": f"Real estate data error: {str(e)}"}
    
    def _extract_zip_from_location(self, location):
        """Extract or map location to zip code"""
        # Simple mapping for demo - in production would use geocoding
        location_map = {
            'manhattan': '10021',
            'beverly hills': '90210', 
            'palo alto': '94301',
            'miami beach': '33109',
            'aspen': '81611',
            'hamptons': '11962',
            'malibu': '90265'
        }
        return location_map.get(location.lower(), '90210')  # Default to Beverly Hills

    def generate_response(self, user_message, api_data, intent_data):
        """Generate final response using OpenAI with API data"""
        try:
            # Prepare context with API data
            context = f"""
            User Query: {user_message}
            Intent Analysis: {json.dumps(intent_data, indent=2)}
            API Data Retrieved: {json.dumps(api_data, indent=2, default=str)}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""
                    Based on the following data, provide a comprehensive and helpful response to the user's query.
                    
                    {context}
                    
                    Guidelines:
                    1. Summarize key findings from the API data
                    2. Provide specific numbers and facts when available
                    3. Offer insights and analysis
                    4. Suggest follow-up questions or deeper analysis
                    5. If data is limited, explain what additional information could be helpful
                    
                    Format your response conversationally but include specific data points.
                    """}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
            # Determine if we should format data for visualization
            data_for_frontend = None
            if api_data.get("edgar", {}).get("company_facts"):
                data_for_frontend = self.format_financial_data(api_data["edgar"])
            elif api_data.get("real_estate"):
                data_for_frontend = self.format_real_estate_transactions(api_data["real_estate"])
            
            return {
                "response": ai_response,
                "data": data_for_frontend
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "response": "I found some data but had trouble analyzing it. Could you please rephrase your question?",
                "data": None
            }

    def format_financial_data(self, edgar_data):
        """Format EDGAR data for frontend visualization"""
        try:
            if not edgar_data.get("company_facts"):
                return None
                
            facts = edgar_data["company_facts"]
            
            # Extract key metrics for display
            metrics = []
            
            # Look for common financial metrics
            us_gaap = facts.get("facts", {}).get("us-gaap", {})
            
            for metric_name, metric_data in us_gaap.items():
                if metric_name in ["Assets", "Revenues", "NetIncomeLoss", "StockholdersEquity"]:
                    units = metric_data.get("units", {})
                    usd_data = units.get("USD", [])
                    
                    if usd_data:
                        latest = max(usd_data, key=lambda x: x.get("end", ""))
                        metrics.append({
                            "label": metric_name.replace("NetIncomeLoss", "Net Income"),
                            "value": f"${latest.get('val', 0):,}",
                            "period": latest.get("end", "")
                        })
            
            return {
                "type": "metrics",
                "content": metrics
            }
            
        except Exception as e:
            logger.error(f"Error formatting financial data: {str(e)}")
            return None

    def format_real_estate_transactions(self, real_estate_data):
        """Format real estate transaction data for frontend visualization"""
        try:
            transactions = real_estate_data.get("transactions", [])
            
            if transactions:
                # Create a table format for high-value transactions
                headers = ["Address", "Price", "Date", "Buyer", "Details"]
                rows = []
                
                for transaction in transactions[:10]:  # Limit to top 10
                    price_formatted = format_currency(transaction.get('price', 0))
                    sqft = transaction.get('sqft', 'Unknown')
                    details = f"{sqft} sqft" if sqft != 'Unknown' else "Details available"
                    
                    row = [
                        transaction.get('address', 'N/A'),
                        price_formatted,
                        transaction.get('sale_date', 'N/A'),
                        transaction.get('buyer', 'N/A'),
                        details
                    ]
                    rows.append(row)
                
                return {
                    "type": "table",
                    "content": {
                        "headers": headers,
                        "rows": rows
                    }
                }
            
            # If no transactions, show market metrics
            market_data = real_estate_data.get("market_analysis", {})
            if market_data:
                metrics = [
                    {"label": "Average Sale Price", "value": format_currency(market_data.get("average_sale_price", 0))},
                    {"label": "Transactions (12mo)", "value": str(market_data.get("transactions_last_12_months", 0))},
                    {"label": "Market Trend", "value": market_data.get("market_trend", "N/A")},
                    {"label": "YoY Change", "value": market_data.get("year_over_year_change", "N/A")}
                ]
                
                return {
                    "type": "metrics", 
                    "content": metrics
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error formatting real estate data: {str(e)}")
            return None

# Initialize the data agent
data_agent = DataAgent()

@app.route('/')
def index():
    return send_from_directory('../', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../', path)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({
                "response": "Please enter a question about financial data or real estate information.",
                "data": None
            })
        
        # Process the query with our AI agent
        result = data_agent.process_query(user_message)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        return jsonify({
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment.",
            "data": None
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "openai": "configured" if openai.api_key else "missing_key",
            "edgar": "available",
            "real_estate_scrapers": "active"
        }
    })

if __name__ == '__main__':
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)