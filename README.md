# Public Stock Comparison Dashboard

An interactive Streamlit dashboard comparing publicly traded companies using recent daily market data from Yahoo Finance through `yfinance`.

## Features

- Shared company selector and date-range filter
- Six distinct visualizations:
  1. Indexed price performance (start = 100)
  2. Adjusted closing price (USD/share)
  3. Daily percentage returns
  4. Rolling 30-trading-day annualized volatility
  5. Daily trading volume (log scale)
  6. Drawdown from prior peak
- Dynamically generated performance and volatility observations
- Brief interpretation guide explaining what each visualization reveals
- Course credit footer: “Developed for CPS*5745 by Angel Bello”
- Summary comparison table (not counted as one of the six visualizations)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

## Deploy publicly with Streamlit Community Cloud

1. Create a GitHub repository, for example `public-stock-dashboard`.
2. Upload `app.py`, `requirements.txt`, and `README.md` to the repository root.
3. Visit https://share.streamlit.io/ and sign in with GitHub.
4. Select **Create app**, choose your repository, branch, and `app.py` as the main file.
5. Deploy the app. In app settings, make sure the app is public and does not require viewer sign-in.
6. Copy the generated `https://....streamlit.app` URL and test it in a private/incognito browser window.

The dashboard fetches data when it runs and caches it for 15 minutes. No API key is required for this data source. Public deployment depends on the hosting provider's current policies and availability.

## Notes

- Yahoo Finance data may be delayed or unavailable. The selected end date is inclusive in the UI.
- Adjusted closing prices are used for price-based comparisons.
- Returns and volatility are historical measures and do not predict future performance.
- This project is educational and is not financial advice.
