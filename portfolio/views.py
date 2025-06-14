from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from .models import Portfolio, Transaction
from .services import coingecko_service, portfolio_analytics

@api_view(['GET', 'POST'])
def portfolios(request):
    if request.method == 'GET':
        portfolios = Portfolio.objects.all().order_by('-created_at')
        result = []
        for p in portfolios:
            transactions = p.transactions.all()
            result.append({
                'id': p.id,
                'name': p.name,
                'created_at': p.created_at.isoformat(),
                'transaction_count': transactions.count(),
                'transactions': [
                    {
                        'id': t.id,
                        'coin_id': t.coin_id,
                        'coin_name': t.coin_name,
                        'coin_symbol': t.coin_symbol,
                        'amount': t.amount,
                        'price_usd': t.price_usd,
                        'transaction_type': t.transaction_type,
                        'timestamp': t.timestamp.isoformat(),
                        'total_value': t.amount * t.price_usd
                    }
                    for t in transactions
                ]
            })
        return Response({'portfolios': result})

    elif request.method == 'POST':
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Portfolio name is required'}, status=400)
        portfolio = Portfolio.objects.create(name=name)
        return Response({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'transaction_count': 0,
            'transactions': []
        }, status=201)

@api_view(['GET', 'DELETE'])
def portfolio_detail(request, portfolio_id):
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
    except Portfolio.DoesNotExist:
        return Response({'error': 'Portfolio not found'}, status=404)

    if request.method == 'GET':
        transactions = portfolio.transactions.all()
        return Response({
            'id': portfolio.id,
            'name': portfolio.name,
            'created_at': portfolio.created_at.isoformat(),
            'transaction_count': transactions.count(),
            'transactions': [
                {
                    'id': t.id,
                    'coin_id': t.coin_id,
                    'coin_name': t.coin_name,
                    'coin_symbol': t.coin_symbol,
                    'amount': t.amount,
                    'price_usd': t.price_usd,
                    'transaction_type': t.transaction_type,
                    'timestamp': t.timestamp.isoformat(),
                    'total_value': t.amount * t.price_usd
                }
                for t in transactions
            ]
        })

    elif request.method == 'DELETE':
        portfolio.delete()
        return Response({'message': 'Portfolio deleted'})

@api_view(['GET', 'POST'])
def portfolio_transactions(request, portfolio_id):
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
    except Portfolio.DoesNotExist:
        return Response({'error': 'Portfolio not found'}, status=404)

    if request.method == 'GET':
        transactions = portfolio.transactions.all()
        return Response({
            'transactions': [
                {
                    'id': t.id,
                    'coin_id': t.coin_id,
                    'coin_name': t.coin_name,
                    'coin_symbol': t.coin_symbol,
                    'amount': t.amount,
                    'price_usd': t.price_usd,
                    'transaction_type': t.transaction_type,
                    'timestamp': t.timestamp.isoformat(),
                    'total_value': t.amount * t.price_usd
                }
                for t in transactions
            ]
        })

    elif request.method == 'POST':
        data = request.data
        try:
            transaction = Transaction.objects.create(
                portfolio=portfolio,
                coin_id=data['coin_id'],
                coin_name=data['coin_name'],
                coin_symbol=data['coin_symbol'].upper(),
                amount=float(data['amount']),
                price_usd=float(data['price_usd']),
                transaction_type=data['transaction_type']
            )
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
            }, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

@api_view(['DELETE'])
def remove_transaction(request, portfolio_id, transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id, portfolio_id=portfolio_id)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=404)
    transaction.delete()
    return Response({'message': 'Transaction deleted'})

@api_view(['GET'])
def portfolio_analytics_view(request, portfolio_id):
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
    except Portfolio.DoesNotExist:
        return Response({'error': 'Portfolio not found'}, status=404)

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
