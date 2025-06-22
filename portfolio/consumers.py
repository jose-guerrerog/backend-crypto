import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from portfolio.services import coingecko_service

logger = logging.getLogger(__name__)

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            await self.accept()
            logger.info("🟢 WebSocket connected")
            await self.send(json.dumps({
                'type': 'connection',
                'message': 'Connected to crypto price updates',
                'status': 'success'
            }))
            self.price_task = asyncio.create_task(self.send_price_updates())
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        logger.info(f"🔌 WebSocket disconnected: {close_code}")
        if hasattr(self, 'price_task'):
            self.price_task.cancel()
            logger.info("⛔ Price update task cancelled")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            logger.info(f"📩 Received from client: {data}")

            if data.get('type') == 'ping':
                await self.send(json.dumps({'type': 'pong', 'timestamp': data.get('timestamp')}))

            elif data.get('type') == 'subscribe':
                coins = data.get('coins', ['bitcoin', 'ethereum', 'cardano'])
                self.coins = coins
                await self.send(json.dumps({
                    'type': 'subscription',
                    'message': f'Subscribed to: {", ".join(coins)}',
                    'coins': coins
                }))
        except Exception as e:
            logger.error(f"⚠️ WebSocket error: {e}")
            await self.send(json.dumps({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            }))

    async def send_price_updates(self):
        try:
            while True:
                try:
                    prices = await self.fetch_crypto_prices()
                    await self.send(json.dumps({
                        'type': 'price_update',
                        'data': prices,
                        'timestamp': asyncio.get_event_loop().time()
                    }))
                    logger.info("📤 Sent price update")
                    await asyncio.sleep(30)
                except asyncio.CancelledError:
                    logger.info("🛑 Price update loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"💥 Error in price loop: {e}")
                    await self.send(json.dumps({
                        'type': 'error',
                        'message': 'Failed to fetch price updates',
                        'error': str(e)
                    }))
                    await asyncio.sleep(10)
        except Exception as e:
            logger.critical(f"🔥 Fatal error in update loop: {e}")

    async def fetch_crypto_prices(self):
        coins = getattr(self, 'coins', ['bitcoin', 'ethereum', 'cardano'])
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, coingecko_service.get_current_prices, coins)