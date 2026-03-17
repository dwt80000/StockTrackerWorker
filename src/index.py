from js import Response, fetch
import json
from urllib.parse import urlparse, parse_qs

async def on_fetch(request, env):
    try:
        url_obj = urlparse(request.url)
        params = parse_qs(url_obj.query)
        symbol = params.get('symbol', [None])[0]

        if not symbol:
            return Response.new(json.dumps({"error": "Symbol missing. Use ?symbol=AAPL"}), 
                               headers={"content-type": "application/json"}, status=400)

        # 2. Get API Key safely
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            return Response.new(json.dumps({"error": "Variable FINNHUB_API_KEY not found"}), status=500)

        api_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={api_key}"
        
        # 3. Fetch data
        resp = await fetch(api_url)
        data = await resp.json()
        
        # 4. Convert JsProxy to Python dict using .to_py()
        # This fixes the "'pyodide.ffi.JsProxy' object is not iterable" crash
        res_dict = data.to_py()
        
        processed = {
            "symbol": symbol.upper(),
            "price": res_dict.get('c', 'N/A'),
            "high": res_dict.get('h', 'N/A'),
            "status": "online"
        }

        return Response.new(json.dumps(processed), headers={"content-type": "application/json"})

    except Exception as e:
        # Return the specific error message for easier debugging
        return Response.new(json.dumps({"crash_reason": str(e)}), status=500)