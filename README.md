# LLM Function Calling Demos

This repository contains two demonstration applications showcasing the integration of Large Language Models (LLM) with function calling capabilities using the Groq API. The demos include a stock price lookup application and a weather information service.

## Projects

### 1. Stock Price Demo
A CLI application that allows users to search for stock symbols and get real-time stock price information using the AlphaVantage API.

### 2. Weather Demo
A demonstration of weather information retrieval using mock data (for educational purposes).

## Prerequisites

- Python 3.6 or higher
- Groq API key
- AlphaVantage API key (for stock price demo)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install required packages:
```bash
pip install groq python-dotenv requests
```

3. Get API Keys:

   a. **Groq API Key**:
   - Visit [Groq's website](https://console.groq.com)
   - Sign up for an account
   - Navigate to API section to generate your API key

   b. **AlphaVantage API Key** (for stock price demo):
   - Go to [AlphaVantage](https://www.alphavantage.co)
   - Sign up for a free API key

4. Create a `.env` file in the project root:
```plaintext
GROQ_API_KEY=your_groq_api_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
```

## Running the Demos

### Stock Price Demo

Run the stock price demo with:
```bash
python llm_function_stock_price_demo.py
```

You will be prompted to enter a company name or stock symbol. The application will:
1. Search for matching stock symbols
2. Display a list of matches
3. Let you choose the correct symbol
4. Show current stock price and related information

Example interaction:
```
Enter the stock or company name you want to search for: Apple
1. AAPL - Apple Inc. (United States)
2. APLE - Apple Hospitality REIT Inc (United States)
3. APRU - Apple Rush Company Inc (United States)

Enter the number of your chosen symbol: 1
The current price of Apple Inc. (AAPL) is $408.43, with a change of -$2.11 (-0.51%)
```

### Weather Demo

Run the weather demo with:
```bash
python llm_function_weather_demo.py
```

This demo uses mock data for demonstration purposes and will show weather information for predefined cities (New York and London).

## Note

- The weather demo uses mock data and is intended for educational purposes only.
- The stock price demo uses real-time data from AlphaVantage API, which has rate limits on free tier accounts.
- Keep your API keys secure and never commit them to version control.