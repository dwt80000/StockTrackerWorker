from js import Response, fetch
import json
from urllib.parse import urlparse, parse_qs

async def on_fetch(request, env):
    try:
        # 1. Parse parameters
        url = request.url
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        symbol = query_params.get('symbol', [None])[0]

        if not symbol:
            return Response.new(json.dumps({"error": "Symbol is required"}), 
                               headers={"content-type": "application/json"}, status=400)

        # 2. Get API Key (ensure variable name matches dashboard)
        # Use getattr in case the env object is wrapped differently
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        
        if not api_key:
            return Response.new(json.dumps({"error": "API Key not configured in env"}), 
                               headers={"content-type": "application/json"}, status=500)

        target_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={api_key}"
        
        # 3. Forward request
        resp = await fetch(target_url)
        data = await resp.json()

        # 4. Process data
        processed_data = {
            "symbol": symbol.upper(),
            "price": data.c,
            "change": data.d,
            "percent": data.dp,
            "source": "Cloudflare Python Worker"
        }

        return Response.new(json.dumps(processed_data), 
                           headers={
                               "content-type": "application/json",
                               "Access-Control-Allow-Origin": "*"
                           })
    except Exception as e:
        # This allows viewing detailed error messages instead of a vague 1101
        return Response.new(json.dumps({"error": str(e)}), status=500)
