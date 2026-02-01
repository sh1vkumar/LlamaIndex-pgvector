import configparser
import os
import sys
from sqlalchemy import create_engine, text
from llama_index.core import SQLDatabase, Settings
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
import torch

# 1. Load Configuration
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini')
config.read(config_path)

if 'postgres' not in config:
    print("Error: [postgres] section missing in secrets.ini")
    sys.exit(1)

user = config['postgres']['user']
password = config['postgres']['password']
table_name = config['postgres']['table_name']
db_name = "postgres" # Standard default database 

# 2. Setup Database
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@localhost/{db_name}")

# Debug: Check if table exists before creating SQLDatabase
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tables = [row[0] for row in result]
        print(f"Available tables: {tables}")
        
        if table_name not in tables:
            print(f"Error: Table '{table_name}' not found in database '{db_name}'")
            print(f"Available tables: {tables}")
            sys.exit(1)
        else:
            print(f"Found table: {table_name}")
            
except Exception as e:
    print(f"Database connection error: {e}")
    sys.exit(1)

sql_database = SQLDatabase(engine, include_tables=[table_name])

# 3. Setup LLM (Local)
# Try to get token from env var, fallback to secrets.ini
hf_token = os.environ.get("HF_TOKEN")
if not hf_token and 'huggingface' in config:
    hf_token = config['huggingface']['api_key']

# Initialize Native Local HuggingFaceLLM with a model good for code/SQL
print("Loading model locally... This may take a moment.")
llm = HuggingFaceLLM(
    model_name="Salesforce/codegen-350M-mono",  # Good for code generation, no auth needed
    tokenizer_name="Salesforce/codegen-350M-mono",
    context_window=2048,
    max_new_tokens=256,
    generate_kwargs={"temperature": 0.1, "do_sample": False},
    device_map="auto", # Should detect mps on Mac
)

# Set global settings (optional, but good practice)
Settings.llm = llm
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 4. Create Query Engine Tool
query_engine = NLSQLTableQueryEngine(
    sql_database,
    tables=[table_name],
    llm=llm
)

sql_tool = QueryEngineTool(
    query_engine=query_engine,
    metadata=ToolMetadata(
        name="sql_db",
        description=f"Useful for translating a natural language query into a SQL query over a table named {table_name} containing financial/stock data."
    )
)

# 5. Skip Agent for now - use query engine directly
print(f"Query engine initialized with CodeGen and Postgres table '{table_name}'.")
print("Ask a question (or type 'exit' to quit):")

while True:
    try:
        user_input = input("\nUser: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break
        
        response = query_engine.query(user_input)
        print(f"Response: {response}")
        
    except KeyboardInterrupt:
        print("\nExiting...")
        break
    except Exception as e:
        print(f"An error occurred: {e}")
