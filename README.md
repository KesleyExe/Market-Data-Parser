What It Does

QuantFlow Zero is a fully self-contained market analysis tool that fetches real-time stock and crypto data from Yahoo Finance, runs five technical indicators on it, and generates a beautiful interactive dashboard all without needing any external Python packages. You just run the script, type a stock symbol, and it spits out a sleek HTML report you open in your browser.

Key Features

- Zero dependencies — Uses only Python's built-in libraries (urllib, json, math, datetime). No pip install needed, no virtual environments, no version conflicts
- Fetches live market data — Pulls real price history from Yahoo Finance's public API for any stock, ETF, or cryptocurrency (AAPL, TSLA, BTC-USD, etc.)
- Five technical indicators analyzed in plain English — Moving Average, RSI, MACD, Bollinger Bands, and Volume, each explained like you're five years old (e.g., "RSI is 78 — OVERBOUGHT. Everyone's buying = potential pullback coming")
- AI-style prediction — Combines all five signals into a single verdict: STRONG BUY, BUY, HOLD/WAIT, SELL, or STRONG SELL, with a confidence percentage
- Interactive chart — Renders price action with Moving Averages and Bollinger Bands using Chart.js, loaded from a CDN inside the HTML
- Built-in risk management — Auto-calculates stop loss (2× ATR), position size (2% portfolio rule), risk/reward ratio, and max loss, so you don't blow up your account
- Generates a portable HTML file — The output is a single .html file you can double-click, email, or host anywhere. No server required
- Auto-opens your browser — After analysis, it automatically launches the report so you see results instantly

| Step                 | What Happens                                                           |
| -------------------- | ---------------------------------------------------------------------- |
| 1. You type a symbol | `AAPL`, `TSLA`, `BTC-USD`, etc.                                        |
| 2. It fetches data   | Uses `urllib` to hit Yahoo Finance's chart API                         |
| 3. Pure Python math  | Calculates MA, RSI, MACD, Bollinger Bands, ATR without NumPy or Pandas |
| 4. Signals scored    | Each indicator gets a strength score (-3 to +3)                        |
| 5. Prediction made   | Scores are summed into BUY/SELL/HOLD with confidence %                 |
| 6. HTML generated    | Everything is baked into a single file with embedded CSS/JS            |
| 7. Browser opens     | You see a dark-mode dashboard with charts and risk metrics             |

