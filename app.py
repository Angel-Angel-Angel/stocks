import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

st.set_page_config(page_title="Public Stock Comparison Dashboard", page_icon="📈", layout="wide")

st.title("📈 Public Stock Comparison Dashboard")
st.caption("Interactive comparison of publicly traded companies using the latest available daily market data.")

DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN"]
COMPANY_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA",
    "GOOGL": "Alphabet (Google)", "AMZN": "Amazon", "META": "Meta",
    "TSLA": "Tesla", "JPM": "JPMorgan Chase", "WMT": "Walmart",
    "NFLX": "Netflix", "AMD": "AMD", "ORCL": "Oracle"
}

with st.sidebar:
    st.header("Dashboard filters")
    tickers = st.multiselect(
        "Companies",
        options=list(COMPANY_NAMES.keys()),
        default=DEFAULT_TICKERS,
        format_func=lambda t: f"{t} — {COMPANY_NAMES[t]}",
        help="All charts update using this shared company selection."
    )
    today = date.today()
    start_default = today - timedelta(days=365 * 3)
    date_range = st.date_input(
        "Date range",
        value=(start_default, today),
        min_value=date(2000, 1, 1),
        max_value=today,
        help="The end date is inclusive in the dashboard."
    )
    st.caption("Data source: Yahoo Finance via yfinance. Prices may be delayed and are not investment advice.")

if len(tickers) < 2:
    st.warning("Select at least two companies to compare.")
    st.stop()

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Choose both a start date and an end date.")
    st.stop()

start_date, end_date = date_range
if start_date >= end_date:
    st.error("The start date must be earlier than the end date.")
    st.stop()

@st.cache_data(ttl=900, show_spinner=False)
def load_stock_data(symbols, start, end):
    # yfinance's end date is exclusive, so add one day to include the user's selected end date.
    raw = yf.download(
        tickers=list(symbols),
        start=start.isoformat(),
        end=(end + timedelta(days=1)).isoformat(),
        auto_adjust=True,
        group_by="column",
        progress=False,
        threads=True
    )
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"].copy()
        volume = raw["Volume"].copy() if "Volume" in raw.columns.get_level_values(0) else pd.DataFrame()
    else:
        # yfinance may return a flat column layout for a single ticker.
        ticker = list(symbols)[0]
        close = raw[["Close"]].rename(columns={"Close": ticker})
        volume = raw[["Volume"]].rename(columns={"Volume": ticker}) if "Volume" in raw else pd.DataFrame()

    if isinstance(close, pd.Series):
        close = close.to_frame(name=list(symbols)[0])
    if isinstance(volume, pd.Series):
        volume = volume.to_frame(name=list(symbols)[0])

    close = close.dropna(how="all")
    if not volume.empty:
        volume = volume.reindex(close.index)
    return close, volume, raw

with st.spinner("Loading the latest available stock data…"):
    close, volume, _ = load_stock_data(tuple(tickers), start_date, end_date)

if close.empty:
    st.error("No stock data was returned. Try a different date range or refresh the page.")
    st.stop()

# Keep only selected symbols that returned data.
available = [t for t in tickers if t in close.columns and close[t].notna().any()]
close = close[available].dropna(how="all")
if len(available) < 2:
    st.error("Fewer than two selected companies returned usable data. Change the selection or date range.")
    st.stop()
if not volume.empty:
    volume = volume[[t for t in available if t in volume.columns]]

labels = {t: f"{t} — {COMPANY_NAMES.get(t, t)}" for t in available}
close = close.rename(columns=labels)
if not volume.empty:
    volume = volume.rename(columns=labels)

# All charts use the same filtered company set and date range.
returns = close.pct_change().dropna(how="all")
indexed = close.div(close.ffill().iloc[0]).mul(100)
rolling_vol = returns.rolling(30, min_periods=15).std() * np.sqrt(252) * 100
drawdown = close.div(close.cummax()).sub(1) * 100

st.markdown(
    f"**Period shown:** {close.index.min().date()} to {close.index.max().date()}  ·  "
    f"**Companies with data:** {', '.join(available)}  ·  "
    f"**Refresh cadence:** cached for 15 minutes"
)

# Dynamic observations from the selected period.
total_return = (close.iloc[-1] / close.iloc[0] - 1) * 100
best_ticker = total_return.idxmax()
worst_ticker = total_return.idxmin()
best_return = total_return.max()
worst_return = total_return.min()
vol_last = rolling_vol.ffill().iloc[-1].dropna() if not rolling_vol.empty else pd.Series(dtype=float)
most_volatile = vol_last.idxmax() if not vol_last.empty else None

st.subheader("Key differences in the selected period")
insights = [
    f"**Best total price performance:** {best_ticker} returned {best_return:.1f}% from the first to last available observation.",
    f"**Lowest total price performance:** {worst_ticker} returned {worst_return:.1f}% over the same displayed period."
]
if most_volatile:
    insights.append(f"**Highest recent realized volatility:** {most_volatile} had the highest available 30-trading-day annualized volatility at the end of the period ({vol_last[most_volatile]:.1f}%).")
st.write(" ".join(insights))
st.caption("These comparisons use adjusted closing prices, which account for splits and distributions. Past performance does not predict future results.")

st.divider()
st.subheader("1. Indexed price performance")
st.markdown("Each company starts at **100** on its first available date, making percentage performance comparable despite different share prices.")
fig1 = px.line(indexed.reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Index (start = 100)"),
              x="Date", y="Index (start = 100)", color="Company", title="Growth of $100-equivalent indexed investment")
fig1.update_layout(hovermode="x unified", yaxis_title="Index value (start = 100)", legend_title="Company")
st.plotly_chart(fig1, use_container_width=True)

st.subheader("2. Adjusted closing price")
st.markdown("Shows the absolute adjusted share-price level in **USD per share**. Different starting prices mean this chart is less suitable than the indexed chart for comparing percentage gains.")
fig2 = px.line(close.reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Adjusted close (USD)"),
               x="Date", y="Adjusted close (USD)", color="Company", title="Adjusted closing price over time")
fig2.update_layout(hovermode="x unified", yaxis_title="USD per share", legend_title="Company")
st.plotly_chart(fig2, use_container_width=True)

st.subheader("3. Daily percentage returns")
st.markdown("Daily change in adjusted close, shown as a percentage. Spikes indicate sessions with unusually large gains or losses.")
ret_long = (returns * 100).reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Daily return (%)")
fig3 = px.line(ret_long, x="Date", y="Daily return (%)", color="Company", title="Daily returns")
fig3.add_hline(y=0, line_dash="dash", line_color="gray")
fig3.update_layout(hovermode="x unified", yaxis_title="Daily return (%)", legend_title="Company")
st.plotly_chart(fig3, use_container_width=True)

st.subheader("4. Rolling 30-trading-day volatility")
st.markdown("Annualized standard deviation of daily returns, expressed as a percentage. Higher values mean more variable recent returns, not necessarily a worse investment.")
vol_long = rolling_vol.reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Annualized volatility (%)")
fig4 = px.line(vol_long, x="Date", y="Annualized volatility (%)", color="Company", title="30-day rolling annualized volatility")
fig4.update_layout(hovermode="x unified", yaxis_title="Annualized volatility (%)", legend_title="Company")
st.plotly_chart(fig4, use_container_width=True)

st.subheader("5. Trading volume")
st.markdown("Daily number of shares traded. Volume is plotted on a logarithmic axis to make very large spikes and smaller sessions easier to compare.")
if not volume.empty:
    volume_long = volume.reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Shares traded")
    volume_long = volume_long[volume_long["Shares traded"] > 0]
    fig5 = px.line(volume_long, x="Date", y="Shares traded", color="Company", title="Daily trading volume")
    fig5.update_yaxes(type="log", title="Shares traded (log scale)")
    fig5.update_layout(hovermode="x unified", legend_title="Company")
    st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Volume data was not returned for this selection.")

st.subheader("6. Drawdown from prior peak")
st.markdown("Shows the percentage below each company's previous peak. More negative values indicate a deeper decline from a prior high.")
dd_long = drawdown.reset_index(names="Date").melt(id_vars="Date", var_name="Company", value_name="Drawdown (%)")
fig6 = px.line(dd_long, x="Date", y="Drawdown (%)", color="Company", title="Drawdown from running peak")
fig6.add_hline(y=0, line_dash="dash", line_color="gray")
fig6.update_layout(hovermode="x unified", yaxis_title="Drawdown (%)", legend_title="Company")
st.plotly_chart(fig6, use_container_width=True)

st.subheader("Comparison table")
table = pd.DataFrame({
    "Start adjusted close (USD)": close.iloc[0],
    "Latest adjusted close (USD)": close.iloc[-1],
    "Total price return (%)": total_return,
    "Annualized volatility (%)": returns.std() * np.sqrt(252) * 100,
    "Maximum drawdown (%)": drawdown.min()
}).round(2)
table.index.name = "Company"
st.dataframe(table, use_container_width=True)

st.caption("Educational project only. Market data is supplied by Yahoo Finance and may be delayed, revised, or unavailable at times. This dashboard is not financial advice.")
