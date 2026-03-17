from js import Response, fetch
import json

async def on_fetch(request, env):
    try:
        # 1. Parse parameters
        # Support both 'symbol' (single) and 'symbols' (comma-separated list)
        url_str = str(request.url)
        symbols_str = ""
        
        if "?symbols=" in url_str:
            symbols_str = url_str.split("?symbols=")[1].split("&")[0]
        elif "?symbol=" in url_str:
            symbols_str = url_str.split("?symbol=")[1].split("&")[0]
        else:
            # Default to AAPL if nothing is provided
            symbols_str = "AAPL"

        # Split into list and clean up
        symbols = [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

        # 2. Get API Key
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            return Response.new(json.dumps({"error": "Config Error: FINNHUB_API_KEY missing"}), status=200)

        results = {}

        # 3. Process each symbol
        # Note: 200 symbols will likely hit Finnhub's 60 req/min limit.
        # We process them sequentially here for maximum compatibility and to slightly pace requests.
        for symbol in symbols:
            try:
                # Fetch Quote
                quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
                q_resp = await fetch(quote_url)
                q_text = await q_resp.text()
                q_data = json.loads(q_text)

                # Fetch Basic Financials
                metric_url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={api_key}"
                m_resp = await fetch(metric_url)
                m_text = await m_resp.text()
                m_data = json.loads(m_text)
                metrics = m_data.get("metric", {})

                # Build symbol result
                results[symbol] = {
                    "current_price": q_data.get("c", "N/A"),
                    "change": q_data.get("d", "N/A"),
                    "percent": q_data.get("dp", "N/A"),
                    "prev_close": q_data.get("pc", "N/A"),
                    "pe_ratio": metrics.get("peNormalized", "N/A") or metrics.get("peTTM", "N/A"),
                    "ma200": metrics.get("200DayMovingAverage", "N/A"),
                    "ma50": metrics.get("50DayMovingAverage", "N/A"),
                    "week52_high": metrics.get("52WeekHigh", "N/A"),
                    "week52_low": metrics.get("52WeekLow", "N/A"),
                    "status": "success"
                }
            except Exception as item_err:
                results[symbol] = {"status": "error", "detail": str(item_err)}

        # 4. Return combined JSON
        return Response.new(
            json.dumps(results), 
            status=200, 
            headers=[
                ["Content-Type", "application/json"], 
                ["Access-Control-Allow-Origin", "*"]
            ]
        )

    except Exception as e:
        # Final safety net
        return Response.new(json.dumps({"error": "Worker Internal Error", "detail": str(e)}), status=200)