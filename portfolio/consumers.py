import json
import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from portfolio.coingecko import coingecko_service

logger = logging.getLogger(__name__)

class CryptoPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("✅ WebSocket connected")
        await self.send(json.dumps({
            'type': 'connection',
            'message': 'Connected to crypto price updates',
            'status': 'success'
        }))
        self.coins = ['bitcoin', 'ethereum', 'solana', 'dogecoin', 'cardano']  # expanded default fallback
        self.price_task = asyncio.create_task(self.send_price_updates())

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
                coins = data.get('coins', [])
                if coins:
                    self.coins = coins
                    logger.info(f"🔔 Subscribed coins updated: {self.coins}")
                if hasattr(self, 'price_task'):
                    self.price_task.cancel()
                    logger.info("♻️ Restarting price task with new coin list")
                    self.price_task = asyncio.create_task(self.send_price_updates())

                await self.send(json.dumps({
                    'type': 'subscription',
                    'message': f'Subscribed to: {", ".join(self.coins)}',
                    'coins': self.coins
                }))
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
            await self.send(json.dumps({
                'type': 'error',
                'message': f'Server error: {str(e)}'
            }))

    async def send_price_updates(self):
        while True:
            try:
                prices = await self.fetch_crypto_prices()
                await self.send(json.dumps({
                    'type': 'price_update',
                    'data': prices,
                    'timestamp': asyncio.get_event_loop().time()
                }))
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                logger.info("🛑 Price update loop cancelled")
                break
            except Exception as e:
                logger.error(f"🚨 Error in price loop: {e}")
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'Failed to fetch price updates',
                    'error': str(e)
                }))
                await asyncio.sleep(10)

    async def fetch_crypto_prices(self):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, coingecko_service.get_prices, self.coins)
