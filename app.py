
from flask import Flask, jsonify, render_template_string, request
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
<a class="nav" href="/?section=help">Help Center</a>
<a class="nav" href="/?section=academy">Trading Academy</a>
</aside>

<main>
    {% set section = request.args.get('section', 'overview') %}

    {% if section == 'help' %}
        <h1>Help Center</h1>
        <div class="subtitle">Find answers and learn how to use Northline Markets.</div>
        <div class="help-search">
    <input
        type="text"
        id="help-search"
        placeholder="Search for answers..."
    >
</div>

<div class="help-categories">
    <button type="button" onclick="filterHelp('all')">All Questions</button>
    <button type="button" onclick="filterHelp('charts')">Charts</button>
    <button type="button" onclick="filterHelp('markets')">Markets</button>
    <button type="button" onclick="filterHelp('platform')">Platform</button>
</div>

<div class="faq-list">

    <details class="faq-item" data-category="platform">
        <summary>What is Northline Markets?</summary>
        <p>Northline Markets is an educational financial markets platform designed to help users explore stocks, market data, charts, and trading concepts.</p>
    </details>

    <details class="faq-item" data-category="charts">
        <summary>How do I read a candlestick chart?</summary>
        <p>Each candlestick represents price movement over a selected time period. The body shows the opening and closing prices, while the wicks show the highest and lowest prices.</p>
    </details>

    <details class="faq-item" data-category="markets">
        <summary>What is the S&P 500?</summary>
        <p>The S&P 500 is an index that tracks approximately 500 leading publicly traded U.S. companies.</p>
    </details>

    <details class="faq-item" data-category="charts">
        <summary>Why isn't my chart loading?</summary>
        <p>Charts may occasionally fail because of data-provider limits, unavailable historical data, or temporary connection issues.</p>
    </details>

    <details class="faq-item" data-category="markets">
        <summary>Why are stock prices delayed?</summary>
        <p>Market data availability and delays depend on the data provider and subscription plan. Some displayed prices may not be real-time.</p>
    </details>

    <details class="faq-item" data-category="platform">
        <summary>What is a watchlist?</summary>
        <p>A watchlist lets you keep track of selected stocks and follow their price movements in one place.</p>
    </details>

</div>

    {% elif section == 'academy' %}
        <h1>Trading Academy</h1>
        <div class="subtitle">Build your understanding of financial markets step by step.</div>
        <div class="academy-grid">

    <div class="panel academy-card">
        <h2>01. Stock Market Basics</h2>
        <p>Learn how financial markets work and understand the basics.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p><strong>What is a stock?</strong> A stock represents ownership in a company.</p>
            <p><strong>What is an exchange?</strong> An exchange is a marketplace where financial securities are bought and sold.</p>
            <p><strong>What is an index?</strong> An index tracks the performance of a selected group of investments.</p>
        </details>
    </div>

    <div class="panel academy-card">
        <h2>02. Understanding Charts</h2>
        <p>Learn how traders study price movements and market activity.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p><strong>Candlesticks:</strong> Show opening, closing, highest, and lowest prices during a time period.</p>
            <p><strong>Volume:</strong> Shows how many shares were traded during a period.</p>
            <p><strong>Timeframes:</strong> Charts can display price activity over minutes, hours, days, or longer.</p>
        </details>
    </div>

    <div class="panel academy-card">
        <h2>03. Technical Analysis</h2>
        <p>Explore common methods used to study historical market behavior.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p><strong>Support:</strong> A price area where buying interest has historically appeared.</p>
            <p><strong>Resistance:</strong> A price area where selling interest has historically appeared.</p>
            <p><strong>Trends:</strong> General upward, downward, or sideways price movements.</p>
        </details>
    </div>

    <div class="panel academy-card">
        <h2>04. Trading Strategies</h2>
        <p>Understand how trading plans are structured.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p>Study how traders define their goals, entry conditions, exit conditions, and the reasons behind each decision.</p>
            <p>There is no strategy that guarantees a profitable result. Historical patterns do not predict future prices.</p>
        </details>
    </div>

    <div class="panel academy-card">
        <h2>05. Risk Management</h2>
        <p>Understand how traders think about uncertainty and potential losses.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p>Learn about position sizing, diversification, risk limits, and why protecting capital matters.</p>
            <p>Never assume a trade will work out as expected.</p>
        </details>
    </div>

    <div class="panel academy-card">
        <h2>06. Practice & Review</h2>
        <p>Learn through simulated examples before studying real-world decisions.</p>
        <details>
            <summary>Explore this lesson</summary>
            <p>Use paper trading to practice with simulated money. Record your reasoning, review outcomes, and learn from mistakes without risking real money.</p>
        </details>
    </div>

</div>

    {% else %}
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

    {% endif %}
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
const helpSearch = document.getElementById("help-search");

if (helpSearch) {
    helpSearch.addEventListener("input", function () {
        const searchText = helpSearch.value.toLowerCase();
        const questions = document.querySelectorAll(".faq-item");

        questions.forEach(question => {
            const questionText = question.textContent.toLowerCase();

            question.style.display = questionText.includes(searchText)
                ? "block"
                : "none";
        });
    });
}

function filterHelp(category) {
    const questions = document.querySelectorAll(".faq-item");

    questions.forEach(question => {
        const matches = category === "all" ||
            question.dataset.category === category;

        question.style.display = matches ? "block" : "none";
    });
}
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
