from js import Response, fetch
import json

async def on_fetch(request, env):
    try:
        # 1. Get parameters (using the most robust parsing method)
        url_str = str(request.url)
        symbol = "AAPL"
        if "?" in url_str:
            parts = url_str.split("?symbol=")
            if len(parts) > 1:
                symbol = parts[1].split("&")[0].upper()

        # 2. Get API Key
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            return Response.new("Error: API Key missing in environment", status=500)

        # 3. Fetch data
        api_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        resp = await fetch(api_url)
        
        # 4. [Critical Fix] Get raw text instead of using resp.json()
        # This completely avoids 'pyodide.ffi.JsProxy' related TypeErrors
        raw_text = await resp.text()
        
        # 5. Parse string using Python's native json library
        data = json.loads(raw_text)
        
        # 6. Construct result (use .get to ensure it doesn't crash)
        result = {
            "symbol": symbol,
            "current_price": data.get("c", "N/A"),
            "high": data.get("h", "N/A"),
            "low": data.get("l", "N/A"),
            "prev_close": data.get("pc", "N/A"),
            "status": "success"
        }

        # 7. Return JSON (use list format for headers to ensure compatibility)
        return Response.new(
            json.dumps(result), 
            status=200, 
            headers=[["Content-Type", "application/json"], ["Access-Control-Allow-Origin", "*"]]
        )

    except Exception as e:
        # Last line of defense: in case of error, return error message instead of vague 1101
        return Response.new(f"Final Attempt Error: {str(e)}", status=200)