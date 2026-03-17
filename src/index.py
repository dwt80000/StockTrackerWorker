from js import Response, fetch
import json

async def on_fetch(request, env):
    try:
        # 1. Parse parameters (robust extraction)
        url_str = str(request.url)
        symbol = "AAPL"
        if "?" in url_str:
            parts = url_str.split("?symbol=")
            if len(parts) > 1:
                symbol = parts[1].split("&")[0].upper()

        # 2. Get API Key
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            return Response.new(json.dumps({"error": "Config Error: FINNHUB_API_KEY missing"}), status=200)

        # 3. Define Endpoints
        quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={api_key}"

        # 4. Fetch data from both endpoints in parallel
        # Note: In Cloudflare Python, we use await fetch() sequentially for simplicity, 
        # as asyncio.gather support for JsPromise can be tricky.
        
        # Current Quote
        quote_resp = await fetch(quote_url)
        quote_raw = await quote_resp.text()
        quote_data = json.loads(quote_raw)
        
        # Basic Financials (P/E, MA200, etc)
        metric_resp = await fetch(metric_url)
        metric_raw = await metric_resp.text()
        metric_data = json.loads(metric_raw)
        
        metrics = metric_data.get("metric", {})

        # 5. Extract values with fallbacks
        price = quote_data.get("c", "N/A")
        prev_close = quote_data.get("pc", "N/A")
        
        # After-hours price: some APIs use "dp" or separate fields, 
        # for Finnhub quote, 'c' is the most recent (regular or extended).
        
        result = {
            "symbol": symbol,
            "current_price": price,
            "change": quote_data.get("d", "N/A"),
            "percent": quote_data.get("dp", "N/A"),
            "high": quote_data.get("h", "N/A"),
            "low": quote_data.get("l", "N/A"),
            "open": quote_data.get("o", "N/A"),
            "prev_close": prev_close,
            
            # Fundamentals from metric endpoint
            "pe_ratio": metrics.get("peNormalized", "N/A") or metrics.get("peTTM", "N/A"),
            "ma200": metrics.get("200DayMovingAverage", "N/A"),
            "ma50": metrics.get("50DayMovingAverage", "N/A"),
            "week52_high": metrics.get("52WeekHigh", "N/A"),
            "week52_low": metrics.get("52WeekLow", "N/A"),
            
            "status": "success",
            "source": "Finnhub via Cloudflare"
        }

        # 6. Return comprehensive JSON
        return Response.new(
            json.dumps(result), 
            status=200, 
            headers=[
                ["Content-Type", "application/json"], 
                ["Access-Control-Allow-Origin", "*"]
            ]
        )

    except Exception as e:
        return Response.new(json.dumps({"error": "Worker Internal Error", "detail": str(e)}), status=200)