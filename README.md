# StockTracker Cloudflare Worker Proxy

This is a Python-based Cloudflare Worker that acts as a secure proxy between your macOS StockTracker app and the Finnhub API.

## Features
- **Secure**: Your Finnhub API Key is stored safely on Cloudflare, not in the app.
- **CORS Enabled**: Allows your app to fetch data directly.
- **Lightweight**: Returns only the essential data your app needs.

## Setup Instructions

1.  **Install Wrangler**:
    If you haven't already, install the Cloudflare CLI:
    ```bash
    npm install -g wrangler
    ```

2.  **Login to Cloudflare**:
    ```bash
    npx wrangler login
    ```

3.  **Set your Finnhub API Key**:
    Replace `your_actual_api_key_here` with your key from Finnhub.io:
    ```bash
    npx wrangler secret put FINNHUB_API_KEY
    ```

4.  **Deploy**:
    ```bash
    npx wrangler deploy
    ```

5.  **Test**:
    Once deployed, you can test it in your browser:
    `https://stock-tracker-proxy.<your-subdomain>.workers.dev/?symbol=AAPL`

## Usage in App
Update `StockService.swift` in your Xcode project to point to your new Worker URL.
