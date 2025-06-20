import json
import logging
import asyncio
import aiohttp
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
            logger.info("WebSocket connected successfully!")
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected to crypto price updates',
                'status': 'success'
            }))
            await asyncio.sleep(2)
            self.price_task = asyncio.create_task(self.send_price_updates())
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected: {close_code}")
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
            logger.info("Price update task cancelled")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"Received from client: {data}")

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
            logger.warning("Invalid JSON received")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
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
                    logger.info("Sent price update successfully")
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    logger.info("Price update task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in price update loop: {e}")
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to fetch price updates',
                        'error': str(e)
                    }))
                    await asyncio.sleep(10)
        except Exception as e:
            logger.critical(f"Fatal error in send_price_updates: {e}")

    async def fetch_crypto_prices(self):
        try:
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'bitcoin,ethereum,cardano,polkadot,chainlink',
                'vs_currencies': 'usd',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }

            query = "&".join(f"{k}={v}" for k, v in params.items())
            target_url = f"{url}?{query}"
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
            logger.warning(f"Proxy fetch failed: {e}")
            return self.get_fallback_prices()

    def get_fallback_prices(self):
        logger.warning("📦 Using fallback price data")
        return {
            'bitcoin': {'usd': 45000, 'usd_24h_change': 2.5},
            'ethereum': {'usd': 3000, 'usd_24h_change': 1.8},
            'cardano': {'usd': 0.42, 'usd_24h_change': -0.5},
            'polkadot': {'usd': 15.5, 'usd_24h_change': -0.8},
            'chainlink': {'usd': 10.25, 'usd_24h_change': 3.2}
        }
