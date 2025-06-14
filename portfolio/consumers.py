import json
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
            print("WebSocket connected successfully!")
            
            # Send initial connection success message
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected to crypto price updates',
                'status': 'success'
            }))
            
            # Start sending price updates after a short delay
            await asyncio.sleep(2)
            self.price_task = asyncio.create_task(self.send_price_updates())
            
        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {close_code}")
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
    
    async def receive(self, text_data):
        # Handle incoming messages from client
        try:
            data = json.loads(text_data)
            print(f"Received from client: {data}")
            
            # Handle different message types
            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif data.get('type') == 'subscribe':
                # Handle subscription to specific coins
                coins = data.get('coins', ['bitcoin', 'ethereum', 'cardano'])
                await self.send(text_data=json.dumps({
                    'type': 'subscription',
                    'message': f'Subscribed to {", ".join(coins)}',
                    'coins': coins
                }))
            else:
                # Echo back for testing
                await self.send(text_data=json.dumps({
                    'type': 'echo',
                    'original_message': data,
                    'server_message': 'Message received successfully'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            }))
    
    async def send_price_updates(self):
        """Send crypto price updates every 30 seconds"""
        try:
            while True:
                try:
                    prices = await self.fetch_crypto_prices()
                    await self.send(text_data=json.dumps({
                        'type': 'price_update',
                        'data': prices,
                        'timestamp': asyncio.get_event_loop().time()
                    }))
                    print("Sent price update successfully")
                    await asyncio.sleep(30)  # Update every 30 seconds
                    
                except asyncio.CancelledError:
                    print("Price update task cancelled")
                    break
                except Exception as e:
                    print(f"Error in price update loop: {e}")
                    # Send error message to client
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to fetch price updates',
                        'error': str(e)
                    }))
                    await asyncio.sleep(10)  # Wait before retrying
                    
        except Exception as e:
            print(f"Fatal error in send_price_updates: {e}")
    
    async def fetch_crypto_prices(self):
        """Fetch crypto prices from CoinGecko API with better error handling"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            # Set a timeout for the request
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Successfully fetched prices: {list(data.keys())}")
                        return data
                    else:
                        print(f"CoinGecko API error: {response.status}")
                        raise Exception(f"API returned status {response.status}")
                        
        except aiohttp.ClientError as e:
            print(f"Network error fetching prices: {e}")
            return self.get_fallback_prices()
        except asyncio.TimeoutError:
            print("Timeout fetching prices from CoinGecko")
            return self.get_fallback_prices()
        except Exception as e:
            print(f"Unexpected error fetching prices: {e}")
            return self.get_fallback_prices()
    
    def get_fallback_prices(self):
        """Return mock prices when API fails"""
        return {
            'bitcoin': {
                'usd': 45000 + (hash(str(asyncio.get_event_loop().time())) % 1000),
                'usd_24h_change': 2.5
            },
            'ethereum': {
                'usd': 3000 + (hash(str(asyncio.get_event_loop().time())) % 100),
                'usd_24h_change': 1.8
            },
            'cardano': {
                'usd': 0.42,
                'usd_24h_change': -0.5
            },
            'polkadot': {
                'usd': 15.5,
                'usd_24h_change': -0.8
            },
            'chainlink': {
                'usd': 10.25,
                'usd_24h_change': 3.2
            }
        }