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

        # 安全获取 API Key
        api_key = getattr(env, "FINNHUB_API_KEY", None)
        if not api_key:
            return Response.new(json.dumps({"error": "Variable FINNHUB_API_KEY not found"}), status=500)

        api_url = f"https://finnhub.io/api/v1/quote?symbol={symbol.upper()}&token={api_key}"
        
        # 发起请求
        resp = await fetch(api_url)
        # 强制转换为字典格式以防万一
        data = await resp.json()
        
        # 转换成标准 Python 字典进行读取，防止属性报错
        res_dict = dict(data)
        
        processed = {
            "symbol": symbol.upper(),
            "price": res_dict.get('c', 'N/A'),
            "high": res_dict.get('h', 'N/A'),
            "status": "online"
        }

        return Response.new(json.dumps(processed), headers={"content-type": "application/json"})

    except Exception as e:
        # 如果报错，把具体错误打印出来，这样我们就能看到是哪一行坏了
        return Response.new(json.dumps({"crash_reason": str(e)}), status=500)