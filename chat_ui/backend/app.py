from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
import os
import requests
import json
from datetime import datetime
import logging

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

class DataAgent:
    def __init__(self):
        self.client = openai.OpenAI(api_key=openai.api_key)
        self.system_prompt = """
        You are an AI Data Assistant specialized in querying and analyzing data from EDGAR (SEC filings) and StreetEasy (NYC real estate) APIs.

        EDGAR API Capabilities:
        - Company filings (10-K, 10-Q, 8-K, proxy statements)
        - Financial data and metrics
        - Insider trading information
        - Company facts and submissions
        - Mutual fund data

        StreetEasy API Capabilities:
        - Real estate listings (rentals and sales)
        - Market trends and analytics
        - Neighborhood data
        - Price history and comparisons
        - Building information

        When users ask questions:
        1. Determine which API(s) to use based on the query
        2. Extract relevant parameters from the user's request
        3. Make appropriate API calls
        4. Analyze and summarize the data
        5. Present findings in a clear, conversational manner

        Always provide specific, actionable insights and offer to dive deeper into any aspect of the data.
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
                    1. Which API(s) to use (EDGAR, StreetEasy, or both)
                    2. What specific data to fetch
                    3. Key parameters to extract
                    
                    Query: {user_message}
                    
                    Respond in JSON format:
                    {{
                        "apis": ["edgar" | "streeteasy"],
                        "query_type": "description",
                        "parameters": {{
                            "company": "if applicable",
                            "ticker": "if applicable",
                            "location": "if applicable",
                            "property_type": "if applicable",
                            "price_range": "if applicable"
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
            
            if "edgar" in intent_data.get("apis", []):
                api_data["edgar"] = self.query_edgar(intent_data)
            
            if "streeteasy" in intent_data.get("apis", []):
                api_data["streeteasy"] = self.query_streeteasy(intent_data)
            
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

    def query_streeteasy(self, intent_data):
        """Query StreetEasy API for real estate data"""
        try:
            params = intent_data.get("parameters", {})
            results = {}
            
            # Note: StreetEasy API access is limited, so we'll simulate responses
            # In production, you'd need proper API credentials and endpoints
            
            location = params.get("location", "Manhattan")
            property_type = params.get("property_type", "rental")
            
            # Simulated real estate data (replace with actual API calls)
            results = {
                "location": location,
                "property_type": property_type,
                "sample_data": {
                    "average_rent": "$3,200",
                    "median_price": "$1,200,000",
                    "inventory": "1,234 listings",
                    "trend": "2.3% increase YoY"
                },
                "note": "This is simulated data. Actual StreetEasy API integration requires proper credentials."
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying StreetEasy: {str(e)}")
            return {"error": f"StreetEasy API error: {str(e)}"}

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
            elif api_data.get("streeteasy"):
                data_for_frontend = self.format_real_estate_data(api_data["streeteasy"])
            
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

    def format_real_estate_data(self, streeteasy_data):
        """Format StreetEasy data for frontend visualization"""
        try:
            sample_data = streeteasy_data.get("sample_data", {})
            
            metrics = [
                {"label": "Average Rent", "value": sample_data.get("average_rent", "N/A")},
                {"label": "Median Price", "value": sample_data.get("median_price", "N/A")},
                {"label": "Active Listings", "value": sample_data.get("inventory", "N/A")},
                {"label": "Market Trend", "value": sample_data.get("trend", "N/A")}
            ]
            
            return {
                "type": "metrics",
                "content": metrics
            }
            
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
            "streeteasy": "simulated"
        }
    })

if __name__ == '__main__':
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
    
    app.run(debug=True, host='0.0.0.0', port=5000)