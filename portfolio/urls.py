
from django.urls import path
from . import views

urlpatterns = [
    # Portfolio endpoints - updated to handle UUID patterns
    path('portfolios/', views.portfolios, name='portfolios'),
    path('portfolios/<uuid:portfolio_id>/', views.portfolio_detail, name='portfolio-detail'),
    
    # Transaction endpoints - updated to handle UUID patterns
    path('portfolios/<uuid:portfolio_id>/transactions/', views.portfolio_transactions, name='portfolio-transactions'),
    path('portfolios/<uuid:portfolio_id>/transactions/<str:transaction_id>/', views.remove_transaction, name='remove-transaction'),
    
    # Analytics endpoint - updated to handle UUID patterns
    path('portfolios/<uuid:portfolio_id>/analytics/', views.portfolio_analytics_view, name='portfolio-analytics'),
    
    # Coin endpoints
    path('coins/search/', views.search_coins, name='search-coins'),
    path('coins/prices/', views.coin_prices, name='coin-prices'),
]