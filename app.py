from flask import Flask, jsonify, render_template_string, abort, request
from datetime import datetime, timezone
import requests, os, time, math, random

app = Flask(__name__)
API_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")
BASE = "https://api.twelvedata.com"

# Only these symbols can be requested (stops people burning your API credits)
SYMBOLS = {
    "SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF", "DIA": "Dow Jones ETF",
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMZN": "Amazon", "TSLA": "Tesla",
    "XAU/USD": "Gold", "XAG/USD": "Silver", "XPT/USD": "Platinum", "XPD/USD": "Palladium",
    "GLD": "Gold ETF", "SLV": "Silver ETF",
}
METALS = ["XAU/USD", "XAG/USD", "XPT/USD", "XPD/USD"]
STOCKS = ["SPY", "QQQ", "DIA", "AAPL", "MSFT", "NVDA", "AMZN", "TSLA"]
DEMO_BASE = {"SPY": 590, "QQQ": 510, "DIA": 430, "AAPL": 230, "MSFT": 430, "NVDA": 140, "AMZN": 200,
             "TSLA": 330, "XAU/USD": 2650, "XAG/USD": 31, "XPT/USD": 960, "XPD/USD": 980, "GLD": 245, "SLV": 28}
RANGES = {  # label: (interval, bars)
    "1D": ("5min", 78), "1W": ("30min", 65), "1M": ("1day", 22), "3M": ("1day", 66), "1Y": ("1day", 252)}

QUOTE_CACHE, HIST_CACHE = {}, {}
QUOTE_TTL, HIST_TTL = 60, 300

LESSONS = {
 "stocks": [
  {"id": "s1", "title": "What a stock really is",
   "body": "A share is a small slice of ownership in a company. You make money if the company's value grows (price gain) or if it pays dividends. You lose money if the value falls. An index like the S&P 500 is a basket of many companies, and an ETF such as SPY lets you buy that whole basket in one trade.",
   "q": "Which best describes an ETF like SPY?", "o": ["One company's stock", "A basket of many stocks traded like one share", "A loan to the government"], "a": 1},
  {"id": "s2", "title": "Reading a candlestick chart",
   "body": "Each candle covers one period (a day, an hour). The body runs from open to close, green when price rose and red when it fell. The thin wicks show the highest and lowest prices. Volume shows how many shares changed hands, and big moves on high volume carry more weight than moves on thin volume.",
   "q": "What do a candle's wicks show?", "o": ["The open and close", "The high and low of the period", "The trading volume"], "a": 1},
  {"id": "s3", "title": "Risk and position sizing",
   "body": "Decide what you can lose before you buy. A common rule is to risk 1% or less of your account on one trade. Position size = (account x risk %) / (entry price - stop price). Use the Position Size calculator in Tools to try it. Diversifying across several holdings keeps one bad bet from sinking the account.",
   "q": "You have $10,000, risk 1%, entry $50, stop $48. How many shares?", "o": ["50", "100", "200"], "a": 0},
  {"id": "s4", "title": "Valuation basics: the P/E ratio",
   "body": "Price-to-earnings divides the share price by yearly profit per share. A P/E of 20 means you pay $20 for each $1 of annual profit. High P/E often means the market expects fast growth, low P/E can mean cheap or troubled. Compare a company with its own history and its industry, not with everything.",
   "q": "A stock trades at $100 and earns $5 per share a year. What is its P/E?", "o": ["5", "20", "500"], "a": 1},
 ],
 "metals": [
  {"id": "m1", "title": "Why gold and silver move",
   "body": "Gold tends to rise when real interest rates fall, when the US dollar weakens, or when investors fear financial or political stress. It pays no interest, so higher rates make holding it less attractive. Silver follows gold but is also an industrial metal (solar panels, electronics), so it swings harder.",
   "q": "Which usually helps gold prices rise?", "o": ["Rising real interest rates", "A weaker US dollar", "Falling investor fear"], "a": 1},
  {"id": "m2", "title": "The gold/silver ratio",
   "body": "The ratio is the gold price divided by the silver price: how many ounces of silver buy one ounce of gold. Some investors treat a very high ratio as a sign silver is cheap relative to gold, and a low one the reverse. It is a reference point, not a guarantee, and it can stay extreme for years.",
   "q": "Gold is $2,600 and silver is $32. What is the ratio?", "o": ["About 81", "About 8", "About 810"], "a": 0},
  {"id": "m3", "title": "Ways to own precious metals",
   "body": "Physical coins and bars give direct ownership but come with dealer premiums, storage and insurance costs. ETFs like GLD and SLV track the price with easy trading but you own shares, not metal in your hand. Mining stocks add company risk and can move much more than the metal itself. Futures use heavy leverage and are for experienced traders.",
   "q": "Which option carries company-specific risk?", "o": ["Physical bars", "Gold mining stocks", "A gold ETF holding bullion"], "a": 1},
  {"id": "m4", "title": "Spot price vs what you pay",
   "body": "The spot price is the live wholesale price of one troy ounce (31.1 grams). Retail coins and bars sell above spot (the premium) and dealers buy below it (the spread). Small coins carry higher premiums per ounce than large bars. Always compare total cost, not only the headline price.",
   "q": "Why do you usually pay more than spot for a coin?", "o": ["Premium over spot", "Spot is always wrong", "Coins weigh less"], "a": 0},
 ],
}
GLOSSARY = [
 ("Ask / Bid", "The lowest price a seller accepts (ask) and the highest a buyer offers (bid). The gap is the spread."),
 ("Bull / Bear market", "A sustained rise (bull) or fall (bear), commonly defined as 20% from a recent peak or low."),
 ("Diversification", "Spreading money across different assets so one failure hurts less."),
 ("Dividend", "A share of company profit paid to stockholders."),
 ("ETF", "A fund that trades like a stock and holds a basket of assets."),
 ("Limit order", "An order to buy or sell only at your price or better."),
 ("Market order", "An order to trade right now at the best available price."),
 ("Premium", "How much a coin or bar costs above the spot price of its metal."),
 ("Spot price", "The current market price for immediate delivery of a metal."),
 ("Stop loss", "An order that sells when price falls to a level you choose, to cap a loss."),
 ("Troy ounce", "The unit for precious metals: 31.1035 grams, heavier than a regular ounce."),
 ("Volatility", "How much and how fast a price moves."),
]
PAGES = [("home", "/", "Overview"), ("stocks", "/stocks", "Stocks"), ("metals", "/metals", "Precious metals"),
         ("watch", "/watchlist", "Watchlist"), ("paper", "/paper-trading", "Paper trading"),
         ("learn", "/learn", "Learn"), ("tools", "/tools", "Tools"), ("glossary", "/glossary", "Glossary")]

# ---------------- data helpers ----------------
def demo_quote(sym):
    base = DEMO_BASE.get(sym, 100)
    rnd = random.Random(sym + datetime.now().strftime("%Y%m%d%H"))
    pct = rnd.uniform(-1.5, 1.5)
    return {"price": round(base * (1 + pct / 100), 2), "pct": round(pct, 2)}


def fetch_quotes(symbols):
    now, out, missing = time.time(), {}, []
    used_demo = False

    # Check cached prices first.
    for s in symbols:
        c = QUOTE_CACHE.get(s)
        if c and now - c["t"] < QUOTE_TTL:
            out[s] = c["d"]
        else:
            missing.append(s)

    # Use sample prices if no API key is configured.
    if missing and not API_KEY:
        for s in missing:
            out[s] = demo_quote(s)
        return out, True

    # Try to retrieve live prices.
    if missing:
        try:
            response = requests.get(
                BASE + "/quote",
                params={
                    "symbol": ",".join(missing),
                    "apikey": API_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if len(missing) == 1:
                data = {missing[0]: data}

            for s in missing:
                d = data.get(s, {})

                if isinstance(d, dict) and "close" in d:
                    q = {
                        "price": round(float(d["close"]), 2),
                        "pct": round(float(d.get("percent_change") or 0), 2)
                    }
                    QUOTE_CACHE[s] = {"d": q, "t": now}
                    out[s] = q
                else:
                    out[s] = demo_quote(s)
                    used_demo = True

        except (requests.RequestException, ValueError, TypeError):
            for s in missing:
                out[s] = demo_quote(s)
            used_demo = True

    return out, used_demo


def demo_history(sym, bars, intraday):
    rnd = random.Random(sym)
    price, rows, step = DEMO_BASE.get(sym, 100) * 0.92, [], 300 if intraday else 86400
    t = int(time.time()) // step * step - bars * step
    for _ in range(bars):
        o = price
        c = o * (1 + rnd.uniform(-0.012, 0.0125))
        rows.append({"time": t, "open": round(o, 2), "high": round(max(o, c) * 1.004, 2),
                     "low": round(min(o, c) * 0.996, 2), "close": round(c, 2)})
        price, t = c, t + step
    return rows

def to_time(s):
    if len(s) <= 10:
        return s
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())

# ---------------- routes ----------------
@app.route("/api/quotes/<group>")
def quotes(group):
    if group == "custom":
        syms = [x for x in request.args.get("s", "").split(",") if x in SYMBOLS][:12]
    else:
        syms = {"stocks": STOCKS, "metals": METALS, "ticker": STOCKS[3:] + METALS}.get(group)
    if not syms:
        abort(404)
    data, demo = fetch_quotes(syms)
    return jsonify({"quotes": data, "names": {s: SYMBOLS[s] for s in syms}, "demo": demo})

@app.route("/api/history/<path:symbol>/<rng>")
def history(symbol, rng):
    symbol = symbol.upper()
    if symbol not in SYMBOLS or rng not in RANGES:
        return jsonify({"error": "Unknown symbol or range"}), 400
    interval, bars = RANGES[rng]
    key = (symbol, rng)
    c = HIST_CACHE.get(key)
    if c and time.time() - c["t"] < HIST_TTL:
        return jsonify(c["d"])
    if not API_KEY:
        return jsonify({"values": demo_history(symbol, bars, interval != "1day"), "demo": True})
    try:
        r = requests.get(BASE + "/time_series", params={"symbol": symbol, "interval": interval,
                         "outputsize": bars, "apikey": API_KEY}, timeout=10).json()
        if "values" not in r:
            return jsonify({"error": r.get("message", "Data unavailable")}), 502
        rows = {}
        for v in r["values"]:
            t = to_time(v["datetime"])
            rows[t] = {"time": t, "open": float(v["open"]), "high": float(v["high"]),
                       "low": float(v["low"]), "close": float(v["close"])}
        d = {"values": [rows[k] for k in sorted(rows, key=str)], "demo": False}
        HIST_CACHE[key] = {"d": d, "t": time.time()}
        return jsonify(d)
    except (requests.RequestException, ValueError):
        return jsonify({"error": "Market data service unavailable"}), 502

def page(name):
    return render_template_string(HTML, page=name, pages=PAGES, lessons=LESSONS, glossary=GLOSSARY,
                                  symbols=SYMBOLS, stocks=STOCKS, metals=METALS)

@app.route("/")
def home(): return page("home")
@app.route("/stocks")
def stocks_page(): return page("stocks")
@app.route("/metals")
def metals_page(): return page("metals")
@app.route("/learn")
def learn_page(): return page("learn")
@app.route("/tools")
def tools_page(): return page("tools")
@app.route("/glossary")
def glossary_page(): return page("glossary")
@app.route("/watchlist")
def watch_page(): return page("watch")
@app.route("/paper-trading")
def paper_page(): return page("paper")

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Northline Markets: learn stocks and precious metals</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#0f1318;--panel:#171d25;--line:#2a323d;--text:#e8e4da;--muted:#98a1ad;--gold:#d9a93f;--silver:#b8c2cf;
--up:#43b88c;--down:#e26a63;--blue:#6aa7e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 Inter,Arial,sans-serif}
h1,h2,h3{font-family:Fraunces,Georgia,serif;line-height:1.2;margin:0 0 .5em}
h1{font-size:34px}h2{font-size:22px}h3{font-size:17px}
a{color:var(--gold)}
:focus-visible{outline:2px solid var(--gold);outline-offset:2px}
header{border-bottom:1px solid var(--line);background:#12171d}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.bar{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:14px 0}
.logo{font:700 22px Fraunces,Georgia,serif;color:var(--gold);text-decoration:none}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{color:var(--muted);text-decoration:none;padding:8px 13px;border-radius:6px}
nav a:hover{color:var(--text)}nav a.on{background:#232c38;color:var(--text)}
.ticker{display:flex;gap:28px;overflow-x:auto;padding:10px 0;white-space:nowrap;border-top:1px solid var(--line)}
.tk b{font-weight:600;margin-right:8px}.tk small{color:var(--muted)}
main{padding:34px 0 50px}
.lead{color:var(--muted);max-width:62ch;font-size:16px;margin-bottom:26px}
.grid{display:grid;gap:16px}.g4{grid-template-columns:repeat(4,1fr)}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:20px}
.q span{color:var(--muted);font-size:13px}.q .p{font:600 26px Fraunces,Georgia,serif;margin-top:4px}
.q .c{font-size:13px}.up{color:var(--up)}.down{color:var(--down)}
.metal{border-top:3px solid var(--gold)}.metal.ag{border-top-color:var(--silver)}
.chartbar{display:flex;gap:10px;justify-content:space-between;flex-wrap:wrap;margin-bottom:12px}
select,input,button{font:inherit;background:#0f1318;color:var(--text);border:1px solid var(--line);border-radius:6px;padding:8px 12px}
button{cursor:pointer}button:hover{border-color:var(--gold)}button.on{background:var(--gold);color:#1a1405;border-color:var(--gold)}
.tf{display:flex;gap:6px}
.note{font-size:12.5px;color:var(--muted)}
.banner{background:#2a2412;border:1px solid #5b4a1a;color:#e9d28f;padding:10px 14px;border-radius:6px;margin-bottom:18px;font-size:13.5px}
.lesson summary{cursor:pointer;font:600 17px Fraunces,Georgia,serif;list-style:none;display:flex;justify-content:space-between;gap:10px}
.lesson summary::after{content:"+";color:var(--gold)}.lesson[open] summary::after{content:"\\2212"}
.lesson .done{color:var(--up);font:600 12px Inter}
.opt{display:block;width:100%;text-align:left;margin:6px 0}
.opt.right{border-color:var(--up);color:var(--up)}.opt.wrong{border-color:var(--down);color:var(--down)}
.prog{height:6px;background:#232c38;border-radius:4px;overflow:hidden;margin:6px 0 24px}.prog i{display:block;height:100%;background:var(--gold);width:0}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}input{width:100%}
.out{margin-top:14px;font:600 19px Fraunces,Georgia,serif;color:var(--gold)}
dl{margin:0}dt{font-weight:600;margin-top:14px}dd{margin:2px 0 0;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:22px 0 40px;color:var(--muted);font-size:12.5px}
@media(max-width:900px){.g4,.g3{grid-template-columns:1fr 1fr}.g2{grid-template-columns:1fr}}
@media(max-width:520px){.g4,.g3{grid-template-columns:1fr}h1{font-size:28px}}
.pill{font-size:12px;font-weight:600;padding:3px 10px;border:1px solid currentColor;border-radius:20px}
.ticker{overflow:hidden}.track{display:inline-flex;gap:28px;animation:scroll 80s linear infinite}.ticker:hover .track{animation-play-state:paused}
@keyframes scroll{to{transform:translateX(-50%)}}
@media(prefers-reduced-motion:reduce){.track{animation:none}.ticker{overflow-x:auto}}
.tbl{width:100%;border-collapse:collapse;font-size:14px}.tbl th{font-weight:500;color:var(--muted);text-align:left;padding:12px 16px;border-bottom:1px solid var(--line);font-size:12.5px}
.tbl td{padding:12px 16px;border-bottom:1px solid #1f2630}.tbl tr[data-s]{cursor:pointer}.tbl tr[data-s]:hover{background:#1c2430}
.tbl .r{text-align:right;font-variant-numeric:tabular-nums}
#chart-head{font:600 26px Fraunces,Georgia,serif;margin-bottom:8px}#chart-head small{font:500 14px Inter,Arial,sans-serif}
</style>
<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>
</head>
<body>
<header><div class="wrap">
 <div class="bar"><div style="display:flex;align-items:center;gap:12px"><a class="logo" href="/">Northline Markets</a><span id="mkt" class="pill"></span></div>
 <nav aria-label="Main">{% for k,u,l in pages %}<a href="{{u}}" class="{{'on' if k==page}}">{{l}}</a>{% endfor %}</nav></div>
 <div class="ticker" id="ticker" aria-label="Live prices"></div>
</div></header>
<main><div class="wrap">
<div id="demo-banner" class="banner" hidden>
  Showing sample prices because live market data is unavailable. Prices are for demonstration only.
</div>

{% if page == 'home' %}
<h1>Learn to invest in stocks and precious metals</h1>
<p class="lead">Follow live prices, practice with free calculators, and work through short lessons on how stocks, gold and silver actually work.</p>
<div class="grid g4" id="home-q"></div>
<div class="grid g2" style="margin-top:16px">
 <div class="panel"><h2>Start learning</h2><p class="note">Eight short lessons, each with a quick quiz. Your progress is saved in this browser.</p>
  <div class="prog"><i id="prog-home"></i></div><a href="/learn">Open the lessons</a></div>
 <div class="panel"><h2>Gold/silver ratio</h2><div class="out" id="ratio">Loading</div>
  <p class="note">Ounces of silver needed to buy one ounce of gold. <a href="/learn">What does it mean?</a></p></div>
</div>
<div class="panel" style="margin-top:16px"><h2>Chart</h2>{% include_chart %}</div>
<div class="grid g2" style="margin-top:16px"><div><h2>Stocks and ETFs</h2><div class="panel" style="padding:0;overflow-x:auto"><table class="tbl" data-group="stocks"></table></div></div><div><h2>Precious metals</h2><div class="panel" style="padding:0;overflow-x:auto"><table class="tbl" data-group="metals"></table></div></div></div>

{% elif page == 'stocks' %}
<h1>Stocks and ETFs</h1><p class="lead">Major indexes and popular companies. Click a symbol to chart it.</p>
<div class="panel" style="padding:0;overflow-x:auto"><table class="tbl" data-group="stocks"></table></div>
<div class="panel" style="margin-top:16px"><h2>Chart</h2>{% include_chart %}</div>

{% elif page == 'metals' %}
<h1>Precious metals</h1><p class="lead">Spot prices per troy ounce in US dollars.</p>
<div class="panel" style="padding:0;overflow-x:auto"><table class="tbl" data-group="metals"></table></div>
<div class="grid g2" style="margin-top:16px">
 <div class="panel"><h2>Gold/silver ratio</h2><div class="out" id="ratio">Loading</div>
 <p class="note">Gold price divided by silver price.</p></div>
 <div class="panel"><h2>Before you buy</h2><p class="note">Coins and bars sell above spot (the premium) and dealers buy below it. Compare total cost, storage and insurance. ETFs such as GLD and SLV are a no-storage alternative.</p></div>
</div>
<div class="panel" style="margin-top:16px"><h2>Chart</h2>{% include_chart %}</div>

{% elif page == 'watch' %}
<h1>Watchlist</h1><p class="lead">Track the symbols you care about. Your list is saved in this browser.</p>
<div class="panel"><div class="chartbar"><select id="w-sel" aria-label="Symbol">{% for s,l in symbols.items() %}<option value="{{s}}">{{l}} ({{s}})</option>{% endfor %}</select><button type="button" id="w-add" class="on">Add to watchlist</button></div>
<div style="overflow-x:auto"><table class="tbl"><thead><tr><th>Symbol</th><th>Name</th><th class="r">Price</th><th class="r">Change</th><th></th></tr></thead><tbody id="w-body"></tbody></table></div><p class="note" id="w-empty"></p></div>


{% elif page == 'paper' %}
<div class="paper-terminal">

  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:22px">
    <div>
      <div class="note" style="letter-spacing:2px">NORTHLINE MARKETS / SIMULATOR</div>
      <h1 style="margin:5px 0">Paper Trading</h1>
      <p class="lead">Professional trading simulator · Virtual account</p>
    </div>
    <div class="panel" style="padding:12px 18px">
      <span class="note">ACCOUNT STATUS</span>
      <div style="font-weight:700;color:#35c98b">● SIMULATION ACTIVE</div>
    </div>
  </div>

  <div class="grid g4" id="pt-sum"></div>

  <div class="grid g2" style="margin-top:20px;align-items:start">

    <div class="panel">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <h2>Order Entry</h2>
        <span class="note">MARKET ORDER</span>
      </div>

      <label for="pt-sym">Select asset</label>
      <select id="pt-sym" style="width:100%">
        {% for s,l in symbols.items() %}
        <option value="{{s}}">{{l}} ({{s}})</option>
        {% endfor %}
      </select>

      <label for="pt-qty">Share quantity</label>
      <input id="pt-qty" type="number" value="10" min="1" step="1" style="width:100%">

      <div class="panel" style="margin-top:16px;background:rgba(255,255,255,.025)">
        <div class="note">ESTIMATED ORDER VALUE</div>
        <div id="pt-estimate" style="font-size:25px;font-weight:700;margin-top:6px">--</div>
        <div class="note" id="pt-order-info">Select an asset to preview your order.</div>
      </div>

      <div style="display:flex;gap:10px;margin-top:18px">
        <button type="button" id="pt-buy" class="on" style="flex:1">BUY</button>
        <button type="button" id="pt-sell" style="flex:1">SELL</button>
      </div>

      <p class="note" id="pt-msg" aria-live="polite"></p>

      <button type="button" id="pt-reset" style="width:100%;margin-top:10px">
        Reset simulated account
      </button>
    </div>

    <div class="panel">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:10px">
        <h2>Open Positions</h2>
        <span class="note" id="pt-position-count">0 POSITIONS</span>
      </div>

      <div style="overflow-x:auto">
        <table class="tbl">
          <thead>
            <tr>
              <th>Asset</th>
              <th class="r">Shares</th>
              <th class="r">Avg. cost</th>
              <th class="r">Last price</th>
              <th class="r">Market value</th>
              <th class="r">P/L</th>
            </tr>
          </thead>
          <tbody id="pt-body"></tbody>
        </table>
      </div>
      <p class="note" style="margin-top:12px">Positions are simulated and saved in this browser.</p>
    </div>

  </div>

  <div class="panel" style="margin-top:20px">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
      <div>
        <h2>Trading Activity</h2>
        <p class="note">Your recent simulated orders will appear here.</p>
      </div>
      <span class="note">ORDER HISTORY</span>
    </div>

    <div style="overflow-x:auto">
      <table class="tbl">
        <thead>
          <tr>
            <th>Asset</th>
            <th>Side</th>
            <th class="r">Quantity</th>
            <th class="r">Execution price</th>
            <th class="r">Order value</th>
            <th class="r">Time</th>
          </tr>
        </thead>
        <tbody id="pt-history">
          <tr><td colspan="6" class="note">Your trading activity will appear here.</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <p class="note" style="margin-top:16px">
    Paper trading uses virtual money only. Orders are simulated and do not execute in real financial markets. Market prices may be delayed or unavailable.
  </p>

</div>



{% elif page == 'learn' %}
<h1>Learn</h1><p class="lead">Read each lesson, then answer the question. Take your time: understanding risk matters more than finding a trade.</p>
<div class="prog"><i id="prog"></i></div>
{% for track,title in [('stocks','Stock market track'),('metals','Precious metals track')] %}
<h2 style="margin-top:28px">{{title}}</h2>
<div class="grid">{% for l in lessons[track] %}
 <details class="panel lesson" data-id="{{l.id}}"><summary><span>{{l.title}}</span><span class="done" hidden>Completed</span></summary>
  <p>{{l.body}}</p><h3>{{l.q}}</h3>
  {% for o in l.o %}<button class="opt" data-ans="{{l.a}}" data-i="{{loop.index0}}">{{o}}</button>{% endfor %}
  <p class="note fb"></p></details>{% endfor %}</div>
{% endfor %}

{% elif page == 'tools' %}
<h1>Tools</h1><p class="lead">Calculators that run in your browser. Nothing you type is sent anywhere.</p>
<div class="grid g2">
 <div class="panel"><h2>Position size</h2>
  <label>Account size ($)</label><input id="ps-acc" type="number" value="10000">
  <label>Risk per trade (%)</label><input id="ps-risk" type="number" value="1" step="0.1">
  <label>Entry price ($)</label><input id="ps-entry" type="number" value="50" step="0.01">
  <label>Stop price ($)</label><input id="ps-stop" type="number" value="48" step="0.01">
  <div class="out" id="ps-out"></div></div>
 <div class="panel"><h2>Compound growth</h2>
  <label>Starting amount ($)</label><input id="cg-start" type="number" value="5000">
  <label>Added each month ($)</label><input id="cg-add" type="number" value="200">
  <label>Yearly return (%)</label><input id="cg-rate" type="number" value="7" step="0.1">
  <label>Years</label><input id="cg-years" type="number" value="20">
  <div class="out" id="cg-out"></div><p class="note">An example, not a forecast. Real returns vary every year.</p></div>
 <div class="panel"><h2>Gold/silver ratio</h2>
  <label>Gold price ($/oz)</label><input id="gs-g" type="number" value="2600">
  <label>Silver price ($/oz)</label><input id="gs-s" type="number" value="32" step="0.01">
  <div class="out" id="gs-out"></div></div>
 <div class="panel"><h2>Ounces, grams, value</h2>
  <label>Weight in troy ounces</label><input id="oz-oz" type="number" value="1" step="0.01">
  <label>Metal price ($/oz)</label><input id="oz-p" type="number" value="2600">
  <div class="out" id="oz-out"></div></div>
</div>

{% elif page == 'glossary' %}
<h1>Glossary</h1><p class="lead">Plain-language definitions of terms you will see everywhere.</p>
<input id="gsearch" placeholder="Search terms" style="max-width:340px" aria-label="Search glossary">
<dl id="gl">{% for t,d in glossary %}<div class="gi"><dt>{{t}}</dt><dd>{{d}}</dd></div>{% endfor %}</dl>
{% endif %}
</div></main>
<footer><div class="wrap">Northline Markets is for education only and is not financial advice. Prices may be delayed or sample data. Investing involves risk, including loss of money. Past performance does not predict future results.</div></footer>

<script>
const fmt = n => "$" + Number(n).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
const cls = p => p >= 0 ? "up" : "down";
const sgn = p => (p >= 0 ? "+" : "") + p.toFixed(2) + "%";
const $ = id => document.getElementById(id);
async function getQuotes(group){
  try{ const r = await fetch("/api/quotes/" + group); const j = await r.json();
    if(j.demo) $("demo-banner").hidden = false; return j; }catch(e){ return {quotes:{}, names:{}}; }
}
function card(s, j){
  const q = j.quotes[s], m = s.indexOf("/") > -1, ag = s.startsWith("XAG");
  const price = q ? fmt(q.price) : "Unavailable";
  const chg = q ? '<div class="c ' + cls(q.pct) + '">' + sgn(q.pct) + "</div>" : "";
  return '<div class="panel q ' + (m ? "metal " + (ag ? "ag" : "") : "") + '"><span>' + j.names[s] + " (" + s + ")</span><div class='p'>" + price + "</div>" + chg + "</div>";
}
(async () => {
  const t = await getQuotes("ticker");
  $("ticker").innerHTML = Object.keys(t.quotes).map(s => '<span class="tk"><b>' + s.replace("/USD","") + "</b>" + fmt(t.quotes[s].price) + ' <small class="' + cls(t.quotes[s].pct) + '">' + sgn(t.quotes[s].pct) + "</small></span>").join("");
  $("ticker").innerHTML = '<div class="track">' + $("ticker").innerHTML + $("ticker").innerHTML + "</div>";
  for(const tb of document.querySelectorAll("table[data-group]")){
    const j = await getQuotes(tb.dataset.group);
    tb.innerHTML = '<thead><tr><th>Symbol</th><th>Name</th><th class="r">Price</th><th class="r">Change</th></tr></thead><tbody>' +
      Object.keys(j.names).map(s => { const q = j.quotes[s];
        return '<tr data-s="' + s + '"><td><b>' + s.replace("/USD","") + "</b></td><td>" + j.names[s] + '</td><td class="r">' + (q ? fmt(q.price) : "n/a") + '</td><td class="r ' + (q ? cls(q.pct) : "") + '">' + (q ? sgn(q.pct) : "") + "</td></tr>"; }).join("") + "</tbody>";
    tb.querySelectorAll("tr[data-s]").forEach(r => r.addEventListener("click", () => {
      const sel = $("chart-symbol"); if(!sel) return; sel.value = r.dataset.s; sel.dispatchEvent(new Event("change")); sel.scrollIntoView({behavior: "smooth", block: "center"}); }));
  }
  if($("ratio") || $("home-q")){
    const j = await getQuotes("metals"), g = j.quotes["XAU/USD"], s = j.quotes["XAG/USD"];
    if($("ratio")) $("ratio").textContent = g && s ? (g.price / s.price).toFixed(1) + " : 1" : "Unavailable";
    if($("home-q")) $("home-q").innerHTML = ["XAU/USD","XAG/USD"].map(x => card(x, j)).join("") + await (async () => { const k = await getQuotes("stocks"); return ["SPY","QQQ"].map(x => card(x, k)).join(""); })();
  }
})();

/* ---- chart ---- */
const el = $("trading-chart");
if(el && window.LightweightCharts){
  const chart = LightweightCharts.createChart(el, {width: el.clientWidth, height: 380,
    layout: {background: {color: "#171d25"}, textColor: "#98a1ad"},
    grid: {vertLines: {color: "#222a34"}, horzLines: {color: "#222a34"}},
    rightPriceScale: {borderColor: "#2a323d"}, timeScale: {borderColor: "#2a323d", timeVisible: true}});
  const series = chart.addCandlestickSeries({upColor: "#43b88c", downColor: "#e26a63", borderVisible: false,
    wickUpColor: "#43b88c", wickDownColor: "#e26a63"});
  let sym = $("chart-symbol").value, rng = "3M", smaOn = true, vals = [];
  const sma = chart.addLineSeries({color: "#d9a93f", lineWidth: 2, priceLineVisible: false, lastValueVisible: false});
  function drawSma(){
    if(!smaOn){ sma.setData([]); return; }
    const o = []; for(let i = 19; i < vals.length; i++){ let t = 0; for(let k = i - 19; k <= i; k++) t += vals[k].close; o.push({time: vals[i].time, value: t / 20}); }
    sma.setData(o);
  }
  async function load(){
    $("chart-msg").textContent = "Loading chart";
    try{ const r = await fetch("/api/history/" + sym + "/" + rng); const j = await r.json();
      if(!j.values){ series.setData([]); $("chart-msg").textContent = j.error || "Chart data unavailable. Try again in a minute."; return; }
      if(j.demo) $("demo-banner").hidden = false;
      vals = j.values; const f = vals[0], l = vals[vals.length - 1], pc = (l.close / f.open - 1) * 100;
      $("chart-head").innerHTML = fmt(l.close) + ' <small class="' + cls(pc) + '">' + sgn(pc) + " over this range</small>";
      series.setData(vals); drawSma(); chart.timeScale().fitContent(); $("chart-msg").textContent = "";
    }catch(e){ $("chart-msg").textContent = "Could not load the chart."; }
  }
  $("chart-symbol").addEventListener("change", e => { sym = e.target.value; load(); });
  document.querySelectorAll(".tf button").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll(".tf button").forEach(x => x.classList.remove("on")); b.classList.add("on"); rng = b.dataset.r; load(); }));
  addEventListener("resize", () => chart.applyOptions({width: el.clientWidth}));
  $("sma-btn").addEventListener("click", () => { smaOn = !smaOn; $("sma-btn").classList.toggle("on", smaOn); drawSma(); });
  load();
}

/* ---- lessons ---- */
const done = JSON.parse(localStorage.getItem("nl-done") || "[]");
function progress(){
  const total = 8, pct = Math.round(done.length / total * 100) + "%";
  ["prog","prog-home"].forEach(i => { if($(i)) $(i).style.width = pct; });
}
progress();
document.querySelectorAll(".lesson").forEach(d => {
  const id = d.dataset.id; if(done.includes(id)) d.querySelector(".done").hidden = false;
  d.querySelectorAll(".opt").forEach(b => b.addEventListener("click", () => {
    const ok = Number(b.dataset.i) === Number(b.dataset.ans), fb = d.querySelector(".fb");
    d.querySelectorAll(".opt").forEach(x => x.classList.remove("right", "wrong"));
    b.classList.add(ok ? "right" : "wrong");
    fb.textContent = ok ? "Correct." : "Not quite. Re-read the lesson and try again.";
    if(ok && !done.includes(id)){ done.push(id); localStorage.setItem("nl-done", JSON.stringify(done)); d.querySelector(".done").hidden = false; progress(); }
  }));
});

/* ---- calculators ---- */
const n = id => parseFloat($(id).value) || 0;
function bind(ids, fn){ ids.forEach(i => $(i) && $(i).addEventListener("input", fn)); if($(ids[0])) fn(); }
bind(["ps-acc","ps-risk","ps-entry","ps-stop"], () => {
  const risk = n("ps-acc") * n("ps-risk") / 100, per = Math.abs(n("ps-entry") - n("ps-stop"));
  $("ps-out").textContent = per ? Math.floor(risk / per) + " shares (risking " + fmt(risk) + ")" : "Entry and stop must differ";
});
bind(["cg-start","cg-add","cg-rate","cg-years"], () => {
  const r = n("cg-rate") / 100 / 12, m = n("cg-years") * 12; let v = n("cg-start");
  for(let i = 0; i < m; i++) v = v * (1 + r) + n("cg-add");
  const put = n("cg-start") + n("cg-add") * m;
  $("cg-out").textContent = fmt(v) + " (you put in " + fmt(put) + ")";
});
bind(["gs-g","gs-s"], () => { $("gs-out").textContent = n("gs-s") ? (n("gs-g") / n("gs-s")).toFixed(1) + " : 1" : "Enter silver price"; });
bind(["oz-oz","oz-p"], () => { $("oz-out").textContent = (n("oz-oz") * 31.1035).toFixed(2) + " g, worth " + fmt(n("oz-oz") * n("oz-p")); });

/* ---- glossary ---- */
if($("gsearch")) $("gsearch").addEventListener("input", e => {
  const t = e.target.value.toLowerCase();
  document.querySelectorAll(".gi").forEach(i => i.style.display = i.textContent.toLowerCase().includes(t) ? "" : "none");
});

/* ---- market status (regular US hours, weekdays; holidays not tracked) ---- */
(function(){
  const et = new Date(new Date().toLocaleString("en-US", {timeZone: "America/New_York"}));
  const d = et.getDay(), m = et.getHours() * 60 + et.getMinutes(), open = d > 0 && d < 6 && m >= 570 && m < 960;
  $("mkt").textContent = open ? "NYSE open" : "NYSE closed"; $("mkt").className = "pill " + (open ? "up" : "down");
})();

/* ---- watchlist ---- */
if($("w-body")){
  let wl = JSON.parse(localStorage.getItem("nl-watch") || '["SPY","AAPL","XAU/USD","XAG/USD"]');
  const wsave = () => localStorage.setItem("nl-watch", JSON.stringify(wl));
  async function wdraw(){
    if(!wl.length){ $("w-body").innerHTML = ""; $("w-empty").textContent = "Your watchlist is empty. Add a symbol above."; return; }
    $("w-empty").textContent = "";
    const j = await getQuotes("custom?s=" + encodeURIComponent(wl.join(",")));
    $("w-body").innerHTML = wl.map(s => { const q = j.quotes[s];
      return "<tr><td><b>" + s + "</b></td><td>" + (j.names[s] || "") + '</td><td class="r">' + (q ? fmt(q.price) : "n/a") + '</td><td class="r ' + (q ? cls(q.pct) : "") + '">' + (q ? sgn(q.pct) : "") + '</td><td class="r"><button type="button" data-x="' + s + '">Remove</button></td></tr>'; }).join("");
    $("w-body").querySelectorAll("[data-x]").forEach(b => b.addEventListener("click", () => { wl = wl.filter(x => x !== b.dataset.x); wsave(); wdraw(); }));
  }
  $("w-add").addEventListener("click", () => { const s = $("w-sel").value; if(!wl.includes(s) && wl.length < 12){ wl.push(s); wsave(); wdraw(); } });
  wdraw();
}


/* ---- NORTHLINE PAPER TRADING ---- */
if ($("pt-buy")) {
  let pt;

  try {
    pt = JSON.parse(localStorage.getItem("nl-pt") || "null");
  } catch (e) {
    pt = null;
  }

  if (!pt || typeof pt !== "object") {
    pt = { cash: 100000, pos: {}, history: [] };
  }

  // Preserve existing accounts and add history support.
  pt.cash = Number(pt.cash ?? 100000);
  pt.pos = pt.pos || {};
  pt.history = Array.isArray(pt.history) ? pt.history : [];

  const STARTING_CASH = 100000;
  const prices = {};

  const psave = () =>
    localStorage.setItem("nl-pt", JSON.stringify(pt));

  const money = value =>
    fmt(Number(value) || 0);

  const stat = (label, value, color = "") =>
    '<div class="panel q"><span>' + label +
    '</span><div class="p ' + color + '">' +
    value + '</div></div>';

  function message(text) {
    if ($("pt-msg")) $("pt-msg").textContent = text;
  }

  async function getPrice(symbol) {
    try {
      const result = await getQuotes(
        "custom?s=" + encodeURIComponent(symbol)
      );

      const quote = result?.quotes?.[symbol];

      if (quote && Number(quote.price) > 0) {
        prices[symbol] = Number(quote.price);
        return prices[symbol];
      }
    } catch (error) {
      console.warn("Paper trading price unavailable:", symbol);
    }

    return prices[symbol] || null;
  }

  
function renderHistory() {
  const body = $("pt-history");
  if (!body) return;

  const history = pt.history.slice(0, 50);

  body.innerHTML = history.length
    ? history.map(item => {
        const color = item.side === "BUY" ? "up" : "down";

        return `
          <tr>
            <td><b>${item.symbol}</b></td>
            <td class="${color}">${item.side}</td>
            <td class="r">${item.qty}</td>
            <td class="r">${money(item.price)}</td>
            <td class="r">${money(item.total)}</td>
            <td>${item.date}</td>
          </tr>
        `;
      }).join("")
    : '<tr><td colspan="6" class="note">Your trading activity will appear here.</td></tr>';
}


  async function pdraw() {
    const symbols = Object.keys(pt.pos);
    let marketValue = 0;
    let rows = "";

    // Refresh prices for current positions.
    await Promise.all(symbols.map(getPrice));

    for (const symbol of symbols) {
      const position = pt.pos[symbol];
      const last = prices[symbol] || position.avg;
      const value = last * position.qty;
      const pl = (last - position.avg) * position.qty;

      marketValue += value;

      rows += `
        <tr>
          <td><b>${symbol.replace("/USD", "")}</b></td>
          <td class="r">${position.qty}</td>
          <td class="r">${money(position.avg)}</td>
          <td class="r">${money(last)}</td>
          <td class="r">${money(value)}</td>
          <td class="r ${cls(pl)}">${money(pl)}</td>
        </tr>
      `;
    }

    $("pt-body").innerHTML = rows ||
      '<tr><td colspan="6" class="note">No open positions yet. Place a simulated order to get started.</td></tr>';

    const accountValue = pt.cash + marketValue;
    const totalReturn =
      ((accountValue / STARTING_CASH) - 1) * 100;

    $("pt-sum").innerHTML =
      stat("Account value", money(accountValue)) +
      stat("Available cash", money(pt.cash)) +
      stat("Invested value", money(marketValue)) +
      stat("Total return", sgn(totalReturn), cls(totalReturn));

    const count = $("pt-position-count");
    if (count) count.textContent = symbols.length + " open positions";

    renderHistory();
    updateEstimate();
  }

  async function updateEstimate() {
    const symbol = $("pt-sym").value;
    const qty = Math.floor(Number($("pt-qty").value));

    const estimate = $("pt-estimate");
    const info = $("pt-order-info");

    if (!estimate || !info) return;

    if (!symbol || qty < 1) {
      estimate.textContent = "—";
      info.textContent = "Enter a valid share quantity.";
      return;
    }

    const price = await getPrice(symbol);

    if (!price) {
      estimate.textContent = "Unavailable";
      info.textContent =
        "A market price is currently unavailable. Try again when data returns.";
      return;
    }

    estimate.textContent = money(price * qty);
    info.textContent =
      qty + " shares × " + money(price) + " per share";
  }

  async function trade(side) {
    const symbol = $("pt-sym").value;
    const qty = Math.floor(Number($("pt-qty").value));

    if (!Number.isFinite(qty) || qty < 1) {
      message("Enter a valid quantity of at least 1 share.");
      return;
    }

    message("Checking the available market price...");

    const price = await getPrice(symbol);

    if (!price) {
      message("No market price is available. Please try again later.");
      return;
    }

    const total = price * qty;
    const position = pt.pos[symbol];

    if (side === "buy") {
      if (total > pt.cash) {
        message("Not enough virtual cash for this order.");
        return;
      }

      const current = position || { qty: 0, avg: 0 };

      current.avg =
        ((current.avg * current.qty) + total) /
        (current.qty + qty);

      current.qty += qty;
      pt.pos[symbol] = current;
      pt.cash -= total;

    } else {
      if (!position || position.qty < qty) {
        message("You do not own enough shares to sell.");
        return;
      }

      position.qty -= qty;
      pt.cash += total;

      if (position.qty === 0) {
        delete pt.pos[symbol];
      }
    }

    pt.history.unshift({
      date: new Date().toLocaleString(),
      symbol,
      side: side.toUpperCase(),
      qty,
      price,
      total
    });

    pt.history = pt.history.slice(0, 50);

    psave();

    message(
      side.toUpperCase() + " order completed: " +
      qty + " shares of " + symbol +
      " at " + money(price) + "."
    );

    await pdraw();
  }

  function resetAccount() {
    if (!confirm(
      "Reset your simulated account to $100,000? This clears positions and history."
    )) return;

    pt = {
      cash: STARTING_CASH,
      pos: {},
      history: []
    };

    Object.keys(prices).forEach(key => delete prices[key]);

    psave();
    message("Your simulated account has been reset.");
    pdraw();
  }

  $("pt-buy").addEventListener("click", () => trade("buy"));
  $("pt-sell").addEventListener("click", () => trade("sell"));
  $("pt-reset").addEventListener("click", resetAccount);

  $("pt-sym").addEventListener("change", updateEstimate);
  $("pt-qty").addEventListener("input", updateEstimate);

  psave();
  pdraw();
}

</script>
</body>
</html>
"""

CHART_HTML = """
<div class="chartbar">
 <select id="chart-symbol" aria-label="Choose symbol">
  {% for s,l in symbols.items() %}<option value="{{s}}" {{'selected' if (page=='metals' and s=='XAU/USD') or (page!='metals' and s=='SPY')}}>{{l}} ({{s}})</option>{% endfor %}
 </select>
 <button type="button" id="sma-btn" class="on">20-period average</button>
 <div class="tf">{% for r in ['1D','1W','1M','3M','1Y'] %}<button type="button" data-r="{{r}}" class="{{'on' if r=='3M'}}">{{r}}</button>{% endfor %}</div>
</div>
<div id="chart-head"></div>
<div id="trading-chart" style="width:100%;height:380px"></div>
<p class="note" id="chart-msg"></p>
"""
# Inline the chart block wherever {% include_chart %} appears
HTML = HTML.replace("{% include_chart %}", CHART_HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
