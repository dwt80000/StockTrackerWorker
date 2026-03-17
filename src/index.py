from js import Response, fetch
import json
import random

async def on_fetch(request, env):
    try:
        # 1. Authentication Check
        access_key = getattr(env, "WORKER_ACCESS_KEY", None)
        client_key = request.headers.get("X-API-Key")
        
        if access_key and client_key != access_key:
            return Response.new(
                json.dumps({"error": "Unauthorized: Invalid or missing X-API-Key"}), 
                status=401,
                headers=[["Content-Type", "application/json"], ["Access-Control-Allow-Origin", "*"]]
            )

        # 2. Parse parameters
        url_str = str(request.url)
        symbols_str = "AAPL"
        if "?symbols=" in url_str:
            symbols_str = url_str.split("?symbols=")[1].split("&")[0]
        elif "?symbol=" in url_str:
            symbols_str = url_str.split("?symbol=")[1].split("&")[0]

        symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

        # 3. Load Balancing
        keys_str = getattr(env, "FINNHUB_KEYS", None) or getattr(env, "FINNHUB_API_KEY", None)
        if not keys_str:
            return Response.new(json.dumps({"error": "Config Error: No API Keys found"}), status=200)
        
        api_keys = [k.strip() for k in keys_str.replace(",", ";").split(";") if k.strip()]
        
        def get_random_key():
            return random.choice(api_keys)

        results = {}

        # 4. Process each symbol
        for symbol in symbols:
            try:
                current_key = get_random_key()
                
                # Fetch Quote
                quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={current_key}"
                q_resp = await fetch(quote_url)
                q_text = await q_resp.text()
                q_data = json.loads(q_text)

                # Fetch Basic Financials
                metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={current_key}"
                m_resp = await fetch(metric_url)
                m_text = await m_resp.text()
                m_data = json.loads(m_text)
                metrics = m_data.get("metric", {})

                # Metric fallbacks
                pe = metrics.get("peNormalized") or metrics.get("peTTM") or metrics.get("peBasicExclExtraTTM") or "N/A"
                ma200 = metrics.get("200DayMovingAverage") or metrics.get("ma200") or "N/A"
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
                    "status": "success",
                    "debug": {
                        "raw_quote": q_data,
                        "raw_metrics": metrics
                    }
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