import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import configparser
import os
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Stock Data Explorer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load database configuration
@st.cache_resource
def init_database():
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini')
    config.read(config_path)
    
    user = config['postgres']['user']
    password = config['postgres']['password']
    table_name = config['postgres']['table_name']
    db_name = "postgres"
    
    engine = create_engine(f"postgresql+psycopg2://{user}:{password}@localhost/{db_name}")
    return engine, table_name

# Database query functions
@st.cache_data
def get_stock_list(_engine, table_name):
    """Get list of all stocks"""
    query = f"SELECT DISTINCT name FROM {table_name} ORDER BY name"
    with _engine.connect() as conn:
        result = conn.execute(text(query))
        return [row[0] for row in result.fetchall()]

@st.cache_data
def get_stock_data(_engine, table_name, stock_symbol=None, start_date=None, end_date=None):
    """Get stock data with optional filters"""
    query = f"SELECT * FROM {table_name}"
    conditions = []
    
    if stock_symbol:
        conditions.append(f"name = '{stock_symbol}'")
    if start_date:
        conditions.append(f"date >= '{start_date}'")
    if end_date:
        conditions.append(f"date <= '{end_date}'")
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY date DESC"
    
    with _engine.connect() as conn:
        return pd.read_sql(query, conn)

@st.cache_data
def natural_language_to_sql(question, table_name, stock_list):
    """Convert natural language questions to SQL queries"""
    question = question.lower()
    
    # Stock-specific queries
    stock_mentioned = None
    for stock in stock_list:
        if stock.lower() in question:
            stock_mentioned = stock
            break
    
    # Price-related queries
    if "highest" in question and ("price" in question or "close" in question):
        if stock_mentioned:
            return f"SELECT date, close FROM {table_name} WHERE name = '{stock_mentioned}' ORDER BY close DESC LIMIT 10", f"Highest closing prices for {stock_mentioned}"
        else:
            return f"SELECT name, date, close FROM {table_name} ORDER BY close DESC LIMIT 10", "Highest closing prices across all stocks"
    
    if "lowest" in question and ("price" in question or "close" in question):
        if stock_mentioned:
            return f"SELECT date, close FROM {table_name} WHERE name = '{stock_mentioned}' ORDER BY close ASC LIMIT 10", f"Lowest closing prices for {stock_mentioned}"
        else:
            return f"SELECT name, date, close FROM {table_name} ORDER BY close ASC LIMIT 10", "Lowest closing prices across all stocks"
    
    if "average" in question and ("price" in question or "close" in question):
        if stock_mentioned:
            return f"SELECT AVG(close) as avg_price FROM {table_name} WHERE name = '{stock_mentioned}'", f"Average closing price for {stock_mentioned}"
        else:
            return f"SELECT name, AVG(close) as avg_price FROM {table_name} GROUP BY name ORDER BY avg_price DESC", "Average closing prices by stock"
    
    # Volume-related queries
    if "volume" in question:
        if "highest" in question or "most" in question:
            if stock_mentioned:
                return f"SELECT date, volume FROM {table_name} WHERE name = '{stock_mentioned}' ORDER BY volume DESC LIMIT 10", f"Highest volume days for {stock_mentioned}"
            else:
                return f"SELECT name, date, volume FROM {table_name} ORDER BY volume DESC LIMIT 10", "Highest volume trading days"
        
        if "average" in question:
            if stock_mentioned:
                return f"SELECT AVG(volume) as avg_volume FROM {table_name} WHERE name = '{stock_mentioned}'", f"Average volume for {stock_mentioned}"
            else:
                return f"SELECT name, AVG(volume) as avg_volume FROM {table_name} GROUP BY name ORDER BY avg_volume DESC", "Average volume by stock"
    
    # Date-related queries
    if "recent" in question or "latest" in question:
        if stock_mentioned:
            return f"SELECT * FROM {table_name} WHERE name = '{stock_mentioned}' ORDER BY date DESC LIMIT 10", f"Recent data for {stock_mentioned}"
        else:
            return f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 20", "Most recent stock data"
    
    if "2018" in question:
        if stock_mentioned:
            return f"SELECT * FROM {table_name} WHERE name = '{stock_mentioned}' AND date >= '2018-01-01' AND date <= '2018-12-31' ORDER BY date", f"{stock_mentioned} data for 2018"
        else:
            return f"SELECT name, AVG(close) as avg_price FROM {table_name} WHERE date >= '2018-01-01' AND date <= '2018-12-31' GROUP BY name ORDER BY avg_price DESC LIMIT 10", "Top stocks by average price in 2018"
    
    if "2017" in question:
        if stock_mentioned:
            return f"SELECT * FROM {table_name} WHERE name = '{stock_mentioned}' AND date >= '2017-01-01' AND date <= '2017-12-31' ORDER BY date", f"{stock_mentioned} data for 2017"
        else:
            return f"SELECT name, AVG(close) as avg_price FROM {table_name} WHERE date >= '2017-01-01' AND date <= '2017-12-31' GROUP BY name ORDER BY avg_price DESC LIMIT 10", "Top stocks by average price in 2017"
    
    # Performance queries
    if "best" in question or "top" in question:
        if "performing" in question or "performance" in question:
            return f"SELECT name, AVG(close) as avg_price, MAX(high) as max_high FROM {table_name} GROUP BY name ORDER BY avg_price DESC LIMIT 10", "Best performing stocks by average price"
    
    if "worst" in question or "bottom" in question:
        if "performing" in question or "performance" in question:
            return f"SELECT name, AVG(close) as avg_price, MIN(low) as min_low FROM {table_name} GROUP BY name ORDER BY avg_price ASC LIMIT 10", "Worst performing stocks by average price"
    
    # Comparison queries
    if "compare" in question:
        stocks_in_question = [stock for stock in stock_list if stock.lower() in question]
        if len(stocks_in_question) >= 2:
            stock_filter = "', '".join(stocks_in_question)
            return f"SELECT name, AVG(close) as avg_price, AVG(volume) as avg_volume FROM {table_name} WHERE name IN ('{stock_filter}') GROUP BY name", f"Comparison of {', '.join(stocks_in_question)}"
    
    # General queries
    if "how many" in question and "stock" in question:
        return f"SELECT COUNT(DISTINCT name) as total_stocks FROM {table_name}", "Total number of stocks in database"
    
    if "date range" in question or "time period" in question:
        return f"SELECT MIN(date) as earliest_date, MAX(date) as latest_date FROM {table_name}", "Date range of available data"
    
    # Default fallback
    if stock_mentioned:
        return f"SELECT * FROM {table_name} WHERE name = '{stock_mentioned}' ORDER BY date DESC LIMIT 10", f"Recent data for {stock_mentioned}"
    else:
        return f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 10", "Recent stock data (try asking about specific stocks, prices, volumes, or dates)"

@st.cache_data
def get_question_suggestions():
    """Get sample questions users can ask"""
    return [
        "What are the highest closing prices for AAPL?",
        "Show me the average price for all stocks",
        "Which stock had the highest volume?",
        "What are the recent prices for MSFT?",
        "Compare AAPL and GOOGL performance",
        "Show me the best performing stocks",
        "What was the lowest price for TSLA?",
        "How many stocks are in the database?",
        "Show me 2018 data for AMZN",
        "Which stocks had the highest average volume?"
    ]

@st.cache_data
def get_summary_stats(_engine, table_name):
    """Get summary statistics"""
    query = f"""
    SELECT 
        name,
        COUNT(*) as total_records,
        MIN(date) as earliest_date,
        MAX(date) as latest_date,
        AVG(close) as avg_close_price,
        MAX(high) as max_high,
        MIN(low) as min_low,
        AVG(volume) as avg_volume
    FROM {table_name}
    GROUP BY name
    ORDER BY avg_close_price DESC
    """
    with _engine.connect() as conn:
        return pd.read_sql(query, conn)

# Initialize database
engine, table_name = init_database()

# App title
st.title("📈 Stock Data Explorer")
st.markdown("Interactive dashboard for S&P 500 stock data analysis")

# Sidebar
st.sidebar.header("🔧 Controls")

# Get stock list
stock_list = get_stock_list(engine, table_name)
st.sidebar.success(f"Connected to database with {len(stock_list)} stocks")

# Stock selection
selected_stocks = st.sidebar.multiselect(
    "Select Stock(s)",
    options=stock_list,
    default=stock_list[:3] if len(stock_list) >= 3 else stock_list,
    help="Choose one or more stocks to analyze"
)

# Date range selection
st.sidebar.subheader("📅 Date Range")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=datetime(2017, 1, 1))
with col2:
    end_date = st.date_input("End Date", value=datetime(2018, 12, 31))

# Analysis type
analysis_type = st.sidebar.selectbox(
    "Analysis Type",
    ["Price Analysis", "Volume Analysis", "Summary Statistics", "Custom Query", "Ask Questions"]
)

# Main content
if selected_stocks:
    # Get data for selected stocks
    if len(selected_stocks) == 1:
        df = get_stock_data(engine, table_name, selected_stocks[0], start_date, end_date)
    else:
        # Get data for multiple stocks
        dfs = []
        for stock in selected_stocks:
            stock_df = get_stock_data(engine, table_name, stock, start_date, end_date)
            dfs.append(stock_df)
        df = pd.concat(dfs, ignore_index=True)
    
    if not df.empty:
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        if analysis_type == "Price Analysis":
            st.header("💰 Price Analysis")
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Avg Close Price", f"${df['close'].mean():.2f}")
            with col3:
                st.metric("Highest Price", f"${df['high'].max():.2f}")
            with col4:
                st.metric("Lowest Price", f"${df['low'].min():.2f}")
            
            # Price chart
            fig = go.Figure()
            
            for stock in selected_stocks:
                stock_data = df[df['name'] == stock].sort_values('date')
                fig.add_trace(go.Scatter(
                    x=stock_data['date'],
                    y=stock_data['close'],
                    mode='lines',
                    name=f"{stock} Close Price",
                    line=dict(width=2)
                ))
            
            fig.update_layout(
                title="Stock Price Over Time",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Candlestick chart for single stock
            if len(selected_stocks) == 1:
                st.subheader(f"📊 Candlestick Chart - {selected_stocks[0]}")
                stock_data = df.sort_values('date')
                
                fig_candle = go.Figure(data=go.Candlestick(
                    x=stock_data['date'],
                    open=stock_data['open'],
                    high=stock_data['high'],
                    low=stock_data['low'],
                    close=stock_data['close'],
                    name=selected_stocks[0]
                ))
                
                fig_candle.update_layout(
                    title=f"{selected_stocks[0]} Candlestick Chart",
                    xaxis_title="Date",
                    yaxis_title="Price ($)",
                    height=500
                )
                
                st.plotly_chart(fig_candle, use_container_width=True)
        
        elif analysis_type == "Volume Analysis":
            st.header("📊 Volume Analysis")
            
            # Volume metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Volume", f"{df['volume'].mean():,.0f}")
            with col2:
                st.metric("Max Volume", f"{df['volume'].max():,.0f}")
            with col3:
                st.metric("Min Volume", f"{df['volume'].min():,.0f}")
            
            # Volume chart
            fig = go.Figure()
            
            for stock in selected_stocks:
                stock_data = df[df['name'] == stock].sort_values('date')
                fig.add_trace(go.Scatter(
                    x=stock_data['date'],
                    y=stock_data['volume'],
                    mode='lines',
                    name=f"{stock} Volume",
                    fill='tonexty' if stock != selected_stocks[0] else 'tozeroy'
                ))
            
            fig.update_layout(
                title="Trading Volume Over Time",
                xaxis_title="Date",
                yaxis_title="Volume",
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume vs Price correlation
            if len(selected_stocks) == 1:
                st.subheader("Volume vs Price Correlation")
                fig_scatter = px.scatter(
                    df, x='volume', y='close',
                    title=f"{selected_stocks[0]} - Volume vs Close Price",
                    labels={'volume': 'Trading Volume', 'close': 'Close Price ($)'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
        
        elif analysis_type == "Summary Statistics":
            st.header("📈 Summary Statistics")
            
            # Get summary stats for all stocks
            summary_df = get_summary_stats(engine, table_name)
            
            # Display summary table
            st.subheader("Stock Summary")
            st.dataframe(
                summary_df.style.format({
                    'avg_close_price': '${:.2f}',
                    'max_high': '${:.2f}',
                    'min_low': '${:.2f}',
                    'avg_volume': '{:,.0f}'
                }),
                use_container_width=True
            )
            
            # Top performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top 10 by Average Price")
                top_price = summary_df.head(10)
                fig_bar = px.bar(
                    top_price, x='name', y='avg_close_price',
                    title="Average Close Price by Stock"
                )
                fig_bar.update_layout(xaxis_title="Stock", yaxis_title="Avg Price ($)")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                st.subheader("📊 Top 10 by Volume")
                top_volume = summary_df.nlargest(10, 'avg_volume')
                fig_bar2 = px.bar(
                    top_volume, x='name', y='avg_volume',
                    title="Average Volume by Stock"
                )
                fig_bar2.update_layout(xaxis_title="Stock", yaxis_title="Avg Volume")
                st.plotly_chart(fig_bar2, use_container_width=True)
        
        elif analysis_type == "Custom Query":
            st.header("🔍 Custom SQL Query")
            
            # Predefined queries
            st.subheader("Quick Queries")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Top 10 Highest Prices"):
                    query = f"SELECT name, date, high FROM {table_name} ORDER BY high DESC LIMIT 10"
                    result = pd.read_sql(query, engine)
                    st.dataframe(result)
            
            with col2:
                if st.button("Most Active Trading Days"):
                    query = f"SELECT name, date, volume FROM {table_name} ORDER BY volume DESC LIMIT 10"
                    result = pd.read_sql(query, engine)
                    st.dataframe(result)
            
            with col3:
                if st.button("Recent Data"):
                    query = f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 20"
                    result = pd.read_sql(query, engine)
                    st.dataframe(result)
            
            # Custom query input
            st.subheader("Write Your Own Query")
            custom_query = st.text_area(
                "SQL Query",
                value=f"SELECT * FROM {table_name} LIMIT 10",
                height=100,
                help="Write your SQL query here. Be careful with large result sets!"
            )
            
            if st.button("Execute Query"):
                try:
                    with engine.connect() as conn:
                        result = pd.read_sql(custom_query, conn)
                        st.success(f"Query executed successfully! {len(result)} rows returned.")
                        st.dataframe(result)
                except Exception as e:
                    st.error(f"Query error: {e}")
        
        elif analysis_type == "Ask Questions":
            st.header("🤖 Ask Questions About Your Data")
            st.markdown("Ask questions in plain English and get SQL-powered answers!")
            
            # Sample questions
            st.subheader("💡 Try These Sample Questions:")
            sample_questions = get_question_suggestions()
            
            # Display sample questions in columns
            col1, col2 = st.columns(2)
            with col1:
                for i, question in enumerate(sample_questions[:5]):
                    if st.button(f"📝 {question}", key=f"sample_{i}"):
                        st.session_state.user_question = question
            
            with col2:
                for i, question in enumerate(sample_questions[5:]):
                    if st.button(f"📝 {question}", key=f"sample_{i+5}"):
                        st.session_state.user_question = question
            
            # Question input
            st.subheader("❓ Ask Your Question:")
            user_question = st.text_input(
                "Type your question here:",
                value=st.session_state.get('user_question', ''),
                placeholder="e.g., What are the highest closing prices for AAPL?",
                help="Ask about stock prices, volumes, dates, comparisons, or performance"
            )
            
            # Clear the session state after using it
            if 'user_question' in st.session_state:
                del st.session_state.user_question
            
            if user_question:
                with st.spinner("🔍 Analyzing your question..."):
                    try:
                        # Convert question to SQL
                        sql_query, description = natural_language_to_sql(user_question, table_name, stock_list)
                        
                        # Show the generated SQL
                        with st.expander("🔧 Generated SQL Query"):
                            st.code(sql_query, language="sql")
                        
                        # Execute the query
                        with engine.connect() as conn:
                            result_df = pd.read_sql(sql_query, conn)
                        
                        # Display results
                        st.success(f"✅ {description}")
                        
                        if len(result_df) > 0:
                            # Show metrics if it's a single value result
                            if len(result_df) == 1 and len(result_df.columns) == 1:
                                col_name = result_df.columns[0]
                                value = result_df.iloc[0, 0]
                                if 'price' in col_name.lower():
                                    st.metric(description, f"${value:.2f}")
                                elif 'volume' in col_name.lower():
                                    st.metric(description, f"{value:,.0f}")
                                elif 'count' in col_name.lower():
                                    st.metric(description, f"{value:,}")
                                else:
                                    st.metric(description, str(value))
                            else:
                                # Show as table
                                st.dataframe(
                                    result_df.style.format({
                                        col: '${:.2f}' if 'price' in col.lower() or 'close' in col.lower() or 'open' in col.lower() or 'high' in col.lower() or 'low' in col.lower()
                                        else '{:,.0f}' if 'volume' in col.lower()
                                        else '{}'
                                        for col in result_df.columns
                                    }),
                                    use_container_width=True
                                )
                                
                                # Create visualization if appropriate
                                if len(result_df) > 1:
                                    # Price chart
                                    if 'close' in result_df.columns and 'date' in result_df.columns:
                                        if 'name' in result_df.columns:
                                            # Multiple stocks
                                            fig = px.line(
                                                result_df, x='date', y='close', color='name',
                                                title="Stock Prices Over Time"
                                            )
                                        else:
                                            # Single stock
                                            fig = px.line(
                                                result_df, x='date', y='close',
                                                title="Stock Price Over Time"
                                            )
                                        st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Bar chart for averages/comparisons
                                    elif 'name' in result_df.columns and any('avg' in col.lower() or 'price' in col.lower() for col in result_df.columns):
                                        price_col = next((col for col in result_df.columns if 'avg' in col.lower() or 'price' in col.lower()), None)
                                        if price_col:
                                            fig = px.bar(
                                                result_df, x='name', y=price_col,
                                                title=f"{price_col.replace('_', ' ').title()} by Stock"
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Volume chart
                                    elif 'volume' in result_df.columns and 'date' in result_df.columns:
                                        fig = px.line(
                                            result_df, x='date', y='volume',
                                            title="Trading Volume Over Time"
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                            
                            # Download option
                            csv = result_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Results",
                                data=csv,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("No results found for your question. Try rephrasing or asking about different stocks/dates.")
                    
                    except Exception as e:
                        st.error(f"❌ Error processing your question: {e}")
                        st.info("💡 Try asking simpler questions or check if the stock symbols are correct.")
            
            # Help section
            with st.expander("❓ How to Ask Questions"):
                st.markdown("""
                **Question Types You Can Ask:**
                
                🏷️ **Stock-specific questions:**
                - "What are the highest prices for AAPL?"
                - "Show me recent data for MSFT"
                - "What's the average volume for GOOGL?"
                
                📊 **Comparison questions:**
                - "Compare AAPL and MSFT performance"
                - "Which stock has higher average price?"
                
                📈 **Performance questions:**
                - "What are the best performing stocks?"
                - "Show me the highest volume days"
                - "Which stocks had the lowest prices?"
                
                📅 **Time-based questions:**
                - "Show me 2018 data for AMZN"
                - "What were prices in 2017?"
                - "Recent stock data"
                
                💡 **General questions:**
                - "How many stocks are in the database?"
                - "What's the date range of the data?"
                
                **Tips:**
                - Mention specific stock symbols (AAPL, MSFT, GOOGL, etc.)
                - Use words like "highest", "lowest", "average", "recent"
                - Specify years (2017, 2018) for time-based queries
                - Ask about "price", "volume", "performance"
                """)
        
        # Raw data section
        with st.expander("📋 View Raw Data"):
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"stock_data_{'-'.join(selected_stocks)}_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
    
    else:
        st.warning("No data found for the selected criteria.")

else:
    st.info("👈 Please select at least one stock from the sidebar to begin analysis.")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit 🎈 | Data from S&P 500 Stock Dataset")