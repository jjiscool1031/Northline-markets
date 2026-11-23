
from flask import Flask, jsonify, render_template_string
import requests
import os
import time
app = Flask(__name__)

API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")
PRICE_CACHE = {}
CACHE_DURATION = 30
HISTORY_CACHE = {}
HISTORY_CACHE_DURATION = 60
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
}.ticker-bar {
    display: flex;
    align-items: center;
    gap: 35px;
    padding: 15px 25px;
    background: #0d1522;
    border-bottom: 1px solid #263247;
    overflow-x: auto;
    white-space: nowrap;
}

.ticker-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 85px;
}

.ticker-item span {
    color: #8292aa;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}

.ticker-item strong {
    color: #36c98f;
    font-size: 14px;
    font-weight: bold;
}

.ticker-bar::-webkit-scrollbar {
    height: 4px;
}

.ticker-bar::-webkit-scrollbar-thumb {
    background: #34445e;
    border-radius: 5px;
}
</style>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
</head>

<body>

<header class="topbar">
    <div class="logo">NORTHLINE MARKETS</div>
    <div class="status">● MARKET DASHBOARD</div>
</header>
<div class="ticker-bar">
    <div class="ticker-item">
        <span>SPY</span>
        <strong id="ticker-spy">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>QQQ</span>
        <strong id="ticker-qqq">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>AAPL</span>
        <strong id="ticker-aapl">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>NVDA</span>
        <strong id="ticker-nvda">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>TSLA</span>
        <strong id="ticker-tsla">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>GOLD</span>
        <strong id="ticker-gold">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>SILVER</span>
        <strong id="ticker-silver">Loading...</strong>
    </div>
    <div class="ticker-item">
        <span>BITCOIN</span>
        <strong id="ticker-btc">Loading...</strong>
    </div>
</div>
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
    <div class="chart-header">
        <div>
            <h2>Market Chart</h2>
            <p style="color:#8998ad;font-size:13px;">
                Interactive price chart
            </p>
        </div>

        <select id="chart-symbol" class="chart-select">
            <option value="SPY">SPY</option>
            <option value="QQQ">QQQ</option>
            <option value="AAPL">AAPL</option>
            <option value="NVDA">NVDA</option>
            <option value="TSLA">TSLA</option>
        </select>
    </div>

    <div id="trading-chart" style="width:100%;height:400px;"></div>

    <div class="chart-timeframes">
        <button type="button">1D</button>
        <button type="button">1W</button>
        <button type="button">1M</button>
        <button type="button">3M</button>
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
loadQuote("SPY", "ticker-spy");
loadQuote("QQQ", "ticker-qqq");
loadQuote("AAPL", "ticker-aapl");
loadQuote("NVDA", "ticker-nvda");
loadQuote("TSLA", "ticker-tsla");
const chartElement = document.getElementById("trading-chart");

if (chartElement && window.LightweightCharts) {
    const chart = LightweightCharts.createChart(chartElement, {
        width: chartElement.clientWidth,
        height: 400,
        layout: {
            background: { color: "#111827" },
            textColor: "#d1d5db"
        },
        grid: {
            vertLines: { color: "#263244" },
            horzLines: { color: "#263244" }
        },
        rightPriceScale: {
            borderColor: "#34445e"
        },
        timeScale: {
            borderColor: "#34445e",
            timeVisible: true
        }
    });

    const candles = chart.addCandlestickSeries({
        upColor: "#16c784",
        downColor: "#ea3943",
        borderUpColor: "#16c784",
        borderDownColor: "#ea3943",
        wickUpColor: "#16c784",
        wickDownColor: "#ea3943"
    });
const chartCache = {};
   

async function loadCandles(symbol) {
    candles.setData([]);

    if (chartCache[symbol]) {
        candles.setData(chartCache[symbol]);
        chart.timeScale().fitContent();
        return;
    }

    try {
        const response = await fetch(`/api/history/${symbol}`);
        const data = await response.json();

        if (!data.values) {
            console.error(data.error || "Chart data unavailable");
            return;
        }

        const formatted = data.values.reverse().map(item => ({
            time: item.datetime,
            open: Number(item.open),
            high: Number(item.high),
            low: Number(item.low),
            close: Number(item.close)
        }));

        chartCache[symbol] = formatted;
        candles.setData(formatted);
        chart.timeScale().fitContent();

    } catch (error) {
        console.error("Chart loading error:", error);
    }
}

    loadCandles("SPY");

    document.getElementById("chart-symbol").addEventListener("change", event => {
        loadCandles(event.target.value);
    });

    window.addEventListener("resize", () => {
        chart.applyOptions({
            width: chartElement.clientWidth
        });
    });
}
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
        cached = PRICE_CACHE.get(symbol)

        if cached and time.time() - cached["time"] < CACHE_DURATION:
            return jsonify({"price": cached["price"]})

        response = requests.get(
            "https://api.twelvedata.com/price",
            params={"symbol": symbol, "apikey": API_KEY},
            timeout=10
        )
        data = response.json()

        if "price" not in data:
            return jsonify({"error": data.get("message", "Quote unavailable")}), 502
        PRICE_CACHE[symbol] = {
        "price": data["price"],
        "time": time.time()
        }
        return jsonify({"price": data["price"]})

    except requests.RequestException:
        return jsonify({"error": "Market data service unavailable"}), 502
@app.route("/api/history/<symbol>")
def history(symbol):
    if not API_KEY:
        return jsonify({"error": "API key not configured"}), 503

    symbol = symbol.upper()

    if not symbol.isalnum() or len(symbol) > 10:
        return jsonify({"error": "Invalid symbol"}), 400

    try:
        cached = HISTORY_CACHE.get(symbol)

        if cached and time.time() - cached["time"] < HISTORY_CACHE_DURATION:
            return jsonify({"values": cached["values"]})

        response = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol,
                "interval": "1day",
                "outputsize": 100,
                "apikey": API_KEY
            },
            timeout=10
        )

        data = response.json()

        if "values" not in data:
            return jsonify({
                "error": data.get("message", "Historical data unavailable")
            }), 502

        HISTORY_CACHE[symbol] = {
            "values": data["values"],
            "time": time.time()
        }

        return jsonify({"values": data["values"]})

    except requests.RequestException:
        return jsonify({
            "error": "Historical market data unavailable"
        }), 502
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
