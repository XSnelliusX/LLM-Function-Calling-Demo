import json
import os
import requests
from groq import Groq
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# Load environment variables and initialize clients
# ------------------------------------------------------------------------------

# Load environment variables from .env file
load_dotenv()

# Retrieve API keys from environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
alphavantage_api_key = os.getenv("alphavantage_API_KEY")

# Ensure required API keys are provided
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")
if not alphavantage_api_key:
    raise ValueError("alphavantage_API_KEY environment variable is not set")

# Initialize Groq client and specify model
client = Groq(api_key=groq_api_key)
model = "llama-3.3-70b-versatile"

# ------------------------------------------------------------------------------
# Alphavantage API Functions for Stock Data
# ------------------------------------------------------------------------------

def search_stock_symbol(keywords: str) -> str:
    """
    Search for stock symbols using Alphavantage's SYMBOL_SEARCH endpoint.
    
    Args:
        keywords (str): Company name or keywords to search for.
        
    Returns:
        str: JSON string of formatted search results sorted by match score.
    """
    url = f'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={keywords}&apikey={alphavantage_api_key}'
    response = requests.get(url)
    data = response.json()

    if 'bestMatches' in data:
        # Sort matches by match score in descending order
        matches = sorted(
            data['bestMatches'],
            key=lambda x: float(x.get('9. matchScore', 0)),
            reverse=True
        )
        # Format the results for clarity
        results = [{
            'symbol': match['1. symbol'],
            'name': match['2. name'],
            'region': match['4. region'],
            'score': float(match['9. matchScore'])
        } for match in matches]
        return json.dumps(results)
    return json.dumps([])

def get_stock_price(symbol: str) -> str:
    """
    Retrieve the current stock price and related information using Alphavantage's GLOBAL_QUOTE endpoint.
    
    Args:
        symbol (str): The stock symbol to look up.
        
    Returns:
        str: JSON string containing stock price information or an error message.
    """
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alphavantage_api_key}'
    response = requests.get(url)
    data = response.json()

    if 'Global Quote' in data:
        quote = data['Global Quote']
        return json.dumps({
            'symbol': quote.get('01. symbol'),
            'price': quote.get('05. price'),
            'change': quote.get('09. change'),
            'change_percent': quote.get('10. change percent')
        })
    return json.dumps({'error': 'No price data available'})

# ------------------------------------------------------------------------------
# Groq Chat API Helper Functions
# ------------------------------------------------------------------------------

def process_stream(response) -> dict:
    """
    Process a streaming response from the Groq API.
    
    This function prints the assistant's reply as it arrives and accumulates both
    the full content and any tool calls encountered in the stream.
    
    Args:
        response: A streaming response from the Groq chat API.
    
    Returns:
        dict: A dictionary with the assistant's role, full content, and a list of tool calls.
    """
    full_text = ""
    tool_calls = []
    for chunk in response:
        delta = chunk.choices[0].delta
        # Print and accumulate text content if available
        if hasattr(delta, 'content') and delta.content:
            print(delta.content, end='', flush=True)
            full_text += delta.content
        # Accumulate any tool calls if provided
        if hasattr(delta, 'tool_calls') and delta.tool_calls:
            tool_calls.extend(delta.tool_calls)
    return {"role": "assistant", "content": full_text, "tool_calls": tool_calls}

def get_model_response(messages: list, tools: list) -> dict:
    """
    Call the Groq chat API with the given messages and tools, then process the streaming response.
    
    Args:
        messages (list): The conversation history.
        tools (list): A list of tool definitions available to the assistant.
        
    Returns:
        dict: Processed assistant response including content and any tool calls.
    """
    response_stream = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_completion_tokens=4096,
        stream=True
    )
    return process_stream(response_stream)

def process_tool_calls(response_message: dict, messages: list, available_functions: dict):
    """
    Process any tool calls from the assistant's response.
    
    For each tool call, the corresponding function is called with the provided arguments,
    and the result is appended to the conversation history.
    
    Args:
        response_message (dict): The assistant's response containing potential tool calls.
        messages (list): The conversation history to be updated with tool responses.
        available_functions (dict): Mapping from tool names to actual functions.
    """
    for tool_call in response_message.get("tool_calls", []):
        function_name = tool_call.function.name
        function_to_call = available_functions.get(function_name)
        if function_to_call:
            # Parse the JSON arguments provided by the tool call
            function_args = json.loads(tool_call.function.arguments)
            # Call the corresponding function with its arguments
            function_response = function_to_call(**function_args)
            # Append the function result as a new message in the conversation history
            messages.append({
                "role": "tool",
                "content": str(function_response),
                "tool_call_id": tool_call.id,
            })

# ------------------------------------------------------------------------------
# Main Stock Information Flow
# ------------------------------------------------------------------------------

def get_stock_info():
    """
    Orchestrates the process of querying for stock information.
    
    1. Gets a stock or company name from the user.
    2. Sets up initial conversation messages and tool definitions.
    3. Makes an initial call to the Groq model.
    4. Processes any tool calls (e.g. searching for stock symbols) and updates the conversation.
    5. Makes follow-up calls based on assistant feedback and user input.
    6. Processes additional tool calls (e.g. fetching stock price) as needed.
    """
    # Get the stock/company search query from the user
    stock_query = input("Enter the stock or company name you want to search for: ")

    # Define the initial conversation context for the assistant
    messages = [
        {
            "role": "system", 
            "content": (
                "You are a helpful stock market assistant. When searching for a stock, first help find the correct symbol use the search_stock_symbol tool to find matching stock symbols, then get its current price using the get_stock_price tool. If multiple symbols are found, ask the user which one they want to look up, return only a numbered list of symbols along with the company name and region, with no additional text or questions. Present the information in a clear, organized way."
            )
        },
        {"role": "user", "content": f"What's the current stock price for {stock_query}?"}
    ]

    # Define tool functions available to the assistant
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_stock_symbol",
                "description": "Search for stock symbols by company name or keywords",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "string",
                            "description": "Company name or keywords to search for",
                        }
                    },
                    "required": ["keywords"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_stock_price",
                "description": "Get the current stock price and related information for a given symbol",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "The stock symbol to look up",
                        }
                    },
                    "required": ["symbol"],
                },
            },
        }
    ]

    # Mapping of available function names to their actual implementations
    available_functions = {
        "search_stock_symbol": search_stock_symbol,
        "get_stock_price": get_stock_price,
    }

    # --------------------------
    # First Assistant Call: Search for stock symbol
    # --------------------------
    initial_response = get_model_response(messages, tools)
    messages.append(initial_response)
    
    # Process any tool calls from the initial response (e.g., symbol search)
    process_tool_calls(initial_response, messages, available_functions)

    # --------------------------
    # Second Assistant Call: Incorporate tool results into conversation
    # --------------------------
    final_response = get_model_response(messages, tools)
    messages.append(final_response)

    # Ask the user to choose one of the stock options (if multiple were provided)
    user_choice = input("\n\nEnter the number of your chosen symbol: ")
    messages.append({"role": "user", "content": f"I choose option {user_choice}."})

    # --------------------------
    # Third Assistant Call: Process user choice and fetch further details
    # --------------------------
    final_choice_response = get_model_response(messages, tools)
    messages.append(final_choice_response)

    # Process any additional tool calls (e.g., fetching the current price)
    if final_choice_response.get("tool_calls"):
        process_tool_calls(final_choice_response, messages, available_functions)
        # Final call to incorporate the tool response results
        final_response = get_model_response(messages, tools)

# ------------------------------------------------------------------------------
# Main Program Start
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    get_stock_info()
