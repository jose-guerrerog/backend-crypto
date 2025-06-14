import json
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("WebSocket connected!")
        
        # Start sending price updates
        self.price_task = asyncio.create_task(self.send_price_updates())
    
    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {close_code}")
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
    
    async def receive(self, text_data):
        # Handle incoming messages from client
        try:
            data = json.loads(text_data)
            print(f"Received: {data}")
            
            # Echo back for testing
            await self.send(text_data=json.dumps({
                'type': 'message',
                'data': f"Server received: {data}"
            }))
        except Exception as e:
            print(f"Error handling message: {e}")
    
    async def send_price_updates(self):
        """Send crypto price updates every 30 seconds"""
        while True:
            try:
                prices = await self.fetch_crypto_prices()
                await self.send(text_data=json.dumps({
                    'type': 'price_update',
                    'data': prices
                }))
                await asyncio.sleep(30)  # Update every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error sending price updates: {e}")
                await asyncio.sleep(10)  # Wait before retrying
    
    async def fetch_crypto_prices(self):
        """Fetch crypto prices from CoinGecko API"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"API error: {response.status}")
                        return {}
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return {
                'bitcoin': {'usd': 45000, 'usd_24h_change': 2.5},
                'ethereum': {'usd': 3000, 'usd_24h_change': 1.8},
                'cardano': {'usd': 0.5, 'usd_24h_change': -0.5},
            }