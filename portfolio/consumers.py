import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .services import coingecko_service

class PriceConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time cryptocurrency price updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price_update_task = None
        self.subscribed_coins = set()
        self.update_interval = 30  # seconds
    
    async def connect(self):
        await self.accept()
        print("WebSocket connection established")
    
    async def disconnect(self, close_code):
        # Cancel the price update task
        if self.price_update_task:
            self.price_update_task.cancel()
        print(f"WebSocket connection closed with code: {close_code}")
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe':
                coin_ids = data.get('coin_ids', [])
                await self.subscribe_to_coins(coin_ids)
            
            elif action == 'unsubscribe':
                coin_ids = data.get('coin_ids', [])
                await self.unsubscribe_from_coins(coin_ids)
            
            elif action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
        
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def subscribe_to_coins(self, coin_ids):
        """Subscribe to price updates for specific coins"""
        new_coins = set(coin_ids) - self.subscribed_coins
        self.subscribed_coins.update(new_coins)
        
        if new_coins and not self.price_update_task:
            # Start the price update task if it's not running
            self.price_update_task = asyncio.create_task(self.send_price_updates())
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'subscribed_coins': list(self.subscribed_coins),
            'newly_subscribed': list(new_coins)
        }))
    
    async def unsubscribe_from_coins(self, coin_ids):
        """Unsubscribe from price updates for specific coins"""
        removed_coins = set(coin_ids) & self.subscribed_coins
        self.subscribed_coins -= removed_coins
        
        if not self.subscribed_coins and self.price_update_task:
            # Stop the price update task if no coins are subscribed
            self.price_update_task.cancel()
            self.price_update_task = None
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'subscribed_coins': list(self.subscribed_coins),
            'unsubscribed': list(removed_coins)
        }))
    
    async def send_price_updates(self):
        """Send periodic price updates for subscribed coins"""
        while self.subscribed_coins:
            try:
                # Fetch current prices (this is a sync operation, so we'll run it in executor)
                coin_list = list(self.subscribed_coins)
                loop = asyncio.get_event_loop()
                
                # Run the synchronous API call in a thread pool
                prices = await loop.run_in_executor(
                    None, 
                    coingecko_service.get_detailed_coin_data, 
                    coin_list
                )
                
                if prices:
                    formatted_prices = {}
                    for coin_id, coin_data in prices.items():
                        formatted_prices[coin_id] = {
                            'id': coin_data.id,
                            'symbol': coin_data.symbol,
                            'name': coin_data.name,
                            'current_price': coin_data.current_price,
                            'price_change_24h': coin_data.price_change_24h,
                            'price_change_percentage_24h': round(coin_data.price_change_percentage_24h, 2),
                            'market_cap': coin_data.market_cap,
                            'volume_24h': coin_data.volume_24h,
                            'last_updated': coin_data.last_updated.isoformat()
                        }
                    
                    await self.send(text_data=json.dumps({
                        'type': 'price_update',
                        'prices': formatted_prices,
                        'timestamp': coin_data.last_updated.isoformat() if prices else None
                    }))
                
                # Wait for the next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Price update failed: {str(e)}'
                }))
                await asyncio.sleep(self.update_interval)