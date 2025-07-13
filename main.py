import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import pandas_ta as ta
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode

st.set_page_config(layout="wide")
st.title('📈 Stock Data Analysis')
st.markdown('🔗 [Download Nasdaq Screener CSV](https://www.nasdaq.com/market-activity/stocks/screener)')

file = st.file_uploader("Upload your CSV file", type="csv")

if file is not None:
    data = pd.read_csv(file)

    # Clean Data
    data = data[data['Country'] != 'Israel']

    data['Last Sale'] = data['Last Sale'].astype(str)
    data[['Last Sale']] = data[['Last Sale']].map(lambda x: x.lstrip('$').rstrip(' '))
    data['Last Sale'] = pd.to_numeric(data['Last Sale'], errors='coerce')

    data['% Change'] = data['% Change'].astype(str)
    data['% Change'] = data['% Change'].map(lambda x: x.rstrip('%').lstrip(' '))
    data['% Change'] = pd.to_numeric(data['% Change'], errors='coerce')

    df = data[['Name', 'Symbol', 'Last Sale', '% Change', 'Net Change', 'Market Cap', 'Volume', 'Sector', 'Industry', 'Country','IPO Year']]
    df = df.dropna(subset=['% Change', 'Last Sale'])
    df.loc[:, ['Last Sale', '% Change']] = df.loc[:, ['Last Sale', '% Change']].round(2)
    df = df.drop(columns=['% Change', 'Net Change'], errors='ignore')
   # df2 = df # Initialize df2 as an empty DataFrame
    
    if 'filtered_data' not in st.session_state:
        st.session_state.filtered_data = pd.DataFrame()
    

    #if 'selected_rows' not in st.session_state:
        #st.session_state.selected_rows = []

    st.subheader("📊 Stock Screener Table")
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination()
    gb.configure_default_column(editable=True, filter=True)
    gb.configure_selection(selection_mode='multiple', use_checkbox=True)
    grid_options = gb.build()

    

    grid_response = AgGrid(df, gridOptions=grid_options, update_mode=GridUpdateMode.SELECTION_CHANGED, height=300)
    selected_rows = grid_response['selected_rows']

    if   selected_rows is not None and len(selected_rows) > 0:
        filtered_data = (selected_rows)
        st.session_state.filtered_data = filtered_data

    if not st.session_state.filtered_data.empty:
        st.subheader("Filtered Data")
        st.write(st.session_state.filtered_data)
    #else:
       # st.error('No data to display. Please check your filters')

    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = []

    st.title("Select Row and Append to List")
    if not st.session_state.filtered_data.empty:
        selected_index = st.selectbox("Select a row", st.session_state.filtered_data.index, format_func=lambda x: st.session_state.filtered_data.loc[x, 'Symbol'])
        if st.button("Append Row to List"):
            selected_row = st.session_state.filtered_data.loc[selected_index]
            st.session_state.selected_rows.append(selected_row)
            st.success(f"Row {selected_row['Symbol']} appended!")

    if len(st.session_state.selected_rows) > 0:
        selected_df = pd.DataFrame(st.session_state.selected_rows)
        st.write("**Click on Nasdaq or Yahoo Finance below for more information or Yaqeen to investigate the Halal status:**")

        link_template = """
        <table style="width:100%;border-collapse: collapse;">
          <thead>
             <tr style="background-color: #f2f2f2;">
                 <th style="text-align: left; padding: 8px;">Stock Symbol</th>
                 <th style="text-align: left; padding: 8px;">Nasdaq</th>
                 <th style="text-align: left; padding: 8px;">Yaqeen</th>
                 <th style="text-align: left; padding: 8px;">Yahoo Finance</th>
            </tr>
        </thead>
        <tbody>
    """
    
        for symbol in selected_df['Symbol'].unique():
          link_template += f"""
          <tr>
            <td style="padding: 8px;"><strong>{symbol}</strong></td>
            <td style="padding: 8px;"><a href="https://www.nasdaq.com/market-activity/stocks/{symbol}" target="_blank">📈 Nasdaq</a></td>
            <td style="padding: 8px;"><a href="https://yaaqen.com/stocks/{symbol}" target="_blank">🔍 Yaqeen</a></td>
            <td style="padding: 8px;"><a href="https://finance.yahoo.com/quote/{symbol}" target="_blank">💼 Yahoo Finance</a></td>
           </tr>
        """
    
        link_template += "</tbody></table>"

        st.markdown(link_template, unsafe_allow_html=True)

        st.dataframe(selected_df)

        st.sidebar.title('Please Enter the Symbol here:')
        ticker_symbol = st.sidebar.selectbox('Select the Ticker', selected_df['Symbol'])
        
        st.title("Remove Row from Selected List")
        remove_index = st.selectbox("Select a row to remove", selected_df.index, format_func=lambda x: selected_df.loc[x, 'Symbol'])
        if st.button("Remove Row from List"):
            symbol_to_remove = selected_df.loc[remove_index, 'Symbol']
            st.session_state.selected_rows = [row for row in st.session_state.selected_rows if row['Symbol'] not in symbol_to_remove]

            st.success(f"Row {symbol_to_remove} removed!")
    else:
        st.sidebar.title('Please Enter the Symbol here:')
        ticker_symbol = st.sidebar.text_input('Enter the Ticker')

    #Start_Date = st.sidebar.date_input('Start Date', value=None)
    #End_Date = st.sidebar.date_input('End Date', value=None)
    #if ticker_symbol and Start_Date and End_Date:

    start_date = st.sidebar.date_input("Start Date", key="start_date_sidebar")
    end_date = st.sidebar.date_input("End Date", key="end_date_sidebar")

    if ticker_symbol and start_date and end_date:
        ticker = yf.Ticker(ticker_symbol)
        try:
            stock_data = ticker.history(start=start_date, end=end_date)
        except Exception as e:
            st.error(f"Failed to fetch historical data: {e}")
            stock_data = pd.DataFrame()

        tabs = st.tabs(["📄 Info", "📈 Historical", "📉 Charts", "📰 News", "💰 Actions", "📊 Financials"])

        # -------- INFO TAB --------
        with tabs[0]:
            st.subheader(f"{ticker_symbol} Info")
            try:
                info = ticker.info
                st.write(ticker.info.get('website','N/A'))
                st.write(f"**Industry**: {info.get('industry', 'N/A')}")
                st.write(f"**Sector**: {info.get('sector', 'N/A')}")
                st.write(f"**Employees**: {info.get('fullTimeEmployees', 'N/A')}")
                st.write(f"**Summary**: {info.get('longBusinessSummary', 'N/A')}")

                price_df = pd.DataFrame.from_dict({
                    "Target High Price": [info.get('targetHighPrice')],
                    "Target Low Price": [info.get('targetLowPrice')],
                    "Target Mean Price": [info.get('targetMeanPrice')],
                    "52 Week High": [info.get('fiftyTwoWeekHigh')],
                    "52 Week Low": [info.get('fiftyTwoWeekLow')],
                    "Book Value": [info.get('bookValue')],
                    "Total Revenue": [info.get('totalRevenue')],
                })
                st.dataframe(price_df)

                ratio_df = pd.DataFrame.from_dict({
                    "EPS": [info.get('trailingEps')],
                    "Profit Margin": [info.get('profitMargins')],
                    "P/B": [info.get('priceToBook')],
                    "PEG Ratio": [info.get('pegRatio')],
                    "Beta": [info.get('beta')],
                    "EBITDA Margin": [info.get('ebitdaMargins')],
                })
                st.dataframe(ratio_df)
            except Exception as e:
                st.warning(f"Could not load stock info: {e}")

        # -------- HISTORICAL TAB --------
        with tabs[1]:
            if not stock_data.empty:
                st.subheader("Historical Data")
                st.dataframe(stock_data.style.format(precision=2).background_gradient(cmap="Blues"))
            else:
                st.warning("No historical data available.")

        # -------- CHARTS TAB --------
        with tabs[2]:
            if not stock_data.empty:
                st.subheader("📉 Price & Volume Chart")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], name='Close', line=dict(color='blue')))
                fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Volume',
                                     marker=dict(color='orange'), yaxis='y2', opacity=0.5))
                fig.update_layout(
                    title=f"{ticker_symbol} Price & Volume",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    yaxis2=dict(title='Volume', overlaying='y', side='right', showgrid=False),
                    height=500
                )
                st.plotly_chart(fig)

                st.subheader("📊 RSI Indicator")
                rsi = ta.rsi(stock_data['Close'])
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(x=stock_data.index, y=rsi, name='RSI', line=dict(color='green')))
                rsi_fig.add_hline(y=70, line=dict(color='red', dash='dash'))
                rsi_fig.add_hline(y=30, line=dict(color='blue', dash='dash'))
                rsi_fig.update_layout(title="RSI (Relative Strength Index)", height=300)
                st.plotly_chart(rsi_fig)

                st.subheader("📉 Candlestick Chart")
                if not stock_data.empty:
                    MA = st.number_input('Enter MA',None)
                    stock_data[MA] = stock_data['Close'].rolling(window=5).mean()

                    candlestick_fig = go.Figure(data=[go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['Open'],
                        high=stock_data['High'],
                        low=stock_data['Low'],
                        close=stock_data['Close'],
                        increasing_line_color='green',  # Color for bullish candles
                        decreasing_line_color='red'     # Color for bearish candles
                    )])

                    # Add the 100-day Moving Average (MA) line
                    candlestick_fig.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data[MA],
                    mode='lines',
                    name= (f'{MA}-Day MA'),
                    line=dict(color='orange', width=2)
            ))

                    # Add volume bars
                    candlestick_fig.add_trace(go.Bar(
                        x=stock_data.index,
                        y=stock_data['Volume'],
                        marker_color='blue',
                        opacity=0.3,
                        yaxis='y2',  # Plot volume on secondary y-axis
                        name='Volume'
                    ))

                    # Update layout for the chart
                    candlestick_fig.update_layout(
                        title=f'{ticker_symbol} Candlestick Chart',
                        xaxis_title='Date',
                        yaxis_title='Price',
                        yaxis=dict(
                            title='Price',
                            side='right'  # Position the price axis on the right
                        ),
                        yaxis2=dict(
                            title='Volume',
                            overlaying='y',
                            side='left',  # Position the volume axis on the left
                            showgrid=False,
                            range=[0, max(stock_data['Volume']) * 5] if not stock_data['Volume'].empty else [0, 1]
                        ),
                        xaxis_rangeslider_visible=False,  # Hide the default range slider
                        width=900,  # Set the width of the chart
                        height=500,  # Set the height of the chart
                        template='plotly_dark',  # Use dark template for better visuals
                    )

                    # Plot the candlestick chart in Streamlit
                    st.plotly_chart(candlestick_fig)
                else:
                    st.warning("No chart data to display.")

        # -------- NEWS TAB --------
        with tabs[3]:
            st.subheader("📰 News")
            try:
                news = yf.Ticker(ticker_symbol).news[:5]
                for item in news:
                    st.markdown(f"### {item['title']}")
                    st.write(f"Source: {item['publisher']}")
                    st.write(f"[Read more]({item['link']})")
            except Exception:
                st.write("No news available.")

        # -------- ACTIONS TAB --------
        with tabs[4]:
            st.subheader("💰 Stock Actions")
            try:
                st.dataframe(ticker.actions)
            except Exception:
                st.write("No actions data available.")

        # -------- FINANCIALS TAB --------
        with tabs[5]:
            st.subheader("📊 Financial Statements")
            try:
                st.write("**Income Statement**")
                st.dataframe(ticker.financials)

                st.write("**Balance Sheet**")
                st.dataframe(ticker.balance_sheet)

                st.write("**Cashflow Statement**")
                st.dataframe(ticker.cashflow)

                st.write("**Institutional Holders**")
                holders = ticker.institutional_holders
                if holders is not None and not holders.empty:
                    st.dataframe(holders)
                else:
                    st.write("No institutional holder data available.")
            except Exception as e:
                st.warning(f"Some financial data could not be loaded: {e}")
        
        
        # Collect Stocks Button
        if st.sidebar.button("Collect Stocks"):
            collected_stocks = st.session_state.selected_rows
            if collected_stocks:
                # Extract only Symbol and Name
                simplified_stocks = [{"Symbol": row["Symbol"], "Name": row["Name"]} for row in collected_stocks]
                
                # Convert to DataFrame
                df_simplified = pd.DataFrame(simplified_stocks)
                
                # Save DataFrame to Excel in the current directory
                output_path = 'collected_stocks.xlsx'
                df_simplified.to_excel(output_path, index=False)
                st.success(f"Collected stocks saved to {output_path}")
            else:
                st.warning('No stocks selected to collect')
