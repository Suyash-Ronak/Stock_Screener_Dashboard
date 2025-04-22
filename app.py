import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

st.markdown(
    "<h1 style='text-align: center; color: #2e86de; font-family: Arial, sans-serif;'>📊 Stock Screener Dashboard</h1>",
    unsafe_allow_html=True)

sector_stocks = {
    "Oil & Gas": ["RELIANCE.NS", "ONGC.NS", "BPCL.NS", "GAIL.NS"],
    "IT": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS", "TECHM.NS"],
    "Banking": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS"],
    "Automobile": ["MARUTI.NS", "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS"],
    "FMCG": ["HINDUNILVR.NS", "ITC.NS", "BRITANNIA.NS", "NESTLEIND.NS"],
    "Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS"],
    "Infrastructure": ["LT.NS", "ADANIPORTS.NS", "ADANIENT.NS", "ULTRACEMCO.NS"],
    "Power": ["NTPC.NS", "POWERGRID.NS"],
    "Metals": ["TATASTEEL.NS", "JSWSTEEL.NS"],
    "Others": ["BHARTIARTL.NS", "ASIANPAINT.NS", "TITAN.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
               "HDFCLIFE.NS", "SHREECEM.NS", "COALINDIA.NS", "GRASIM.NS", "UPL.NS", "HDFCAMC.NS", "APOLLOHOSP.NS"]
}

# Create display names and API symbols mapping
api_symbols = sorted([stock for sector in sector_stocks.values() for stock in sector])
display_names = [symbol.replace(".NS", "") for symbol in api_symbols]
stock_mapping = dict(zip(display_names, api_symbols))

col1, col2 = st.columns(2)

with col1:
    selected_sector = st.selectbox("Select Market Sector", ["All Sectors"] + list(sector_stocks.keys()), index=0)

with col2:
    if selected_sector == "All Sectors":
        selected_display = st.multiselect(
            "Or Select Individual Stocks (Max 10)",
            display_names,
            default=[display_names[0]],
            max_selections=10
        )
        selected_stocks = [stock_mapping[name] for name in selected_display]
    else:
        sector_display = [s.replace(".NS", "") for s in sector_stocks[selected_sector]]
        st.multiselect(
            "Or Select Individual Stocks (Max 10)",
            sector_display,
            default=sector_display[:1],
            disabled=True
        )
        selected_stocks = sector_stocks[selected_sector]


def format_market_cap(value):
    if value == 'N/A': return value
    value = float(value)
    if value >= 1e12:
        return f"\u20b9{value / 1e12:.2f}T"
    elif value >= 1e9:
        return f"\u20b9{value / 1e9:.2f}B"
    return f"\u20b9{value:,.2f}"


if st.button("Show Stock Data"):
    if not selected_stocks:
        st.warning("Please select at least one stock.")
    else:
        try:
            all_data = {}
            for symbol in selected_stocks:
                stock = yf.Ticker(symbol)
                df = stock.history(period="1y")
                if df.empty:
                    st.error(f"No data available for {symbol}")
                    continue

                info = stock.info
                latest_price = df["Close"].iloc[-1]

                df["MA50"] = ta.trend.sma_indicator(df["Close"], window=50)
                df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
                macd = ta.trend.MACD(df["Close"])
                df["MACD"] = macd.macd()
                df["MACD_signal"] = macd.macd_signal()

                details = {
                    "Stock": symbol.replace(".NS", ""),
                    "Price (\u20b9)": latest_price,
                    "Market Cap": info.get('marketCap', 'N/A'),
                    "P/E": info.get('trailingPE', 'N/A'),
                    "Div Yield": info.get('dividendYield', 'N/A'),
                    "52W High (\u20b9)": info.get('fiftyTwoWeekHigh', 'N/A'),
                    "52W Low (\u20b9)": info.get('fiftyTwoWeekLow', 'N/A'),
                    "EPS": info.get('trailingEps', 'N/A'),
                }
                all_data[symbol] = {"details": details, "df": df}

            # Create DataFrame directly from details to avoid duplicate stock column
            df_table = pd.DataFrame([v["details"] for v in all_data.values()])

            # Format columns
            df_table["Price (\u20b9)"] = df_table["Price (\u20b9)"].apply(
                lambda x: f"\u20b9{x:,.2f}" if x != 'N/A' else 'N/A')
            df_table["Market Cap"] = df_table["Market Cap"].apply(format_market_cap)
            df_table["P/E"] = df_table["P/E"].apply(lambda x: f"{x:.2f}" if x != 'N/A' else 'N/A')
            df_table["Div Yield"] = df_table["Div Yield"].apply(lambda x: f"{x * 100:.2f}%" if x != 'N/A' else 'N/A')
            df_table["52W High (\u20b9)"] = df_table["52W High (\u20b9)"].apply(
                lambda x: f"\u20b9{x:,.2f}" if x != 'N/A' else 'N/A')
            df_table["52W Low (\u20b9)"] = df_table["52W Low (\u20b9)"].apply(
                lambda x: f"\u20b9{x:,.2f}" if x != 'N/A' else 'N/A')
            df_table["EPS"] = df_table["EPS"].apply(lambda x: f"{x:.2f}" if x != 'N/A' else 'N/A')
            df_table.reset_index(drop=True, inplace=True)
            df_table.insert(0, 'S.No', range(1, len(df_table) + 1))

            st.markdown("""
                <style>
                    thead tr th {
                        background-color: #2e86de !important;
                        color: white !important;
                        font-weight: bold !important;
                        text-align: center;
                    }
                    tbody td {
                        text-align: center;
                        font-family: 'Segoe UI', sans-serif;
                    }
                </style>
            """, unsafe_allow_html=True)

            st.dataframe(df_table, use_container_width=True,hide_index=True)


            def plot_unified_chart(data, title):
                fig = go.Figure()
                for col in data.columns:
                    fig.add_trace(
                        go.Scatter(x=data.index, y=data[col], mode='lines', name=col, hovertemplate='%{y:.2f}'))
                fig.update_layout(title=title, hovermode='x unified', xaxis_title='Date', yaxis_title='Value')
                st.plotly_chart(fig, use_container_width=True)


            if len(selected_stocks) > 1:
                indicators = {"Close": {}, "MA50": {}, "RSI": {}, "MACD": {}, "MACD_signal": {}}
                for symbol in all_data.keys():
                    df = all_data[symbol]["df"]
                    clean_name = symbol.replace(".NS", "")
                    for ind in indicators:
                        indicators[ind][clean_name] = df[ind]

                for ind, data in indicators.items():
                    plot_unified_chart(pd.DataFrame(data), f"{ind} Comparison")
            else:
                symbol = selected_stocks[0]
                df = all_data[symbol]["df"]
                for label, cols in {
                    "Price with 50-day MA": ["Close", "MA50"],
                    "RSI (14-day)": ["RSI"],
                    "MACD with Signal Line": ["MACD", "MACD_signal"]
                }.items():
                    plot_unified_chart(df[cols], f"{symbol.replace('.NS', '')} {label}")

        except Exception as e:
            st.error(f"Error fetching data: {e}")

st.write("Note: Prices in INR. 'N/A' indicates unavailable data. Charts show 1-year data with technical indicators.")

