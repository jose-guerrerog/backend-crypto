import json
import asyncio
import aiohttp
import time
from channels.generic.websocket import AsyncWebsocketConsumer

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscribed_coins = ['bitcoin', 'ethereum', 'cardano', 'polkadot']
        self.last_request_time = 0
        self.rate_limit_delay = 2.0  # 2 seconds between requests for WebSocket
        
    async def connect(self):
        try:
            await self.accept()
            print("WebSocket connected successfully!")

            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected to crypto price updates',
                'status': 'success'
            }))

            # Start price updates after a short delay
            await asyncio.sleep(2)
            self.price_task = asyncio.create_task(self.send_price_updates())

        except Exception as e:
            print(f"WebSocket connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected: {close_code}")
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
            print("Price update task cancelled")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            print(f"Received from client: {data}")

            if data.get('action') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif data.get('action') == 'subscribe':
                coin_ids = data.get('coin_ids', ['bitcoin', 'ethereum', 'cardano'])
                self.subscribed_coins = coin_ids
                await self.send(text_data=json.dumps({
                    'type': 'subscription',
                    'message': f'Subscribed to {", ".join(coin_ids)}',
                    'coin_ids': coin_ids
                }))
                print(f"Updated subscription to: {coin_ids}")
            elif data.get('action') == 'unsubscribe':
                coin_ids = data.get('coin_ids', [])
                for coin_id in coin_ids:
                    if coin_id in self.subscribed_coins:
                        self.subscribed_coins.remove(coin_id)
                await self.send(text_data=json.dumps({
                    'type': 'unsubscription',
                    'message': f'Unsubscribed from {", ".join(coin_ids)}',
                    'coin_ids': coin_ids
                }))
            else:
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
        """Send periodic price updates to the client"""
        try:
            while True:
                try:
                    # Rate limiting
                    current_time = time.time()
                    time_since_last = current_time - self.last_request_time
                    if time_since_last < self.rate_limit_delay:
                        await asyncio.sleep(self.rate_limit_delay - time_since_last)

                    # Fetch prices for subscribed coins
                    prices = await self.fetch_crypto_prices(self.subscribed_coins)
                    
                    if prices:
                        await self.send(text_data=json.dumps({
                            'type': 'price_update',
                            'prices': prices,  # Match your frontend expectation
                            'timestamp': time.time()
                        }))
                        print("Sent price update successfully")
                    
                    self.last_request_time = time.time()
                    
                    # Wait 30 seconds before next update
                    await asyncio.sleep(30)

                except asyncio.CancelledError:
                    print("Price update task cancelled")
                    break
                except Exception as e:
                    print(f"Error in price update loop: {e}")
                    # Send fallback data on error
                    fallback_prices = self.get_fallback_prices()
                    await self.send(text_data=json.dumps({
                        'type': 'price_update',
                        'prices': fallback_prices,
                        'timestamp': time.time(),
                        'source': 'fallback'
                    }))
                    await asyncio.sleep(10)  # Shorter delay on error

        except Exception as e:
            print(f"Fatal error in send_price_updates: {e}")

    async def fetch_crypto_prices(self, coin_ids=None):
        """Fetch cryptocurrency prices directly from CoinGecko API"""
        if not coin_ids:
            coin_ids = self.subscribed_coins

        try:
            # Direct CoinGecko API call
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': 'usd',
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }

            headers = {
                'User-Agent': 'CryptoPortfolioApp/1.0',
                'Accept': 'application/json'
            }

            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(url, params=params) as response:
                    print(f"🔍 CoinGecko API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Successfully fetched prices for: {list(data.keys())}")
                        
                        # Transform data to match your expected format
                        transformed_prices = {}
                        for coin_id, price_data in data.items():
                            transformed_prices[coin_id] = {
                                'id': coin_id,
                                'symbol': coin_id,  # CoinGecko simple/price doesn't include symbol
                                'name': coin_id.title(),  # Simple name transformation
                                'current_price': price_data.get('usd', 0),
                                'price_change_24h': 0,  # Not available in simple endpoint
                                'price_change_percentage_24h': price_data.get('usd_24h_change', 0),
                                'market_cap': price_data.get('usd_market_cap', 0),
                                'volume_24h': price_data.get('usd_24h_vol', 0),
                                'last_updated': str(int(time.time()))
                            }
                        
                        return transformed_prices
                    
                    elif response.status == 429:
                        print("⚠️ Rate limited by CoinGecko API")
                        await asyncio.sleep(60)  # Wait 1 minute on rate limit
                        return self.get_fallback_prices()
                    
                    else:
                        error_text = await response.text()
                        print(f"❌ CoinGecko API error [{response.status}]: {error_text}")
                        return self.get_fallback_prices()

        except asyncio.TimeoutError:
            print("❌ CoinGecko API request timed out")
            return self.get_fallback_prices()
        except Exception as e:
            print(f"❌ Error fetching crypto prices: {e}")
            return self.get_fallback_prices()

    def get_fallback_prices(self):
        """Return fallback price data when API fails"""
        print("📦 Using fallback price data")
        fallback_data = {
            'bitcoin': {
                'id': 'bitcoin',
                'symbol': 'btc',
                'name': 'Bitcoin',
                'current_price': 43000,
                'price_change_24h': 1200,
                'price_change_percentage_24h': 2.85,
                'market_cap': 850000000000,
                'volume_24h': 25000000000,
                'last_updated': str(int(time.time()))
            },
            'ethereum': {
                'id': 'ethereum',
                'symbol': 'eth',
                'name': 'Ethereum',
                'current_price': 2500,
                'price_change_24h': -50,
                'price_change_percentage_24h': -1.96,
                'market_cap': 300000000000,
                'volume_24h': 15000000000,
                'last_updated': str(int(time.time()))
            },
            'cardano': {
                'id': 'cardano',
                'symbol': 'ada',
                'name': 'Cardano',
                'current_price': 0.45,
                'price_change_24h': 0.02,
                'price_change_percentage_24h': 4.65,
                'market_cap': 15000000000,
                'volume_24h': 500000000,
                'last_updated': str(int(time.time()))
            },
            'polkadot': {
                'id': 'polkadot',
                'symbol': 'dot',
                'name': 'Polkadot',
                'current_price': 7.50,
                'price_change_24h': 0.09,
                'price_change_percentage_24h': 1.25,
                'market_cap': 8000000000,
                'volume_24h': 300000000,
                'last_updated': str(int(time.time()))
            },
            'solana': {
                'id': 'solana',
                'symbol': 'sol',
                'name': 'Solana',
                'current_price': 95,
                'price_change_24h': 3,
                'price_change_percentage_24h': 3.26,
                'market_cap': 40000000000,
                'volume_24h': 2000000000,
                'last_updated': str(int(time.time()))
            }
        }
        
        # Only return data for subscribed coins
        return {coin_id: fallback_data[coin_id] for coin_id in self.subscribed_coins if coin_id in fallback_data}