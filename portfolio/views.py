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
            portfolios_data.append({
                'id': portfolio.id,
                'name': portfolio.name,
                'created_at': portfolio.created_at.isoformat(),
                'transaction_count': len(portfolio.transactions)
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
            'transaction_count': 0
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

@api_view(['POST'])
def add_transaction(request, portfolio_id):
    """Add a transaction to a portfolio"""
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
        return Response(
            {'error': f'Search failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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
        return Response(
            {'error': f'Failed to fetch prices: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )