# AI Data Assistant - EDGAR & StreetEasy Chat UI

A modern chat interface powered by OpenAI that allows natural language queries to the EDGAR API (SEC filings) and StreetEasy API (NYC real estate data).

## 🚀 Features

- **Natural Language Queries**: Ask questions in plain English about companies, financials, and real estate
- **Dual API Integration**: Access both EDGAR (SEC) and StreetEasy data through one interface
- **AI-Powered Analysis**: OpenAI GPT-4 analyzes and summarizes data from multiple sources
- **Beautiful UI**: Modern, responsive chat interface with data visualizations
- **Real-time Data**: Live data from SEC filings and real estate markets

## 📊 Supported Queries

### EDGAR API (Financial Data)
- Company financials: "Show me Tesla's latest 10-K filing"
- Compare companies: "Compare Apple and Microsoft revenue"
- Market analysis: "What are Amazon's recent SEC filings?"
- Financial metrics: "Show me Google's balance sheet data"

### StreetEasy API (Real Estate)
- Property search: "Find apartments in Manhattan under $3000"
- Market trends: "Show real estate trends in Brooklyn"
- Neighborhood data: "What's the average rent in SoHo?"
- Price analysis: "Compare condo prices in NYC boroughs"

## 🛠 Installation

### Prerequisites
- Python 3.8+
- OpenAI API key
- Modern web browser

### 1. Clone the Repository
```bash
git clone <repository-url>
cd chat_ui
```

### 2. Set Up Backend
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp ../.env.example .env
# Edit .env and add your OpenAI API key
```

### 4. Install Frontend Dependencies
The frontend uses vanilla JavaScript with CDN resources, so no additional installation is needed.

## 🔧 Configuration

### OpenAI API Key
1. Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add it to your `.env` file:
```
OPENAI_API_KEY=your_actual_api_key_here
```

### API Endpoints
The application uses:
- **EDGAR API**: `https://data.sec.gov` (public, no key required)
- **StreetEasy API**: Currently simulated (requires partnership for real data)

## 🚀 Running the Application

### Start the Backend Server
```bash
cd backend
python app.py
```

The server will start on `http://localhost:5000`

### Access the Frontend
Open your browser and navigate to:
```
http://localhost:5000
```

## 📝 Usage Examples

### Financial Queries
```
"Show me the latest 10-K filing for Tesla"
"Compare revenue between Apple and Microsoft"
"What are Amazon's total assets?"
"Find recent insider trading for NVIDIA"
```

### Real Estate Queries
```
"Find apartments for rent in Manhattan under $3000"
"Show market trends in Brooklyn"
"What's the average home price in Queens?"
"Compare rental prices across NYC boroughs"
```

### Combined Queries
```
"Show me real estate trends and tech company performance in 2024"
"How do NYC property values correlate with financial sector growth?"
```

## 🏗 Architecture

```
Frontend (HTML/CSS/JS)
    ↓ HTTP Requests
Flask Backend (Python)
    ↓ API Calls
┌─────────────┬─────────────┐
│ OpenAI API  │ EDGAR API   │ StreetEasy API
│ (Analysis)  │ (Financial) │ (Real Estate)
└─────────────┴─────────────┘
```

### Components
- **Frontend**: Vanilla JavaScript chat interface with modern CSS
- **Backend**: Flask server with OpenAI integration
- **Data Agent**: AI agent that processes queries and fetches data
- **APIs**: EDGAR for financial data, StreetEasy for real estate

## 🔌 API Integrations

### EDGAR API
- **Endpoint**: `https://data.sec.gov`
- **Data**: SEC filings, company facts, financial metrics
- **Authentication**: None required (public API)
- **Rate Limits**: Respectful usage recommended

### StreetEasy API
- **Status**: Currently simulated
- **Real Integration**: Requires partnership agreement
- **Data**: NYC real estate listings, trends, analytics

### OpenAI API
- **Model**: GPT-4
- **Usage**: Query analysis, data interpretation, response generation
- **Cost**: Based on token usage

## 🎨 Frontend Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Chat**: Instant message updates
- **Data Visualization**: Tables, metrics cards, charts
- **Loading States**: Smooth animations during API calls
- **Error Handling**: User-friendly error messages
- **Suggested Queries**: Quick-start examples

## 🔧 Development

### Adding New Data Sources
1. Create a new query method in `DataAgent` class
2. Update the intent analysis prompt
3. Add data formatting functions
4. Update frontend visualization components

### Customizing the UI
- Modify `styles.css` for appearance changes
- Update `script.js` for new functionality
- Edit `index.html` for structure changes

### Environment Variables
```bash
OPENAI_API_KEY=your_key
FLASK_ENV=development
FLASK_DEBUG=True
```

## 📊 Data Visualization

The app automatically formats responses with:
- **Metric Cards**: Key financial/real estate metrics
- **Data Tables**: Structured information display
- **Trend Indicators**: Visual market direction cues
- **Interactive Elements**: Clickable data points

## 🔒 Security & Privacy

- **API Keys**: Stored securely in environment variables
- **Data Handling**: No persistent storage of user queries
- **CORS**: Configured for secure cross-origin requests
- **Input Validation**: Sanitized user inputs

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   ```
   Solution: Check your .env file and ensure the API key is valid
   ```

2. **EDGAR API Rate Limiting**
   ```
   Solution: Implement request delays and retry logic
   ```

3. **Frontend Not Loading**
   ```
   Solution: Ensure Flask server is running on port 5000
   ```

## 📈 Future Enhancements

- [ ] Real StreetEasy API integration
- [ ] Additional financial data sources
- [ ] Chart visualizations
- [ ] Export functionality
- [ ] User authentication
- [ ] Query history
- [ ] Advanced filtering options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support, please:
1. Check the troubleshooting section
2. Review the API documentation
3. Submit an issue on GitHub

---

**Built with ❤️ using OpenAI, Flask, and modern web technologies**