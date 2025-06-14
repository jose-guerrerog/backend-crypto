from django.urls import path
from django.http import JsonResponse
import json

def portfolios_list(request):
    """Simple portfolios endpoint"""
    if request.method == 'GET':
        # Return mock portfolios data
        portfolios = [
            {
                'id': 'dbb637bd-964d-458c-89fd-0c11f428282f',
                'name': 'My Crypto Portfolio',
                'total_value': 15420.50,
                'created_at': '2024-01-15T10:30:00Z',
                'holdings': [
                    {'symbol': 'BTC', 'amount': 0.35, 'value': 15000},
                    {'symbol': 'ETH', 'amount': 2.1, 'value': 6300},
                    {'symbol': 'ADA', 'amount': 1000, 'value': 420.50}
                ]
            }
        ]
        return JsonResponse({
            'results': portfolios,
            'count': len(portfolios),
            'status': 'success'
        })
    
    elif request.method == 'POST':
        # Handle portfolio creation
        try:
            data = json.loads(request.body)
            # Mock response for created portfolio
            return JsonResponse({
                'id': 'new-portfolio-uuid',
                'name': data.get('name', 'New Portfolio'),
                'total_value': 0,
                'created_at': '2024-06-15T12:00:00Z',
                'status': 'created'
            }, status=201)
        except:
            return JsonResponse({'error': 'Invalid data'}, status=400)

def portfolio_detail(request, portfolio_id):
    """Single portfolio endpoint with UUID support"""
    if request.method == 'GET':
        return JsonResponse({
            'id': portfolio_id,
            'name': 'My Crypto Portfolio',
            'total_value': 15420.50,
            'created_at': '2024-01-15T10:30:00Z',
            'holdings': [
                {
                    'id': 1,
                    'symbol': 'BTC',
                    'name': 'Bitcoin', 
                    'amount': 0.35,
                    'current_price': 45000,
                    'value': 15750,
                    'change_24h': 2.5
                },
                {
                    'id': 2,
                    'symbol': 'ETH',
                    'name': 'Ethereum',
                    'amount': 2.1,
                    'current_price': 3000,
                    'value': 6300,
                    'change_24h': 1.8
                },
                {
                    'id': 3,
                    'symbol': 'ADA',
                    'name': 'Cardano',
                    'amount': 1000,
                    'current_price': 0.42,
                    'value': 420,
                    'change_24h': -0.5
                }
            ],
            'status': 'success'
        })
    
    elif request.method == 'PUT' or request.method == 'PATCH':
        # Handle portfolio updates
        try:
            data = json.loads(request.body)
            return JsonResponse({
                'id': portfolio_id,
                'name': data.get('name', 'Updated Portfolio'),
                'status': 'updated'
            })
        except:
            return JsonResponse({'error': 'Invalid data'}, status=400)
            
    elif request.method == 'DELETE':
        return JsonResponse({'status': 'deleted'}, status=204)

# Holdings endpoints
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
                'id': 'new-holding-id',
                'portfolio': portfolio_id,
                'symbol': data.get('symbol'),
                'amount': data.get('amount'),
                'status': 'created'
            }, status=201)
        except:
            return JsonResponse({'error': 'Invalid data'}, status=400)

urlpatterns = [
    path('portfolios/', portfolios_list, name='portfolios-list'),
    path('portfolios/<str:portfolio_id>/', portfolio_detail, name='portfolio-detail'),
    path('portfolios/<str:portfolio_id>/holdings/', portfolio_holdings, name='portfolio-holdings'),
]