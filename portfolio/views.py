from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from .models import Portfolio, Transaction
from .services import coingecko_service, portfolio_analytics

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from .models import Portfolio
from django.http import JsonResponse

@csrf_exempt
@api_view(['GET', 'POST'])
def portfolios(request):
    if request.method == 'GET':
        try:
            portfolios = Portfolio.objects.all().order_by('-created_at')
            result = []
            for p in portfolios:
                transactions = p.transactions.all()
                print(f"🧠 Portfolio: {p.name} ({p.id}) - {transactions.count()} transactions")

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
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = request.data
            name = data.get('name', '').strip() if isinstance(data, dict) else None

            if not name:
                return Response({
                    'error': 'Portfolio name is required',
                    'debug': {'data': str(data)}
                }, status=400)

            portfolio = Portfolio.objects.create(name=name)

            return Response({
                'id': portfolio.id,
                'name': portfolio.name,
                'created_at': portfolio.created_at.isoformat(),
                'transaction_count': 0,
                'transactions': []
            }, status=201)

        except Exception as e:
            # Debug info visible in response
            return Response({
                'error': 'Server error',
                'debug': str(e),
                'data': str(request.data)
            }, status=500)


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
        metrics = portfolio_analytics.calculate_portfolio_metrics(portfolio)

        # Debug: show transaction count and fetched prices
        transactions = portfolio.transactions.all()
        coin_ids = list(set(t.coin_id for t in transactions))
        debug_info = {
            'transaction_count': transactions.count(),
            'coin_ids': coin_ids,
        }

        return JsonResponse({
            'metrics': metrics.__dict__,
            'debug': debug_info
        })

    except Portfolio.DoesNotExist:
        return JsonResponse({'error': 'Portfolio not found'}, status=404)

@api_view(['GET'])
def search_coins(request):
    """Search for cryptocurrencies"""
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        try:
            results = coingecko_service.search_coins(query)
        except Exception as e:
            print(f"CoinGecko search error: {e}")

    return Response({'coins': results})


@api_view(['GET'])
def coin_prices(request):
    """Get current prices for specified coins"""
    coin_ids = request.GET.get('ids', '').strip()
    if not coin_ids:
        return Response({'prices': {}})

    coin_list = [coin.strip() for coin in coin_ids.split(',') if coin.strip()]
    try:
        prices = coingecko_service.get_detailed_coin_data(coin_list)
        formatted = {
            coin_id: {
                'id': c.id,
                'symbol': c.symbol,
                'name': c.name,
                'current_price': c.current_price,
                'price_change_24h': c.price_change_24h,
                'price_change_percentage_24h': round(c.price_change_percentage_24h, 2),
                'market_cap': c.market_cap,
                'volume_24h': c.volume_24h,
                'last_updated': c.last_updated.isoformat()
            } for coin_id, c in prices.items()
        }
        return Response({'prices': formatted})
    except Exception as e:
        print(f"Price fetch error: {e}")
        return Response({'error': str(e)}, status=500)
