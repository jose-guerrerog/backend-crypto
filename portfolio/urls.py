from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid

@csrf_exempt
def portfolios_list(request):
    """Portfolios endpoint"""
    if request.method == 'GET':
        # Return portfolios in the format your frontend expects
        portfolios = [
            {
                'id': 'dbb637bd-964d-458c-89fd-0c11f428282f',
                'name': 'My Crypto Portfolio',
                'created_at': '2024-01-15T10:30:00Z',
                'transaction_count': 3,
                'transactions': [
                    {
                        'id': 'tx1',
                        'coin_id': 'bitcoin',
                        'coin_name': 'Bitcoin',
                        'coin_symbol': 'BTC',
                        'amount': 0.35,
                        'price_usd': 42000,
                        'transaction_type': 'buy',
                        'timestamp': '2024-01-15T10:30:00Z',
                        'total_value': 14700
                    },
                    {
                        'id': 'tx2',
                        'coin_id': 'ethereum',
                        'coin_name': 'Ethereum',
                        'coin_symbol': 'ETH',
                        'amount': 2.1,
                        'price_usd': 3000,
                        'transaction_type': 'buy',
                        'timestamp': '2024-01-16T10:30:00Z',
                        'total_value': 6300
                    },
                    {
                        'id': 'tx3',
                        'coin_id': 'cardano',
                        'coin_name': 'Cardano',
                        'coin_symbol': 'ADA',
                        'amount': 1000,
                        'price_usd': 0.42,
                        'transaction_type': 'buy',
                        'timestamp': '2024-01-17T10:30:00Z',
                        'total_value': 420
                    }
                ]
            }
        ]
        return JsonResponse({
            'portfolios': portfolios,
            'count': len(portfolios),
            'status': 'success'
        })
    
    elif request.method == 'POST':
        # Handle portfolio creation
        try:
            data = json.loads(request.body)
            new_portfolio = {
                'id': str(uuid.uuid4()),
                'name': data.get('name', 'New Portfolio'),
                'created_at': '2024-06-15T12:00:00Z',
                'transaction_count': 0,
                'transactions': []
            }
            return JsonResponse(new_portfolio, status=201)
        except Exception as e:
            return JsonResponse({'error': 'Invalid data', 'details': str(e)}, status=400)

@csrf_exempt
def portfolio_detail(request, portfolio_id):
    """Single portfolio endpoint"""
    if request.method == 'GET':
        return JsonResponse({
            'id': portfolio_id,
            'name': 'My Crypto Portfolio',
            'created_at': '2024-01-15T10:30:00Z',
            'transaction_count': 3,
            'transactions': [
                {
                    'id': 'tx1',
                    'coin_id': 'bitcoin',
                    'coin_name': 'Bitcoin',
                    'coin_symbol': 'BTC',
                    'amount': 0.35,
                    'price_usd': 42000,
                    'transaction_type': 'buy',
                    'timestamp': '2024-01-15T10:30:00Z',
                    'total_value': 14700
                },
                {
                    'id': 'tx2',
                    'coin_id': 'ethereum',
                    'coin_name': 'Ethereum',
                    'coin_symbol': 'ETH',
                    'amount': 2.1,
                    'price_usd': 3000,
                    'transaction_type': 'buy',
                    'timestamp': '2024-01-16T10:30:00Z',
                    'total_value': 6300
                },
                {
                    'id': 'tx3',
                    'coin_id': 'cardano',
                    'coin_name': 'Cardano',
                    'coin_symbol': 'ADA',
                    'amount': 1000,
                    'price_usd': 0.42,
                    'transaction_type': 'buy',
                    'timestamp': '2024-01-17T10:30:00Z',
                    'total_value': 420
                }
            ]
        })
    
    elif request.method == 'DELETE':
        return JsonResponse({'status': 'deleted'}, status=204)

@csrf_exempt
def portfolio_transactions(request, portfolio_id):
    """Portfolio transactions endpoint"""
    if request.method == 'GET':
        return JsonResponse({
            'transactions': [
                {
                    'id': 'tx1',
                    'coin_id': 'bitcoin',
                    'coin_name': 'Bitcoin',
                    'coin_symbol': 'BTC',
                    'amount': 0.35,
                    'price_usd': 42000,
                    'transaction_type': 'buy',
                    'timestamp': '2024-01-15T10:30:00Z',
                    'total_value': 14700
                }
            ]
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_transaction = {
                'id': str(uuid.uuid4()),
                'coin_id': data.get('coin_id'),
                'coin_name': data.get('coin_name'),
                'coin_symbol': data.get('coin_symbol'),
                'amount': float(data.get('amount', 0)),
                'price_usd': float(data.get('price_usd', 0)),
                'transaction_type': data.get('transaction_type', 'buy'),
                'timestamp': '2024-06-15T12:00:00Z',
                'total_value': float(data.get('amount', 0)) * float(data.get('price_usd', 0))
            }
            return JsonResponse(new_transaction, status=201)
        except Exception as e:
            return JsonResponse({'error': 'Invalid data', 'details': str(e)}, status=400)

@csrf_exempt
def transaction_detail(request, portfolio_id, transaction_id):
    """Single transaction endpoint"""
    if request.method == 'DELETE':
        return JsonResponse({'status': 'deleted'}, status=204)

@csrf_exempt
def portfolio_analytics(request, portfolio_id):
    """Portfolio analytics endpoint"""
    return JsonResponse({
        'total_value': 50000,
        'total_cost': 45000,
        'total_profit_loss': 5000,
        'profit_loss_percentage': 11.11,
        'asset_allocation': {
            'Bitcoin (BTC)': 60.0,
            'Ethereum (ETH)': 25.0,
            'Cardano (ADA)': 15.0,
        },
        'best_performer': {
            'coin_id': 'bitcoin',
            'coin_name': 'Bitcoin',
            'coin_symbol': 'BTC',
            'profit_loss': 3000,
            'profit_loss_percentage': 15.0,
        },
        'worst_performer': {
            'coin_id': 'ethereum',
            'coin_name': 'Ethereum',
            'coin_symbol': 'ETH',
            'profit_loss': -500,
            'profit_loss_percentage': -2.0,
        },
    })

@csrf_exempt
def coin_search(request):
    """Coin search endpoint"""
    query = request.GET.get('q', '').lower()
    mock_coins = [
        {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'thumb': '', 'market_cap_rank': 1},
        {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'thumb': '', 'market_cap_rank': 2},
        {'id': 'cardano', 'name': 'Cardano', 'symbol': 'ADA', 'thumb': '', 'market_cap_rank': 3},
        {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'thumb': '', 'market_cap_rank': 4},
        {'id': 'dogecoin', 'name': 'Dogecoin', 'symbol': 'DOGE', 'thumb': '', 'market_cap_rank': 5},
    ]
    
    filtered_coins = [
        coin for coin in mock_coins 
        if query in coin['name'].lower() or query in coin['symbol'].lower()
    ]
    
    return JsonResponse({'coins': filtered_coins})

@csrf_exempt
def coin_prices(request):
    """Coin prices endpoint"""
    ids = request.GET.get('ids', '').split(',')
    mock_prices = {
        'bitcoin': {
            'id': 'bitcoin',
            'symbol': 'btc',
            'name': 'Bitcoin',
            'current_price': 43000,
            'price_change_24h': 1200,
            'price_change_percentage_24h': 2.85,
            'market_cap': 850000000000,
            'volume_24h': 25000000000,
            'last_updated': '2024-06-15T12:00:00Z'
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
            'last_updated': '2024-06-15T12:00:00Z'
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
            'last_updated': '2024-06-15T12:00:00Z'
        }
    }
    
    prices = {coin_id: mock_prices.get(coin_id) for coin_id in ids if coin_id in mock_prices}
    return JsonResponse({'prices': prices})

# Holdings endpoints (keeping your original for compatibility)
@csrf_exempt
def portfolio_holdings(request, portfolio_id):
    """Portfolio holdings endpoint"""
    if request.method == 'GET':
        return JsonResponse({
            'results': [
                {
                    'id': 1,
                    'portfolio': portfolio_id,
                    'symbol': 'BTC',
                    'amount': 0.35,
                    'purchase_price': 42000,
                    'current_price': 45000
                }
            ]
        })
    elif request.method == 'POST':
        # Add new holding
        try:
            data = json.loads(request.body)
            return JsonResponse({
                'id': str(uuid.uuid4()),
                'portfolio': portfolio_id,
                'symbol': data.get('symbol'),
                'amount': data.get('amount'),
                'status': 'created'
            }, status=201)
        except Exception as e:
            return JsonResponse({'error': 'Invalid data', 'details': str(e)}, status=400)

urlpatterns = [
    # Portfolio endpoints
    path('portfolios/', portfolios_list, name='portfolios-list'),
    path('portfolios/<str:portfolio_id>/', portfolio_detail, name='portfolio-detail'),
    
    # Transaction endpoints (what your frontend expects)
    path('portfolios/<str:portfolio_id>/transactions/', portfolio_transactions, name='portfolio-transactions'),
    path('portfolios/<str:portfolio_id>/transactions/<str:transaction_id>/', transaction_detail, name='transaction-detail'),
    
    # Analytics endpoint
    path('portfolios/<str:portfolio_id>/analytics/', portfolio_analytics, name='portfolio-analytics'),
    
    # Coin endpoints
    path('coins/search/', coin_search, name='coin-search'),
    path('coins/prices/', coin_prices, name='coin-prices'),
    
    # Holdings endpoints (keeping for compatibility)
    path('portfolios/<str:portfolio_id>/holdings/', portfolio_holdings, name='portfolio-holdings'),
]