from js import Response, fetch
import json
import random

async def on_fetch(request, env):
    try:
        # 1. Parse parameters
        url_str = str(request.url)
        symbols_str = "AAPL"
        if "?symbols=" in url_str:
            symbols_str = url_str.split("?symbols=")[1].split("&")[0]
        elif "?symbol=" in url_str:
            symbols_str = url_str.split("?symbol=")[1].split("&")[0]

        symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

        # 2. Load Balancing: Handle multiple API keys
        # We look for FINNHUB_KEYS (semicolon separated) or fall back to FINNHUB_API_KEY
        keys_str = getattr(env, "FINNHUB_KEYS", None) or getattr(env, "FINNHUB_API_KEY", None)
        if not keys_str:
            return Response.new(json.dumps({"error": "Config Error: No API Keys found"}), status=200)
        
        # Split by semicolon or comma and clean up
        api_keys = [k.strip() for k in keys_str.replace(",", ";").split(";") if k.strip()]
        
        def get_random_key():
            return random.choice(api_keys)

        results = {}

        # 3. Process each symbol
        for symbol in symbols:
            try:
                # Use a random key for each symbol to distribute load
                current_key = get_random_key()
                
                # Fetch Quote
                quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={current_key}"
                q_resp = await fetch(quote_url)
                q_data = json.loads(await q_resp.text())

                # Fetch Basic Financials (P/E, MA200, etc)
                metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={current_key}"
                m_resp = await fetch(metric_url)
                m_data = json.loads(await m_resp.text())
                metrics = m_data.get("metric", {})

                # Metric fallbacks (Key-chaining)
                # P/E Ratio: try multiple variations
                pe = metrics.get("peNormalized") or metrics.get("peTTM") or metrics.get("peBasicExclExtraTTM") or "N/A"
                
                # MA200: try multiple variations
                ma200 = metrics.get("200DayMovingAverage") or metrics.get("ma200") or "N/A"
                
                # MA50: try multiple variations
                ma50 = metrics.get("50DayMovingAverage") or metrics.get("ma50") or "N/A"

                results[symbol] = {
                    "current_price": q_data.get("c", "N/A"),
                    "high": q_data.get("h", "N/A"),
                    "low": q_data.get("l", "N/A"),
                    "open": q_data.get("o", "N/A"),
                    "prev_close": q_data.get("pc", "N/A"),
                    "change": q_data.get("d", "N/A"),
                    "percent": q_data.get("dp", "N/A"),
                    "pe_ratio": pe,
                    "ma200": ma200,
                    "ma50": ma50,
                    "week52_high": metrics.get("52WeekHigh", "N/A"),
                    "week52_low": metrics.get("52WeekLow", "N/A"),
                    "status": "success"
                }
            except Exception as item_err:
                results[symbol] = {"status": "error", "detail": str(item_err)}

        return Response.new(
            json.dumps(results), 
            status=200, 
            headers=[["Content-Type", "application/json"], ["Access-Control-Allow-Origin", "*"]]
        )

    except Exception as e:
        return Response.new(json.dumps({"error": "Worker Internal Error", "detail": str(e)}), status=200)