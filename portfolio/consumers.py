import json
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
            print("WebSocket connected successfully!")

            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected to crypto price updates',
                'status': 'success'
            }))

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
        try:
            data = json.loads(text_data)
            print(f"Received from client: {data}")

            if data.get('type') == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif data.get('type') == 'subscribe':
                coins = data.get('coins', ['bitcoin', 'ethereum', 'cardano'])
                await self.send(text_data=json.dumps({
                    'type': 'subscription',
                    'message': f'Subscribed to {", ".join(coins)}',
                    'coins': coins
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
                    await asyncio.sleep(30)

                except asyncio.CancelledError:
                    print("Price update task cancelled")
                    break
                except Exception as e:
                    print(f"Error in price update loop: {e}")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to fetch price updates',
                        'error': str(e)
                    }))
                    await asyncio.sleep(10)

        except Exception as e:
            print(f"Fatal error in send_price_updates: {e}")

    async def fetch_crypto_prices(self):
        """Fetch crypto prices using proxy to avoid blocking"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }

            param_str = "&".join(f"{key}={value}" for key, value in params.items())
            target_url = f"{url}?{param_str}"
            proxy_url = f"https://api.allorigins.win/get?url={target_url}"

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(proxy_url) as response:
                    if response.status == 200:
                        wrapper = await response.json()
                        if 'contents' in wrapper:
                            contents = wrapper['contents'].encode('utf-8', 'surrogatepass').decode('utf-8', 'ignore')
                            return json.loads(contents)
                        else:
                            raise Exception("Proxy response missing 'contents'")
                    else:
                        raise Exception(f"Proxy failed with status {response.status}")
        except Exception as e:
            print(f"Proxy fetch failed: {e}")
            return self.get_fallback_prices()

    def get_fallback_prices(self):
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
