"""
QuantFlow Zero - Market Intelligence Dashboard
NO EXTERNAL DEPENDENCIES. Just Python 3.8+ built-in libraries.
Generates a single HTML file you double-click to open.

Usage:
    python quantflow_zero.py
    Then open the generated "quantflow_report.html" in your browser
"""

"""
QuantFlow Zero - Market Intelligence Dashboard
Copyright (c) 2026 Kesley
MIT License - See LICENSE file for details
"""

import urllib.request
import urllib.error
import json
import math
import datetime
import os
import sys

# ==================== PURE PYTHON DATA FETCHING ====================

def fetch_yahoo_data(symbol, period="3mo"):
    symbol = symbol.upper().replace("-", "-")

    # Yahoo Finance API endpoint
    # period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    period_map = {
        "1d": ("1d", "1m"),
        "5d": ("5d", "5m"),
        "1mo": ("1mo", "30m"),
        "3mo": ("3mo", "1d"),
        "6mo": ("6mo", "1d"),
        "1y": ("1y", "1d"),
        "2y": ("2y", "1wk"),
        "5y": ("5y", "1wk"),
    }

    range_val, interval = period_map.get(period, ("3mo", "1d"))

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range_val}&interval={interval}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]

        # Convert to simple lists of dicts
        prices = []
        for i in range(len(timestamps)):
            if quotes['close'][i] is not None:
                prices.append({
                    'date': datetime.datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                    'open': quotes['open'][i] or 0,
                    'high': quotes['high'][i] or 0,
                    'low': quotes['low'][i] or 0,
                    'close': quotes['close'][i] or 0,
                    'volume': quotes['volume'][i] or 0
                })

        return prices

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# ==================== PURE PYTHON MATH (NO NUMPY) ====================

def mean(values):
    """Calculate average"""
    if not values:
        return 0
    return sum(values) / len(values)

def std_dev(values):
    """Calculate standard deviation"""
    if len(values) < 2:
        return 0
    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    return math.sqrt(variance)

def ema(values, period):
    """Calculate Exponential Moving Average"""
    if len(values) < period:
        return values

    multiplier = 2 / (period + 1)
    ema_values = [mean(values[:period])]

    for price in values[period:]:
        ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])

    # Pad with None for alignment
    return [None] * (period - 1) + ema_values

def calculate_ma(prices, period):
    """Simple Moving Average"""
    closes = [p['close'] for p in prices]
    ma = []
    for i in range(len(closes)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(mean(closes[i - period + 1:i + 1]))
    return ma

def calculate_rsi(prices, period=14):
    """Relative Strength Index"""
    closes = [p['close'] for p in prices]
    if len(closes) < period + 1:
        return [None] * len(closes)

    rsi = [None] * period

    for i in range(period, len(closes)):
        gains = []
        losses = []
        for j in range(i - period + 1, i + 1):
            change = closes[j] - closes[j - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = mean(gains) if gains else 0
        avg_loss = mean(losses) if losses else 0

        if avg_loss == 0:
            rsi.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi.append(100 - (100 / (1 + rs)))

    return rsi

def calculate_macd(prices):
    """MACD indicator"""
    closes = [p['close'] for p in prices]
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)

    macd_line = []
    for i in range(len(closes)):
        if ema12[i] is None or ema26[i] is None:
            macd_line.append(None)
        else:
            macd_line.append(ema12[i] - ema26[i])

    # Signal line = 9-period EMA of MACD
    valid_macd = [m for m in macd_line if m is not None]
    signal_ema = ema(valid_macd, 9)

    signal_line = [None] * (len(macd_line) - len(signal_ema)) + signal_ema

    return macd_line, signal_line

def calculate_bollinger(prices, period=20):
    """Bollinger Bands"""
    closes = [p['close'] for p in prices]
    middle = calculate_ma(prices, period)

    upper = []
    lower = []

    for i in range(len(closes)):
        if i < period - 1:
            upper.append(None)
            lower.append(None)
        else:
            window = closes[i - period + 1:i + 1]
            std = std_dev(window)
            upper.append(middle[i] + (std * 2))
            lower.append(middle[i] - (std * 2))

    return upper, lower, middle

def calculate_atr(prices, period=14):
    """Average True Range"""
    if len(prices) < 2:
        return 0

    tr_values = []
    for i in range(1, len(prices)):
        high_low = prices[i]['high'] - prices[i]['low']
        high_close = abs(prices[i]['high'] - prices[i - 1]['close'])
        low_close = abs(prices[i]['low'] - prices[i - 1]['close'])
        tr_values.append(max(high_low, high_close, low_close))

    if len(tr_values) < period:
        return mean(tr_values) if tr_values else 0

    return mean(tr_values[-period:])

def calculate_volume_ma(prices, period=20):
    """Volume Moving Average"""
    volumes = [p['volume'] for p in prices]
    vma = []
    for i in range(len(volumes)):
        if i < period - 1:
            vma.append(None)
        else:
            vma.append(mean(volumes[i - period + 1:i + 1]))
    return vma

# ==================== ANALYSIS ENGINE ====================

def analyze_symbol(symbol):
    """Full technical analysis using pure Python"""
    print(f"\n📡 Fetching data for {symbol}...")
    prices = fetch_yahoo_data(symbol)

    if not prices or len(prices) < 50:
        return {"error": f"Not enough data for {symbol}. Try a different symbol."}

    print(f"✅ Got {len(prices)} days of data")

    latest = prices[-1]
    prev = prices[-2]
    price = latest['close']
    price_change = ((price - prev['close']) / prev['close']) * 100 if prev['close'] != 0 else 0

    signals = {}

    # Moving Averages
    ma20 = calculate_ma(prices, 20)
    ma50 = calculate_ma(prices, 50)

    ma_signal = "NEUTRAL"
    ma_strength = 0
    if ma20[-1] and ma50[-1]:
        if ma20[-1] > ma50[-1]:
            ma_signal = "BULLISH"
            ma_strength = 3 if (ma20[-2] and ma20[-2] <= (ma50[-2] or 0)) else 2
        else:
            ma_signal = "BEARISH"
            ma_strength = -3 if (ma20[-2] and ma20[-2] >= (ma50[-2] or 0)) else -2

    signals['moving_average'] = {
        'signal': ma_signal,
        'strength': ma_strength,
        'value': f"${price:.2f} vs MA20: ${ma20[-1]:.2f}" if ma20[-1] else "N/A",
        'explanation': f"Price (${price:.2f}) is {'above' if ma_signal == 'BULLISH' else 'below' if ma_signal == 'BEARISH' else 'mixed with'} both moving averages. Trend is {'UP' if ma_signal == 'BULLISH' else 'DOWN' if ma_signal == 'BEARISH' else 'UNCLEAR'}."
    }

    # RSI
    rsi_values = calculate_rsi(prices)
    latest_rsi = rsi_values[-1] if rsi_values[-1] is not None else 50

    rsi_signal = "NEUTRAL"
    rsi_strength = 0
    if latest_rsi > 70:
        rsi_signal, rsi_strength = "BEARISH", -2
    elif latest_rsi > 60:
        rsi_signal, rsi_strength = "BEARISH", -1
    elif latest_rsi < 30:
        rsi_signal, rsi_strength = "BULLISH", 2
    elif latest_rsi < 40:
        rsi_signal, rsi_strength = "BULLISH", 1

    signals['rsi'] = {
        'signal': rsi_signal,
        'strength': rsi_strength,
        'value': f"{latest_rsi:.1f}",
        'explanation': f"RSI at {latest_rsi:.1f} is {'OVERBOUGHT - expect pullback' if latest_rsi > 70 else 'OVERSOLD - potential bounce' if latest_rsi < 30 else 'neutral - no extreme pressure'}."
    }

    # MACD
    macd_line, signal_line = calculate_macd(prices)
    macd_val = macd_line[-1] if macd_line[-1] is not None else 0
    sig_val = signal_line[-1] if signal_line[-1] is not None else 0
    prev_macd = macd_line[-2] if len(macd_line) > 1 and macd_line[-2] is not None else macd_val
    prev_sig = signal_line[-2] if len(signal_line) > 1 and signal_line[-2] is not None else sig_val

    macd_signal = "NEUTRAL"
    macd_strength = 0
    if macd_val > sig_val:
        macd_signal = "BULLISH"
        macd_strength = 3 if prev_macd <= prev_sig else 1
    elif macd_val < sig_val:
        macd_signal = "BEARISH"
        macd_strength = -3 if prev_macd >= prev_sig else -1

    signals['macd'] = {
        'signal': macd_signal,
        'strength': macd_strength,
        'value': f"MACD: {macd_val:.3f}",
        'explanation': f"MACD {'crossed above' if macd_signal == 'BULLISH' and macd_strength == 3 else 'is above' if macd_signal == 'BULLISH' else 'crossed below' if macd_signal == 'BEARISH' and macd_strength == -3 else 'is below'} signal line. Momentum is {'shifting UP' if macd_signal == 'BULLISH' else 'shifting DOWN' if macd_signal == 'BEARISH' else 'neutral'}."
    }

    # Bollinger Bands
    bb_upper, bb_lower, bb_mid = calculate_bollinger(prices)
    upper = bb_upper[-1] if bb_upper[-1] is not None else price * 1.05
    lower = bb_lower[-1] if bb_lower[-1] is not None else price * 0.95
    mid = bb_mid[-1] if bb_mid[-1] is not None else price

    bb_signal = "NEUTRAL"
    bb_strength = 0
    if price > upper:
        bb_signal, bb_strength = "BEARISH", -2
    elif price < lower:
        bb_signal, bb_strength = "BULLISH", 2
    elif price > mid:
        bb_signal, bb_strength = "BEARISH", -1
    elif price < mid:
        bb_signal, bb_strength = "BULLISH", 1

    signals['bollinger'] = {
        'signal': bb_signal,
        'strength': bb_strength,
        'value': f"${lower:.0f} - ${upper:.0f}",
        'explanation': f"Price is {'above upper band - unusually expensive' if price > upper else 'below lower band - unusually cheap' if price < lower else 'in normal range'}."
    }

    # Volume
    vma = calculate_volume_ma(prices)
    vol_ma = vma[-1] if vma[-1] is not None else latest['volume']
    vol_ratio = latest['volume'] / vol_ma if vol_ma != 0 else 1

    vol_signal = "NEUTRAL"
    vol_strength = 0
    if vol_ratio > 1.5 and price_change > 0:
        vol_signal, vol_strength = "BULLISH", 2
    elif vol_ratio > 1.5 and price_change < 0:
        vol_signal, vol_strength = "BEARISH", -2

    signals['volume'] = {
        'signal': vol_signal,
        'strength': vol_strength,
        'value': f"{vol_ratio:.1f}x normal",
        'explanation': f"Volume is {vol_ratio:.1f}x average. {'Strong buying on up day' if vol_signal == 'BULLISH' else 'Panic selling on down day' if vol_signal == 'BEARISH' else 'Normal activity'}."
    }

    # Prediction
    total_strength = sum(s['strength'] for s in signals.values())
    bullish = sum(1 for s in signals.values() if s['signal'] == 'BULLISH')
    bearish = sum(1 for s in signals.values() if s['signal'] == 'BEARISH')

    if total_strength >= 4:
        prediction, outlook = "STRONG BUY", "Multiple strong buy signals aligned. High conviction."
    elif total_strength >= 2:
        prediction, outlook = "BUY", "More bullish signals than bearish. Good setup."
    elif total_strength <= -4:
        prediction, outlook = "STRONG SELL", "Multiple warning signs. Consider exiting."
    elif total_strength <= -2:
        prediction, outlook = "SELL", "More bearish than bullish. Protect capital."
    else:
        prediction, outlook = "HOLD / WAIT", "Mixed signals. Wait for clearer direction."

    confidence = min(100, abs(total_strength) / 15 * 100)

    # Risk Management
    atr = calculate_atr(prices)
    if prediction in ["BUY", "STRONG BUY"]:
        stop_loss = price - (atr * 2)
        target = price + (atr * 3)
    else:
        stop_loss = price + (atr * 2)
        target = price - (atr * 3)

    risk_per_share = abs(price - stop_loss)
    position_size = int((100000 * 0.02) / risk_per_share) if risk_per_share > 0 else 0
    risk_reward = abs(target - price) / risk_per_share if risk_per_share > 0 else 0

    # Chart data (last 60 points)
    chart_slice = prices[-60:]

    return {
        'symbol': symbol.upper(),
        'price': round(price, 2),
        'change': round(price_change, 2),
        'signals': signals,
        'prediction': prediction,
        'confidence': round(confidence, 1),
        'bullish_count': bullish,
        'bearish_count': bearish,
        'outlook': outlook,
        'risk': {
            'stop_loss': round(stop_loss, 2),
            'target': round(target, 2),
            'position_size': position_size,
            'risk_reward': round(risk_reward, 2),
            'atr': round(atr, 2),
            'max_loss': round(risk_per_share * position_size, 2)
        },
        'chart_data': {
            'dates': [p['date'] for p in chart_slice],
            'prices': [p['close'] for p in chart_slice],
            'ma20': ma20[-60:] if len(ma20) >= 60 else ma20,
            'ma50': ma50[-60:] if len(ma50) >= 60 else ma50,
            'bb_upper': bb_upper[-60:] if len(bb_upper) >= 60 else bb_upper,
            'bb_lower': bb_lower[-60:] if len(bb_lower) >= 60 else bb_lower,
            'volume': [p['volume'] for p in chart_slice]
        }
    }

# ==================== HTML GENERATOR ====================

def generate_html(data):
    """Generate a beautiful HTML report"""

    if 'error' in data:
        return f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body style="background:#0a0e1a;color:#ef4444;font-family:sans-serif;text-align:center;padding:50px;">
<h1>❌ Error</h1><p>{data['error']}</p></body></html>"""

    pred_class = 'buy' if 'BUY' in data['prediction'] else 'sell' if 'SELL' in data['prediction'] else 'hold'
    pred_color = '#10b981' if pred_class == 'buy' else '#ef4444' if pred_class == 'sell' else '#f59e0b'

    signal_cards = ""
    for key, sig in data['signals'].items():
        badge_class = 'bullish' if sig['signal'] == 'BULLISH' else 'bearish' if sig['signal'] == 'BEARISH' else 'neutral'
        badge_color = '#10b981' if sig['signal'] == 'BULLISH' else '#ef4444' if sig['signal'] == 'BEARISH' else '#94a3b8'
        bg_color = 'rgba(16,185,129,0.1)' if sig['signal'] == 'BULLISH' else 'rgba(239,68,68,0.1)' if sig['signal'] == 'BEARISH' else 'rgba(148,163,184,0.05)'
        strength = abs(sig['strength'])
        segments = ""
        for i in range(3):
            active = i < strength
            seg_color = '#10b981' if active and sig['signal'] == 'BULLISH' else '#ef4444' if active and sig['signal'] == 'BEARISH' else '#3b82f6' if active else '#1e293b'
            segments += f'<div style="flex:1;height:4px;border-radius:2px;background:{seg_color};margin:0 2px;"></div>'

        signal_cards += f"""
        <div style="background:#111827;border:1px solid #1e293b;border-radius:16px;padding:1.5rem;transition:all 0.3s;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                <div style="font-size:0.8rem;text-transform:uppercase;letter-spacing:1px;color:#64748b;font-weight:700;">{key.replace('_', ' ').upper()}</div>
                <div style="padding:0.3rem 0.7rem;border-radius:20px;font-size:0.7rem;font-weight:700;text-transform:uppercase;background:{bg_color};color:{badge_color};border:1px solid {badge_color}33;">{sig['signal']}</div>
            </div>
            <div style="font-size:1.4rem;font-weight:700;margin-bottom:0.5rem;color:#e2e8f0;">{sig['value']}</div>
            <div style="color:#64748b;font-size:0.85rem;line-height:1.5;">{sig['explanation']}</div>
            <div style="display:flex;margin-top:0.75rem;">{segments}</div>
        </div>
        """

    # Chart data as JSON for Chart.js
    chart_json = json.dumps(data['chart_data'])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QuantFlow - {data['symbol']} Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e1a;
            color: #e2e8f0;
            min-height: 100vh;
        }}
        .bg-grid {{
            position: fixed; top: 0; left: 0;
            width: 100%; height: 100%;
            background-image: 
                linear-gradient(rgba(59, 130, 246, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none; z-index: 0;
        }}
        .container {{
            max-width: 1400px; margin: 0 auto; padding: 2rem;
            position: relative; z-index: 1;
        }}
        header {{ text-align: center; padding: 3rem 0; }}
        .logo {{
            font-size: 3rem; font-weight: 800;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -2px;
            margin-bottom: 0.5rem;
        }}
        .tagline {{ color: #64748b; font-size: 1.1rem; }}
        .price-header {{
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;
        }}
        .price-display {{ font-size: 2.2rem; font-weight: 800; }}
        .price-change {{
            font-size: 1.1rem; font-weight: 600;
            padding: 0.4rem 1rem; border-radius: 8px;
        }}
        .price-change.up {{ color: #10b981; background: rgba(16,185,129,0.1); }}
        .price-change.down {{ color: #ef4444; background: rgba(239,68,68,0.1); }}
        .prediction-hero {{
            background: linear-gradient(135deg, #111827, #1a2234);
            border: 1px solid #1e293b; border-radius: 20px;
            padding: 2.5rem; text-align: center; margin-bottom: 2rem;
            position: relative; overflow: hidden;
        }}
        .prediction-hero::after {{
            content: ''; position: absolute; top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
            opacity: 0.5; pointer-events: none;
        }}
        .prediction-label {{
            font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px;
            color: #64748b; margin-bottom: 1rem; position: relative; z-index: 1;
        }}
        .prediction-value {{
            font-size: 2.8rem; font-weight: 800; margin-bottom: 0.5rem;
            position: relative; z-index: 1; color: {pred_color};
            text-shadow: 0 0 30px {pred_color}33;
        }}
        .confidence-bar {{
            width: 100%; max-width: 400px; height: 8px;
            background: #1e293b; border-radius: 4px;
            margin: 1.5rem auto; overflow: hidden;
            position: relative; z-index: 1;
        }}
        .confidence-fill {{
            height: 100%; border-radius: 4px;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            width: {data['confidence']}%; transition: width 1s ease;
        }}
        .confidence-text {{
            color: #64748b; font-size: 0.9rem;
            position: relative; z-index: 1;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem; margin-top: 2rem;
        }}
        .chart-container {{
            background: #111827; border: 1px solid #1e293b;
            border-radius: 16px; padding: 1.5rem;
            margin-top: 2rem; height: 400px; position: relative;
        }}
        .risk-panel {{
            background: linear-gradient(135deg, rgba(239,68,68,0.05), rgba(16,185,129,0.05));
            border: 1px solid #1e293b; border-radius: 16px;
            padding: 1.5rem; margin-top: 2rem;
        }}
        .risk-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5rem; margin-top: 1rem;
        }}
        .risk-item {{
            text-align: center; padding: 1rem;
            background: #0a0e1a; border-radius: 12px;
            border: 1px solid #1e293b;
        }}
        .risk-label {{
            font-size: 0.7rem; text-transform: uppercase;
            letter-spacing: 1px; color: #64748b; margin-bottom: 0.5rem;
        }}
        .risk-value {{ font-size: 1.3rem; font-weight: 700; }}
        .risk-value.danger {{ color: #ef4444; }}
        .risk-value.safe {{ color: #10b981; }}
        .risk-rules {{
            margin-top: 1.5rem; padding: 1rem;
            background: #0a0e1a; border-radius: 8px;
            color: #64748b; font-size: 0.8rem; line-height: 1.6;
        }}
        @media (max-width: 768px) {{
            .logo {{ font-size: 2rem; }}
            .prediction-value {{ font-size: 2rem; }}
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="bg-grid"></div>
    <div class="container">
        <header>
            <div class="logo">QuantFlow</div>
            <div class="tagline">Market Intelligence for Everyone</div>
        </header>

        <div class="price-header">
            <div>
                <div style="font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">{data['symbol']}</div>
                <div class="price-display">${data['price']}</div>
            </div>
            <div class="price-change {'up' if data['change'] >= 0 else 'down'}">
                {'+' if data['change'] >= 0 else ''}{data['change']}%
            </div>
        </div>

        <div class="prediction-hero">
            <div class="prediction-label">AI Prediction</div>
            <div class="prediction-value">{data['prediction']}</div>
            <div class="confidence-bar">
                <div class="confidence-fill"></div>
            </div>
            <div class="confidence-text">{data['confidence']}% Confidence • {data['bullish_count']} Bullish • {data['bearish_count']} Bearish</div>
            <div style="margin-top: 1rem; color: #64748b; font-size: 0.95rem;">{data['outlook']}</div>
        </div>

        <div class="grid">
            {signal_cards}
        </div>

        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>

        <div class="risk-panel">
            <div style="text-align: center; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; font-weight: 700; margin-bottom: 1rem;">🛡️ Risk Management</div>
            <div class="risk-grid">
                <div class="risk-item">
                    <div class="risk-label">Stop Loss</div>
                    <div class="risk-value danger">${data['risk']['stop_loss']}</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Position Size</div>
                    <div class="risk-value safe">{data['risk']['position_size']} shares</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Risk/Reward</div>
                    <div class="risk-value {'safe' if data['risk']['risk_reward'] >= 2 else 'danger'}">1:{data['risk']['risk_reward']}</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">Max Loss (2% Rule)</div>
                    <div class="risk-value danger">${data['risk']['max_loss']}</div>
                </div>
                <div class="risk-item">
                    <div class="risk-label">ATR (Volatility)</div>
                    <div class="risk-value">${data['risk']['atr']}</div>
                </div>
            </div>
            <div class="risk-rules">
                <strong style="color: #e2e8f0;">Risk Rules:</strong><br>
                • Never risk more than 2% of your portfolio on a single trade<br>
                • Stop loss is placed at 2x ATR from entry<br>
                • Only take trades with Risk/Reward ratio of at least 1:2<br>
                • Position size is calculated automatically based on your stop distance
            </div>
        </div>

        <div style="text-align: center; margin-top: 2rem; padding: 1rem; color: #64748b; font-size: 0.75rem;">
            ⚠️ For educational purposes only. Not financial advice.<br>
            Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>

    <script>
        const chartData = {chart_json};

        const datasets = [{{
            label: 'Price',
            data: chartData.prices,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.4,
            borderWidth: 2,
            pointRadius: 0
        }}];

        if (chartData.ma20 && chartData.ma20.some(v => v !== null && v !== 0)) {{
            datasets.push({{
                label: 'MA20',
                data: chartData.ma20,
                borderColor: '#10b981',
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            }});
        }}

        if (chartData.ma50 && chartData.ma50.some(v => v !== null && v !== 0)) {{
            datasets.push({{
                label: 'MA50',
                data: chartData.ma50,
                borderColor: '#f59e0b',
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            }});
        }}

        if (chartData.bb_upper && chartData.bb_upper.some(v => v !== null && v !== 0)) {{
            datasets.push({{
                label: 'BB Upper',
                data: chartData.bb_upper,
                borderColor: 'rgba(239, 68, 68, 0.3)',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                borderDash: [5, 5]
            }});
            datasets.push({{
                label: 'BB Lower',
                data: chartData.bb_lower,
                borderColor: 'rgba(16, 185, 129, 0.3)',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                borderDash: [5, 5]
            }});
        }}

        new Chart(document.getElementById('priceChart'), {{
            type: 'line',
            data: {{
                labels: chartData.dates,
                datasets: datasets
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{ intersect: false, mode: 'index' }},
                plugins: {{
                    legend: {{ labels: {{ color: '#94a3b8' }} }}
                }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(30, 41, 59, 0.5)' }}, ticks: {{ color: '#64748b' }} }},
                    y: {{ grid: {{ color: 'rgba(30, 41, 59, 0.5)' }}, ticks: {{ color: '#64748b' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    return html

# ==================== MAIN ====================

def main():
    print("=" * 60)
    print("  🚀 QuantFlow ZERO - No Dependencies Required")
    print("=" * 60)
    print()

    # Get symbol from user
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
    else:
        symbol = input("Enter a stock symbol (e.g., AAPL, TSLA, BTC-USD): ").strip().upper()

    if not symbol:
        symbol = "AAPL"
        print(f"Using default: {symbol}")

    # Analyze
    result = analyze_symbol(symbol)

    if 'error' in result:
        print(f"❌ {result['error']}")
        return

    # Generate HTML
    print("🎨 Generating report...")
    html = generate_html(result)

    # Save to file
    output_file = "quantflow_report.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print()
    print("=" * 60)
    print(f"✅ Report saved: {os.path.abspath(output_file)}")
    print()
    print("🌐 Open this file in your browser to view the dashboard")
    print("=" * 60)

    # Try to open browser
    try:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(output_file)}")
        print("🚀 Opening browser automatically...")
    except:
        pass

if __name__ == "__main__":
    main()
