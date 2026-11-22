
from flask import Flask, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Northline Markets</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #080d16;
    color: #e5eaf2;
    font-family: Arial, sans-serif;
}

.topbar {
    height: 65px;
    background: #101827;
    border-bottom: 1px solid #263247;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 25px;
}

.logo {
    font-size: 21px;
    font-weight: bold;
    color: #55a6ff;
}

.status {
    color: #36c98f;
    font-size: 12px;
}

.layout {
    display: flex;
    min-height: calc(100vh - 65px);
}

.sidebar {
    width: 215px;
    background: #0d1421;
    border-right: 1px solid #263247;
    padding: 25px 15px;
}

.sidebar h3 {
    color: #77869d;
    font-size: 11px;
    letter-spacing: 1.5px;
    padding-left: 12px;
}

.nav {
    display: block;
    color: #b9c5d6;
    text-decoration: none;
    padding: 13px 12px;
    margin: 5px 0;
    border-radius: 7px;
    font-size: 14px;
}

.nav:hover, .nav.active {
    background: #1b2b43;
    color: #62aaff;
}

main {
    flex: 1;
    padding: 28px;
    min-width: 0;
}

h1 {
    font-size: 26px;
    margin: 0 0 8px;
}

.subtitle {
    color: #8391a7;
    margin-bottom: 28px;
    font-size: 14px;
}

.market-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 25px;
}

.market-card, .panel {
    background: #111b2b;
    border: 1px solid #263247;
    border-radius: 10px;
    padding: 18px;
}

.market-card span {
    color: #8998ad;
    font-size: 12px;
}

.market-card h2 {
    margin: 10px 0 0;
    font-size: 22px;
}

.green {
    color: #36c98f;
}

.red {
    color: #ff6577;
}

.content-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 18px;
}

.panel h2 {
    font-size: 16px;
    margin: 0 0 18px;
}

.chart-placeholder {
    height: 310px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #65748b;
    background: #0b1320;
    border: 1px dashed #34445e;
    border-radius: 8px;
    text-align: center;
}

.watch-row {
    display: flex;
    justify-content: space-between;
    padding: 14px 0;
    border-bottom: 1px solid #263247;
    font-size: 13px;
}

.section {
    margin-top: 22px;
}

@media (max-width: 850px) {
    .sidebar {
        width: 155px;
    }

    .market-bar {
        grid-template-columns: repeat(2, 1fr);
    }

    .content-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 550px) {
    .sidebar {
        display: none;
    }

    main {
        padding: 16px;
    }
}
</style>
</head>

<body>

<header class="topbar">
    <div class="logo">NORTHLINE MARKETS</div>
    <div class="status">● MARKET DASHBOARD</div>
</header>

<div class="layout">

<aside class="sidebar">
    <h3>MARKETS</h3>
    <a class="nav active" href="/">Market Overview</a>
    <a class="nav" href="/?section=trading">Day Trading</a>
    <a class="nav" href="/?section=stocks">Stocks</a>
    <a class="nav" href="/?section=metals">Precious Metals</a>
    <a class="nav" href="/?section=crypto">Cryptocurrency</a>

    <h3>TOOLS</h3>
    <a class="nav" href="/?section=watchlist">Watchlist</a>
    <a class="nav" href="/?section=education">Learning Center</a>
</aside>

<main>
    <h1>Market Overview</h1>
    <div class="subtitle">
        Your central hub for financial markets and market information.
    </div>

    <div class="market-bar">
        <div class="market-card">
            <span>S&P 500 · SPY</span>
            <h2 id="spy">Loading...</h2>
        </div>

        <div class="market-card">
            <span>NASDAQ · QQQ</span>
            <h2 id="qqq">Loading...</h2>
        </div>

        <div class="market-card">
            <span>DOW JONES · DIA</span>
            <h2 id="dia">Loading...</h2>
        </div>

        <div class="market-card">
            <span>GOLD · XAU/USD</span>
            <h2>Gold Market</h2>
        </div>
    </div>

    <div class="content-grid">
        <section class="panel">
            <h2>Market Chart</h2>
            <div class="chart-placeholder">
                Interactive candlestick chart coming in the next build step.
            </div>
        </section>

        <section class="panel">
            <h2>Market Watch</h2>

            <div class="watch-row">
                <strong>Apple</strong><span>AAPL</span>
            </div>

            <div class="watch-row">
                <strong>Microsoft</strong><span>MSFT</span>
            </div>

            <div class="watch-row">
                <strong>NVIDIA</strong><span>NVDA</span>
            </div>

            <div class="watch-row">
                <strong>Amazon</strong><span>AMZN</span>
            </div>

            <div class="watch-row">
                <strong>Tesla</strong><span>TSLA</span>
            </div>
        </section>
    </div>

    <section class="panel section">
        <h2>Northline Markets</h2>
        <p style="color:#8998ad;font-size:14px;">
            A market information and financial education platform.
            More tools and interactive features are on the way.
        </p>
    </section>
</main>

</div>

<script>
async function loadQuote(symbol, elementId) {
    try {
        const response = await fetch("/api/quote/" + symbol);
        const data = await response.json();

        const element = document.getElementById(elementId);

        if (data.price) {
            element.textContent = "$" + Number(data.price).toFixed(2);
        } else {
            element.textContent = "Unavailable";
        }
    } catch (error) {
        document.getElementById(elementId).textContent = "Unavailable";
    }
}

loadQuote("SPY", "spy");
loadQuote("QQQ", "qqq");
loadQuote("DIA", "dia");
</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/quote/<symbol>")
def quote(symbol):
    if not API_KEY:
        return jsonify({"error": "API key not configured"}), 503

    symbol = symbol.upper()

    if not symbol.isalnum() or len(symbol) > 10:
        return jsonify({"error": "Invalid symbol"}), 400

    try:
        response = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol": symbol, "apikey": API_KEY},
            timeout=10
        )
        data = response.json()

        if "price" not in data:
            return jsonify({"error": data.get("message", "Quote unavailable")}), 502

        return jsonify({"price": data["price"]})

    except requests.RequestException:
        return jsonify({"error": "Market data service unavailable"}), 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
