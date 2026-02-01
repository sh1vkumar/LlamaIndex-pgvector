import configparser
import os
from sqlalchemy import create_engine, text

# Load config
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini')
config.read(config_path)

user = config['postgres']['user']
password = config['postgres']['password']
table_name = config['postgres']['table_name']
db_name = "postgres"

# Create engine
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@localhost/{db_name}")

def execute_query(query):
    """Execute a SQL query and return results"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchall()
    except Exception as e:
        return f"Error: {e}"

def natural_language_to_sql(question):
    """Convert natural language to SQL (simple pattern matching)"""
    question = question.lower()
    
    # Common patterns
    if "closing price" in question or "close price" in question:
        if "aapl" in question:
            return f"SELECT date, close FROM {table_name} WHERE name = 'AAPL' ORDER BY date DESC LIMIT 10"
        elif "ppl" in question:
            return f"SELECT date, close FROM {table_name} WHERE name = 'PPL' ORDER BY date DESC LIMIT 10"
    
    if "highest" in question and "price" in question:
        return f"SELECT name, MAX(high) as highest_price FROM {table_name} GROUP BY name ORDER BY highest_price DESC LIMIT 10"
    
    if "average volume" in question:
        return f"SELECT name, AVG(volume) as avg_volume FROM {table_name} GROUP BY name ORDER BY avg_volume DESC LIMIT 10"
    
    if "show me" in question and "stocks" in question:
        return f"SELECT DISTINCT name FROM {table_name} ORDER BY name LIMIT 20"
    
    # Default query
    return f"SELECT * FROM {table_name} LIMIT 5"

print(f"Simple SQL Query Interface for table '{table_name}'")
print("Ask questions like:")
print("- What is the closing price for AAPL?")
print("- Show me the highest prices")
print("- What is the average volume?")
print("- Show me all stocks")
print("\nType 'exit' to quit")

while True:
    try:
        user_input = input("\nUser: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        # Convert to SQL
        sql_query = natural_language_to_sql(user_input)
        print(f"SQL: {sql_query}")
        
        # Execute query
        results = execute_query(sql_query)
        
        if isinstance(results, str):  # Error case
            print(results)
        else:
            print(f"Results ({len(results)} rows):")
            for i, row in enumerate(results[:10]):  # Show first 10 results
                print(f"  {i+1}: {row}")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more rows")
        
    except KeyboardInterrupt:
        print("\nExiting...")
        break
    except Exception as e:
        print(f"An error occurred: {e}")