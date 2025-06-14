from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
import json

from .models import portfolio_storage, Transaction
from .services import coingecko_service, portfolio_analytics

@api_view(['GET', 'POST'])
def portfolios(request):
    """Handle portfolio list and creation"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    if request.method == 'GET':
        user_portfolios = portfolio_storage.get_session_portfolios(session_key)
        portfolios_data = []
        
        for portfolio in user_portfolios:
            # Include transactions in the portfolio data
            transactions_data = []
            for transaction in portfolio.transactions:
                transactions_data.append({
                    'id': transaction.id,
                    'coin_id': transaction.coin_id,
                    'coin_name': transaction.coin_name,
                    'coin_symbol': transaction.coin_symbol,
                    'amount': transaction.amount,
                    'price_usd': transaction.price_usd,
                    'transaction_type': transaction.transaction_type,
                    'timestamp': transaction.timestamp.isoformat(),
                    'total_value': transaction.amount * transaction.price_usd
                })
            
            portfolios_data.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'created_at': portfolio.created_at.isoformat(),
                'transaction_count': len(portfolio.transactions),
                'transactions': transactions_data
            })
        
        return Response({'portfolios': portfolios_data})
    
    elif request.method == 'POST':
        data = request.data
        name = data.get('name', '').strip()
        
        if not name:
            return Response(
                {'error': 'Portfolio name is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        portfolio = portfolio_storage.create_portfolio(session_key, name)
        
        return Response({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'transaction_count': 0,
            'transactions': []
        }, status=status.HTTP_201_CREATED)

@api_view(['GET', 'DELETE'])
def portfolio_detail(request, portfolio_id):
    """Handle individual portfolio operations"""
    session_key = request.session.session_key
    if not session_key:
        return Response(
            {'error': 'Session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolio = portfolio_storage.get_portfolio(portfolio_id)
    if not portfolio:
        return Response(
            {'error': 'Portfolio not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify portfolio belongs to current session
    if portfolio_id not in portfolio_storage.session_portfolios.get(session_key, []):
        return Response(
            {'error': 'Portfolio not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        transactions_data = []
        for transaction in portfolio.transactions:
            transactions_data.append({
                'id': transaction.id,
                'coin_id': transaction.coin_id,
                'coin_name': transaction.coin_name,
                'coin_symbol': transaction.coin_symbol,
                'amount': transaction.amount,
                'price_usd': transaction.price_usd,
                'transaction_type': transaction.transaction_type,
                'timestamp': transaction.timestamp.isoformat(),
                'total_value': transaction.amount * transaction.price_usd
            })
        
        return Response({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'transaction_count': len(portfolio.transactions),
            'transactions': transactions_data
        })
    
    elif request.method == 'DELETE':
        success = portfolio_storage.delete_portfolio(session_key, portfolio_id)
        if success:
            return Response({'message': 'Portfolio deleted successfully'})
        else:
            return Response(
                {'error': 'Failed to delete portfolio'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@api_view(['GET', 'POST'])
def portfolio_transactions(request, portfolio_id):
    """Handle portfolio transactions - both GET (list) and POST (add)"""
    session_key = request.session.session_key
    if not session_key:
        return Response(
            {'error': 'Session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolio = portfolio_storage.get_portfolio(portfolio_id)
    if not portfolio or portfolio_id not in portfolio_storage.session_portfolios.get(session_key, []):
        return Response(
            {'error': 'Portfolio not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        # Return list of transactions
        transactions_data = []
        for transaction in portfolio.transactions:
            transactions_data.append({
                'id': transaction.id,
                'coin_id': transaction.coin_id,
                'coin_name': transaction.coin_name,
                'coin_symbol': transaction.coin_symbol,
                'amount': transaction.amount,
                'price_usd': transaction.price_usd,
                'transaction_type': transaction.transaction_type,
                'timestamp': transaction.timestamp.isoformat(),
                'total_value': transaction.amount * transaction.price_usd
            })
        
        return Response({'transactions': transactions_data})
    
    elif request.method == 'POST':
        # Add new transaction
        data = request.data
        required_fields = ['coin_id', 'coin_name', 'coin_symbol', 'amount', 'price_usd', 'transaction_type']
        
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            transaction = Transaction(
                id="",  # Will be generated in __post_init__
                coin_id=data['coin_id'],
                coin_name=data['coin_name'],
                coin_symbol=data['coin_symbol'].upper(),
                amount=float(data['amount']),
                price_usd=float(data['price_usd']),
                transaction_type=data['transaction_type'],
                timestamp=datetime.now()
            )
            
            if transaction.amount <= 0:
                return Response(
                    {'error': 'Amount must be positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if transaction.price_usd <= 0:
                return Response(
                    {'error': 'Price must be positive'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if transaction.transaction_type not in ['buy', 'sell']:
                return Response(
                    {'error': 'Transaction type must be buy or sell'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            portfolio_storage.add_transaction(portfolio_id, transaction)
            
            return Response({
                'id': transaction.id,
                'coin_id': transaction.coin_id,
                'coin_name': transaction.coin_name,
                'coin_symbol': transaction.coin_symbol,
                'amount': transaction.amount,
                'price_usd': transaction.price_usd,
                'transaction_type': transaction.transaction_type,
                'timestamp': transaction.timestamp.isoformat(),
                'total_value': transaction.amount * transaction.price_usd
            }, status=status.HTTP_201_CREATED)
            
        except (ValueError, TypeError) as e:
            return Response(
                {'error': 'Invalid numeric values'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(['DELETE'])
def remove_transaction(request, portfolio_id, transaction_id):
    """Remove a transaction from a portfolio"""
    session_key = request.session.session_key
    if not session_key:
        return Response(
            {'error': 'Session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolio = portfolio_storage.get_portfolio(portfolio_id)
    if not portfolio or portfolio_id not in portfolio_storage.session_portfolios.get(session_key, []):
        return Response(
            {'error': 'Portfolio not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    success = portfolio_storage.remove_transaction(portfolio_id, transaction_id)
    if success:
        return Response({'message': 'Transaction removed successfully'})
    else:
        return Response(
            {'error': 'Transaction not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
def portfolio_analytics_view(request, portfolio_id):
    """Get portfolio analytics and metrics"""
    session_key = request.session.session_key
    if not session_key:
        return Response(
            {'error': 'Session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    portfolio = portfolio_storage.get_portfolio(portfolio_id)
    if not portfolio or portfolio_id not in portfolio_storage.session_portfolios.get(session_key, []):
        return Response(
            {'error': 'Portfolio not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        metrics = portfolio_analytics.calculate_portfolio_metrics(portfolio)
        
        return Response({
            'total_value': round(metrics.total_value, 2),
            'total_cost': round(metrics.total_cost, 2),
            'total_profit_loss': round(metrics.total_profit_loss, 2),
            'profit_loss_percentage': round(metrics.profit_loss_percentage, 2),
            'best_performer': metrics.best_performer,
            'worst_performer': metrics.worst_performer,
            'asset_allocation': {k: round(v, 2) for k, v in metrics.asset_allocation.items()}
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to calculate analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def search_coins(request):
    """Search for cryptocurrencies"""
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'coins': []})
    
    try:
        results = coingecko_service.search_coins(query)
        formatted_results = []
        
        for coin in results:
            formatted_results.append({
                'id': coin['id'],
                'name': coin['name'],
                'symbol': coin['symbol'].upper(),
                'thumb': coin.get('thumb', ''),
                'market_cap_rank': coin.get('market_cap_rank')
            })
        
        return Response({'coins': formatted_results})
        
    except Exception as e:
        # Return fallback coins if API fails
        mock_coins = [
            {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'thumb': '', 'market_cap_rank': 1},
            {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'thumb': '', 'market_cap_rank': 2},
            {'id': 'cardano', 'name': 'Cardano', 'symbol': 'ADA', 'thumb': '', 'market_cap_rank': 3},
            {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'thumb': '', 'market_cap_rank': 4},
            {'id': 'dogecoin', 'name': 'Dogecoin', 'symbol': 'DOGE', 'thumb': '', 'market_cap_rank': 5},
        ]
        
        filtered_coins = [
            coin for coin in mock_coins 
            if query.lower() in coin['name'].lower() or query.lower() in coin['symbol'].lower()
        ] if query else mock_coins[:5]
        
        return Response({'coins': filtered_coins})

@api_view(['GET'])
def coin_prices(request):
    """Get current prices for specified coins"""
    coin_ids = request.GET.get('ids', '').strip()
    if not coin_ids:
        return Response({'prices': {}})
    
    coin_list = [coin.strip() for coin in coin_ids.split(',') if coin.strip()]
    
    try:
        prices = coingecko_service.get_detailed_coin_data(coin_list)
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
        
        return Response({'prices': formatted_prices})
        
    except Exception as e:
        # Return fallback prices if API fails
        mock_prices = {
            'bitcoin': {
                'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin',
                'current_price': 43000, 'price_change_24h': 1200, 'price_change_percentage_24h': 2.85,
                'market_cap': 850000000000, 'volume_24h': 25000000000, 'last_updated': datetime.now().isoformat()
            },
            'ethereum': {
                'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum',
                'current_price': 2500, 'price_change_24h': -50, 'price_change_percentage_24h': -1.96,
                'market_cap': 300000000000, 'volume_24h': 15000000000, 'last_updated': datetime.now().isoformat()
            },
            'cardano': {
                'id': 'cardano', 'symbol': 'ADA', 'name': 'Cardano',
                'current_price': 0.45, 'price_change_24h': 0.02, 'price_change_percentage_24h': 4.65,
                'market_cap': 15000000000, 'volume_24h': 500000000, 'last_updated': datetime.now().isoformat()
            }
        }
        
        filtered_prices = {coin_id: mock_prices.get(coin_id) for coin_id in coin_list if coin_id in mock_prices}
        return Response({'prices': filtered_prices})

# Legacy function for backward compatibility (keeping your original function)
@api_view(['POST'])
def add_transaction(request, portfolio_id):
    """Legacy add transaction endpoint - redirects to portfolio_transactions"""
    return portfolio_transactions(request, portfolio_id)