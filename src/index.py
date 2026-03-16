from js import Response, fetch, JSON
import json

async def on_fetch(request, env):
    # 1. 解析参数
    url = request.url
    
    # 更标准的方法是使用 URL 对象
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    symbol = query_params.get('symbol', [None])[0]
    
    if not symbol:
        return Response.new(json.dumps({"error": "Symbol is required"}), 
                            headers={"content-type": "application/json"}, 
                            status=400)

    # 2. 获取环境变量中的 API Key
    # 注意：在 Cloudflare Python Worker 中，env 对象可以直接访问 secret
    # 你需要在 Dashboard 或 wrangler secret put FINNHUB_API_KEY 中设置它
    api_key = env.FINNHUB_API_KEY
    
    if not api_key:
        return Response.new(json.dumps({"error": "API Key not configured"}), 
                            headers={"content-type": "application/json"}, 
                            status=500)

    target_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={api_key}"

    try:
        # 3. 转发请求
        resp = await fetch(target_url)
        data = await resp.json()

        # 4. 数据二次加工 (让你的 App 获取的数据更轻量)
        # Finnhub 返回值说明:
        # c: Current price
        # d: Change
        # dp: Percent change
        # h: High price of the day
        # l: Low price of the day
        # o: Open price of the day
        # pc: Previous close price
        
        processed_data = {
            "symbol": symbol.upper(),
            "price": data.c,      # Current price
            "change": data.d,     # Change
            "percent": data.dp,   # Percent change
            "high": data.h,       # High of the day
            "low": data.l,        # Low of the day
            "source": "Finnhub via Cloudflare Python Worker"
        }

        return Response.new(json.dumps(processed_data), 
                            headers={
                                "content-type": "application/json",
                                "Access-Control-Allow-Origin": "*" # 允许跨域
                            })
    except Exception as e:
        return Response.new(json.dumps({"error": str(e)}), status=500)
