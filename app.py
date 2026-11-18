
from flask import Flask, jsonify, request, render_template_string
import requests
import os
app = Flask(__name__)

# PASTE YOUR NEW TWELVE DATA API KEY BETWEEN THE QUOTES
API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")

BASE_URL = "https://api.twelvedata.com"


def get_data(endpoint, params):
    params["apikey"] = API_KEY

    try:
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "error":
            return {"error": data.get("message", "API error")}

        return data

    except requests.exceptions.RequestException as error:
        return {"error": f"Could not connect to Twelve Data: {error}"}


HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Northline Markets</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #090e17;
    color: #e8edf5;
    font-family: Arial, sans-serif;
}

header {
    height: 75px;
    background: #101827;
    border-bottom: 1px solid #263348;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 35px;
}

.logo {
    font-size: 23px;
    font-weight: bold;
    letter-spacing: 1px;
}

.logo span {
    color: #42c99a;
}

.status {
    color: #42c99a;
    font-size: 13px;
}

.container {
    max-width: 1400px;
    margin: auto;
    padding: 30px;
}

h1 {
    font-size: 28px;
    margin-bottom: 8px;
}

.subtitle {
    color: #8996aa;
    margin-bottom: 25px;
}

.search-area {
    display: flex;
    gap: 10px;
    margin-bottom: 25px;
}

input {
    flex: 1;
    min-width: 0;
    background: #151f30;
    border: 1px solid #34435a;
    border-radius: 8px;
    padding: 15px;
    color: white;
    font-size: 15px;
    outline: none;
}

input:focus {
    border-color: #42c99a;
}

button {
    background: #42c99a;
    color: #07150f;
    border: none;
    padding: 13px 20px;
    border-radius: 7px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: .85;
}

.panel {
    background: #111a29;
    border: 1px solid #263348;
    border-radius: 12px;
    padding: 22px;
    margin-bottom: 22px;
}

.market-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin: 15px 0 25px;
}

.market-card {
    background: #111a29;
    border: 1px solid #263348;
    border-radius: 10px;
    padding: 18px;
    min-width: 0;
}

.market-symbol {
    color: #8996aa;
    font-size: 13px;
    margin-bottom: 8px;
}

.market-price {
    font-size: 23px;
    font-weight: bold;
    margin-bottom: 7px;
}

.market-change {
    font-size: 13px;
    font-weight: bold;
}

.stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 22px;
}

.stat {
    background: #111a29;
    border: 1px solid #263348;
    border-radius: 10px;
    padding: 20px;
    min-width: 0;
}

.stat-label {
    color: #8996aa;
    font-size: 13px;
    margin-bottom: 12px;
}

.stat-value {
    font-size: 23px;
    font-weight: bold;
    overflow-wrap: anywhere;
}

.green {
    color: #42c99a;
}

.red {
    color: #ff6878;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 20px;
}

.chart-buttons {
    display: flex;
    gap: 7px;
    flex-wrap: wrap;
}

.chart-buttons button {
    background: #202c3f;
    color: #dce5f1;
    padding: 9px 13px;
}

.chart-buttons button.active {
    background: #42c99a;
    color: #07150f;
}

.chart-container {
    height: 340px;
    position: relative;
}

.watchlist-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid #263348;
    gap: 10px;
}

.watchlist-item:last-child {
    border-bottom: none;
}

.small-button {
    padding: 8px 12px;
    font-size: 12px;
}

.message {
    color: #aab6c8;
    margin: 12px 0;
    font-size: 14px;
}

.error {
    color: #ff6878;
}

@media(max-width: 750px) {
    .market-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
    margin: 15px 0 25px;
}

.market-card {
    background: #111a29;
    border: 1px solid #263348;
    border-radius: 10px;
    padding: 18px;
    min-width: 0;
}

.market-symbol {
    color: #8996aa;
    font-size: 13px;
    margin-bottom: 8px;
}

.market-price {
    font-size: 23px;
    font-weight: bold;
    margin-bottom: 7px;
}

.market-change {
    font-size: 13px;
    font-weight: bold;
}

.stats {
        grid-template-columns: repeat(2, 1fr);
    }

    .container {
        padding: 18px;
    }

    header {
        padding: 0 18px;
    }

    .stat-value {
        font-size: 19px;
    }

    .chart-container {
        height: 260px;
    }
}
</style>
</head>

<body>

<header>
    <div class="logo">NORTHLINE <span>MARKETS</span></div>
    <div class="status">● MARKET DATA</div>
</header>

<div class="container">

    <h1>Market Dashboard</h1>
    <div class="subtitle">Track stocks, explore price movements, and build your watchlist.</div>

    <div class="panel">
        <div class="chart-header">
            <h2>Market Overview</h2>
            <span class="message">Market snapshot · ETFs tracking major indexes</span>
        </div>
        <div class="market-grid">
            <div class="market-card">
                <div class="market-symbol">SPY · S&amp;P 500 ETF</div>
                <div class="market-price" id="market-SPY">Loading...</div>
                <div class="market-change" id="market-change-SPY">--</div>
            </div>
            <div class="market-card">
                <div class="market-symbol">QQQ · Nasdaq-100 ETF</div>
                <div class="market-price" id="market-QQQ">Loading...</div>
                <div class="market-change" id="market-change-QQQ">--</div>
            </div>
            <div class="market-card">
                <div class="market-symbol">DIA · Dow Jones ETF</div>
                <div class="market-price" id="market-DIA">Loading...</div>
                <div class="market-change" id="market-change-DIA">--</div>
            </div>
        </div>
        <div id="market-message" class="message">Loading market data...</div>
    </div>

    <div class="search-area">
        <input id="symbolInput" placeholder="Search a stock symbol (AAPL, MSFT, NVDA)">
        <button onclick="searchStock()">Search</button>
    </div>

    <div id="message" class="message">Enter a stock symbol to get started.</div>

    <div class="stats">
        <div class="stat">
            <div class="stat-label">Stock Price</div>
            <div class="stat-value" id="price">--</div>
        </div>

        <div class="stat">
            <div class="stat-label">Daily Change</div>
            <div class="stat-value" id="change">--</div>
        </div>

        <div class="stat">
            <div class="stat-label">Daily High</div>
            <div class="stat-value" id="high">--</div>
        </div>

        <div class="stat">
            <div class="stat-label">Daily Low</div>
            <div class="stat-value" id="low">--</div>
        </div>
    </div>

    <div class="panel">
        <div class="chart-header">
            <div>
                <h2 id="companyName">Stock Chart</h2>
                <div id="companySymbol" class="subtitle"></div>
            </div>

            <div class="chart-buttons">
                <button class="active" onclick="loadHistory('1D', this)">1D</button>
                <button onclick="loadHistory('1W', this)">1W</button>
                <button onclick="loadHistory('1M', this)">1M</button>
                <button onclick="loadHistory('1Y', this)">1Y</button>
            </div>
        </div>

        <div class="chart-container">
            <canvas id="stockChart"></canvas>
        </div>
    </div>

    <div class="panel">
        <div class="chart-header">
            <h2>My Watchlist</h2>
            <button onclick="addToWatchlist()" class="small-button">+ Add Current Stock</button>
        </div>

        <div id="watchlist">
            <div class="message">Your watchlist is empty.</div>
        </div>
    </div>

</div>

<script>
let currentSymbol = "";
let stockChart = null;
let watchlist = [];

const money = value => {
    const number = Number(value);
    return Number.isFinite(number)
        ? "$" + number.toFixed(2)
        : "--";
};

async function loadMarketOverview() {
    const symbols = ["SPY", "QQQ", "DIA"];
    const message = document.getElementById("market-message");

    try {
        const response = await fetch("/api/market");
        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Market data could not be loaded.");
        }

        symbols.forEach(symbol => {
            const quote = data[symbol];
            const priceElement = document.getElementById("market-" + symbol);
            const changeElement = document.getElementById("market-change-" + symbol);

            if (!quote || quote.error) {
                priceElement.textContent = "Unavailable";
                changeElement.textContent = quote && quote.error ? quote.error : "--";
                changeElement.className = "market-change";
                return;
            }

            priceElement.textContent = money(quote.close);

            const change = Number(quote.change);
            const percent = Number(quote.percent_change);

            if (Number.isFinite(change) && Number.isFinite(percent)) {
                const sign = change > 0 ? "+" : "";
                changeElement.textContent =
                    sign + change.toFixed(2) + " (" + sign + percent.toFixed(2) + "%)";
                changeElement.className =
                    "market-change " + (change >= 0 ? "green" : "red");
            } else {
                changeElement.textContent = "--";
                changeElement.className = "market-change";
            }
        });

        message.textContent = "Market snapshot loaded from Twelve Data.";
    } catch (error) {
        message.textContent = error.message;
        message.className = "message error";
        symbols.forEach(symbol => {
            document.getElementById("market-" + symbol).textContent = "--";
            document.getElementById("market-change-" + symbol).textContent = "Unavailable";
        });
    }
}

function showMessage(message, isError = false) {
    const element = document.getElementById("message");
    element.textContent = message;
    element.className = isError ? "message error" : "message";
}

async function searchStock() {
    const symbol = document.getElementById("symbolInput").value.trim().toUpperCase();

    if (!symbol) {
        showMessage("Please enter a stock symbol.", true);
        return;
    }

    currentSymbol = symbol;
    showMessage("Loading stock information...");

    try {
        const response = await fetch("/api/quote?symbol=" + encodeURIComponent(symbol));
        const data = await response.json();

        if (data.error) {
            showMessage(data.error, true);
            return;
        }

        document.getElementById("price").textContent = money(data.close);

        const change = Number(data.change);
        const changeElement = document.getElementById("change");

        if (Number.isFinite(change)) {
            changeElement.textContent =
                (change > 0 ? "+" : "") + change.toFixed(2) +
                " (" + Number(data.percent_change).toFixed(2) + "%)";

            changeElement.className = "stat-value " +
                (change >= 0 ? "green" : "red");
        } else {
            changeElement.textContent = "--";
            changeElement.className = "stat-value";
        }

        document.getElementById("high").textContent = money(data.high);
        document.getElementById("low").textContent = money(data.low);

        document.getElementById("companyName").textContent =
            data.name || symbol;

        document.getElementById("companySymbol").textContent =
            symbol + " · " + (data.exchange || "Stock");

        showMessage("Showing quote information for " + symbol + ".");
        loadHistory("1D");

    } catch (error) {
        showMessage("Something went wrong while loading this stock.", true);
    }
}

async function loadHistory(period, clickedButton = null) {
    if (!currentSymbol) return;

    if (clickedButton) {
        document.querySelectorAll(".chart-buttons button").forEach(button => {
            button.classList.remove("active");
        });
        clickedButton.classList.add("active");
    } else {
        document.querySelectorAll(".chart-buttons button").forEach(button => {
            button.classList.toggle(
                "active",
                button.textContent.trim() === period
            );
        });
    }

    try {
        const response = await fetch(
            "/api/history?symbol=" + encodeURIComponent(currentSymbol) +
            "&period=" + encodeURIComponent(period)
        );

        const data = await response.json();

        if (data.error) {
            showMessage(data.error, true);
            return;
        }

        if (!data.values || data.values.length === 0) {
            showMessage("No chart data was returned for this time range.", true);
            return;
        }

        const labels = data.values.map(item => item.datetime);
        const prices = data.values.map(item => Number(item.close));

        const ctx = document.getElementById("stockChart").getContext("2d");

        if (stockChart) {
            stockChart.destroy();
        }

        stockChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [{
                    label: currentSymbol + " Price",
                    data: prices,
                    borderColor: "#42c99a",
                    backgroundColor: "rgba(66, 201, 154, 0.12)",
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.25
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: "index"
                },
                plugins: {
                    legend: {
                        labels: {
                            color: "#dce5f1"
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: "#8996aa",
                            maxTicksLimit: 8
                        },
                        grid: {
                            color: "#202c3f"
                        }
                    },
                    y: {
                        ticks: {
                            color: "#8996aa",
                            callback: value => "$" + value
                        },
                        grid: {
                            color: "#202c3f"
                        }
                    }
                }
            }
        });

    } catch (error) {
        showMessage("Could not load chart information.", true);
    }
}

function addToWatchlist() {
    if (!currentSymbol) {
        showMessage("Search for a stock before adding it.", true);
        return;
    }

    if (watchlist.includes(currentSymbol)) {
        showMessage("That stock is already in your watchlist.");
        return;
    }

    watchlist.push(currentSymbol);
    renderWatchlist();
    showMessage(currentSymbol + " added to your watchlist.");
}

function removeFromWatchlist(symbol) {
    watchlist = watchlist.filter(item => item !== symbol);
    renderWatchlist();
}

function renderWatchlist() {
    const container = document.getElementById("watchlist");
    container.innerHTML = "";

    if (watchlist.length === 0) {
        container.textContent = "Your watchlist is empty.";
        container.className = "message";
        return;
    }

    container.className = "";

    watchlist.forEach(symbol => {
        const row = document.createElement("div");
        row.className = "watchlist-item";

        const name = document.createElement("strong");
        name.textContent = symbol;

        const actions = document.createElement("div");

        const viewButton = document.createElement("button");
        viewButton.className = "small-button";
        viewButton.textContent = "View";
        viewButton.onclick = () => {
            document.getElementById("symbolInput").value = symbol;
            searchStock();
        };

        const removeButton = document.createElement("button");
        removeButton.className = "small-button";
        removeButton.style.marginLeft = "8px";
        removeButton.style.background = "#34435a";
        removeButton.style.color = "white";
        removeButton.textContent = "Remove";
        removeButton.onclick = () => removeFromWatchlist(symbol);

        actions.appendChild(viewButton);
        actions.appendChild(removeButton);
        row.appendChild(name);
        row.appendChild(actions);
        container.appendChild(row);
    });
}

loadMarketOverview();

document.getElementById("symbolInput").addEventListener("keydown", event => {
    if (event.key === "Enter") {
        searchStock();
    }
});
</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/market")
def market():
    if API_KEY == "PASTE_YOUR_NEW_TWELVE_DATA_API_KEY_HERE":
        return jsonify({
            "error": "Add your new Twelve Data API key near the top of app.py first."
        }), 400

    results = {}
    for symbol in ("SPY", "QQQ", "DIA"):
        quote_data = get_data("quote", {"symbol": symbol})
        results[symbol] = quote_data

    return jsonify(results)


@app.route("/api/quote")
def quote():
    if API_KEY == "PASTE_YOUR_NEW_TWELVE_DATA_API_KEY_HERE":
        return jsonify({
            "error": "Add your Twelve Data API key near the top of app.py first."
        }), 400

    symbol = request.args.get("symbol", "").strip().upper()

    if not symbol:
        return jsonify({"error": "Enter a stock symbol."}), 400

    data = get_data("quote", {"symbol": symbol})

    if "error" in data:
        return jsonify(data), 400

    return jsonify(data)


@app.route("/api/history")
def history():
    if API_KEY == "PASTE_YOUR_NEW_TWELVE_DATA_API_KEY_HERE":
        return jsonify({"error": "Add your Twelve Data API key first."}), 400

    symbol = request.args.get("symbol", "").strip().upper()
    period = request.args.get("period", "1D")

    settings = {
        "1D": {"interval": "5min", "outputsize": 78},
        "1W": {"interval": "15min", "outputsize": 130},
        "1M": {"interval": "1day", "outputsize": 30},
        "1Y": {"interval": "1week", "outputsize": 52}
    }

    if period not in settings:
        return jsonify({"error": "Invalid chart time range."}), 400

    if not symbol:
        return jsonify({"error": "Enter a stock symbol."}), 400

    params = {
        "symbol": symbol,
        "interval": settings[period]["interval"],
        "outputsize": settings[period]["outputsize"],
        "order": "ASC"
    }

    data = get_data("time_series", params)

    if "error" in data:
        return jsonify(data), 400

    return jsonify(data)


if __name__ == "__main__":
    print("\nNORTHLINE MARKETS")
    print("Open http://127.0.0.1:5000 in your browser.")
    app.run(host="127.0.0.1", port=5000, debug=False)
