from js import Response, fetch
import json
from urllib.parse import urlparse, parse_qs

async def on_fetch(request, env):
    try:
        # 1. Parse parameters
        url_obj = urlparse(request.url)
        params = parse_qs(url_obj.query)
        symbol = params.get('symbol', ['AAPL'])[0] # Default to AAPL to prevent crash on missing parameter

        # 2. Get API Key safely
        # Try attribute access first, then dictionary access, else None
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            try:
                api_key = env["FINNHUB_API_KEY"]
            except:
                pass
        
        if not api_key:
            return Response.new(json.dumps({"error": "Config Error: FINNHUB_API_KEY not found in env"}), status=200)

        # 3. Network request
        api_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={api_key}"
        resp = await fetch(api_url)
        
        # 4. Parse data (Key pitfall to avoid)
        js_data = await resp.json()
        # Never use dict() conversion directly on js_data (JsProxy)
        
        # 5. Read data directly from JS proxy object without iteration
        # In Pyodide, JS objects often expose properties as attributes
        price = getattr(js_data, "c", "N/A")
        
        return Response.new(
            json.dumps({"symbol": symbol.upper(), "price": price, "status": "ok"}),
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        # Return the specific error message to avoid vague Cloudflare 1101 errors
        return Response.new(json.dumps({"error": "Worker Internal Error", "detail": str(e)}), status=200)